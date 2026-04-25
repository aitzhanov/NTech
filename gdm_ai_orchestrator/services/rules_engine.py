# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def _make_reason(code, message, level='info', field=None):
    return {
        'code': code,
        'message': message,
        'level': level,
        'field': field,
    }


def _evaluate_rule(rule, context):
    """
    Evaluate a single gdm.ai.rule record against the given context.
    Returns True if rule PASSES (no problem), False if rule FAILS.
    """
    check_type = rule.check_type
    contract = context.get('contract', {})
    flags = context.get('flags', {})

    if check_type == 'field_required':
        field = rule.field_name
        if not field:
            return True
        # Check via readiness flags first (pre-computed)
        readiness = flags.get('readiness', {})
        flag_map = {
            'supplier_id': 'has_supplier',
            'date_start': 'has_dates',
            'date_end': 'has_dates',
            'amount_total': 'has_amount',
            'volume_total': 'has_volume',
        }
        if field in flag_map:
            return bool(readiness.get(flag_map[field]))
        # Fallback: check directly in context
        return bool(contract.get(field))

    if check_type == 'date_range':
        consistency = flags.get('consistency', {})
        return bool(consistency.get('date_valid', True))

    if check_type == 'amount_consistency':
        # Re-evaluate with custom threshold from rule
        amount_total = contract.get('amount_total') or 0
        invoice_total = context.get('invoice', {}).get('total_amount') or 0
        if not amount_total:
            return True
        return invoice_total <= amount_total * (rule.threshold or 1.2)

    # custom: always pass at engine level (handled externally)
    return True


def evaluate_rules(context, env=None):
    """
    Evaluate all active rules for gdm.contract.

    If env is provided — loads rules from gdm.ai.rule model (DB-driven).
    Otherwise falls back to hardcoded defaults.

    Returns dict:
        decision, risk_level, confidence, reasons,
        required_action, requires_onchain_action, reasoning_summary
    """
    reasons = []
    risk = 'low'
    decision = 'ready'
    required_action = 'none'
    requires_onchain_action = False
    reasoning_summary = 'Contract is valid and ready for the next step.'
    trigger_onchain = False

    if env is not None:
        # --- DB-driven rules ---
        rules = env['gdm.ai.rule'].sudo().search([
            ('active', '=', True),
            ('entity_model', '=', 'gdm.contract'),
        ], order='sequence asc')

        if not rules:
            _logger.warning('[rules_engine] No active rules found in DB — falling back to defaults')
            return _evaluate_defaults(context)

        for rule in rules:
            passed = _evaluate_rule(rule, context)
            if rule.trigger_onchain_on_pass and passed:
                trigger_onchain = True

            if not passed:
                reasons.append(_make_reason(
                    rule.code,
                    rule.message,
                    level=rule.risk_level,
                    field=rule.field_name or None,
                ))
                # Escalate risk
                rule_risk = rule.risk_level
                if rule_risk == 'high':
                    risk = 'high'
                elif rule_risk == 'medium' and risk != 'high':
                    risk = 'medium'

                # Escalate decision
                fail_decision = rule.decision_on_fail
                if fail_decision == 'invalid':
                    decision = 'invalid'
                elif fail_decision == 'not_ready' and decision not in ('invalid',):
                    decision = 'not_ready'
                elif fail_decision == 'review' and decision == 'ready':
                    decision = 'review'

                # Escalate required_action (first non-none wins)
                if required_action == 'none' and rule.required_action_on_fail != 'none':
                    required_action = rule.required_action_on_fail

        requires_onchain_action = trigger_onchain and decision == 'ready' and not reasons
        if requires_onchain_action:
            required_action = 'prepare_onchain'

    else:
        # --- Hardcoded fallback ---
        return _evaluate_defaults(context)

    confidence = 0.9 if not reasons else 0.6
    if reasons:
        reasoning_summary = '; '.join(
            r.get('message') for r in reasons if r.get('message')
        )

    return {
        'decision': decision,
        'risk_level': risk,
        'confidence': confidence,
        'reasons': reasons,
        'required_action': required_action,
        'requires_onchain_action': requires_onchain_action,
        'reasoning_summary': reasoning_summary,
    }


def _evaluate_defaults(context):
    """
    Hardcoded fallback rules — used when no DB rules exist.
    Mirrors the original rules_engine behaviour.
    """
    flags = context.get('flags', {})
    readiness = flags.get('readiness', {})
    consistency = flags.get('consistency', {})

    reasons = []
    risk = 'low'
    decision = 'ready'
    required_action = 'none'
    requires_onchain_action = False
    reasoning_summary = 'Contract is valid and ready for the next step.'

    if not readiness.get('has_supplier'):
        reasons.append(_make_reason('missing_supplier', 'Missing supplier', level='high', field='supplier_id'))
        risk = 'high'
        decision = 'not_ready'
        required_action = 'complete_master_data'

    if not readiness.get('has_dates'):
        reasons.append(_make_reason('missing_contract_dates', 'Missing contract dates', level='high', field='date_start,date_end'))
        risk = 'high'
        decision = 'not_ready'
        required_action = required_action or 'fix_dates'

    if not readiness.get('has_amount') and not readiness.get('has_volume'):
        reasons.append(_make_reason('missing_financials', 'Missing financials (amount/volume)', level='medium', field='amount_total,volume_total'))
        if risk != 'high':
            risk = 'medium'
        decision = 'not_ready'
        if required_action == 'none':
            required_action = 'review_financials'

    if not consistency.get('date_valid'):
        reasons.append(_make_reason('invalid_date_range', 'Invalid date range', level='high', field='date_start,date_end'))
        risk = 'high'
        decision = 'invalid'
        required_action = 'fix_dates'

    if not consistency.get('amount_vs_invoice'):
        reasons.append(_make_reason('invoice_amount_exceeds_contract', 'Invoice amount exceeds contract', level='medium', field='amount_total'))
        if risk != 'high':
            risk = 'medium'
        if decision == 'ready':
            decision = 'review'
        if required_action == 'none':
            required_action = 'review_financials'

    confidence = 0.9 if not reasons else 0.6
    if reasons:
        reasoning_summary = '; '.join(r.get('message') for r in reasons if r.get('message'))

    if decision == 'ready' and not reasons:
        requires_onchain_action = True
        required_action = 'prepare_onchain'

    return {
        'decision': decision,
        'risk_level': risk,
        'confidence': confidence,
        'reasons': reasons,
        'required_action': required_action,
        'requires_onchain_action': requires_onchain_action,
        'reasoning_summary': reasoning_summary,
    }
