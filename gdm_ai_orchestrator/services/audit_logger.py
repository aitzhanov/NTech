# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def log_decision(env, decision, phase, message=None, extra=None):
    """
    Write a structured audit entry to the system log and optionally to chatter.

    Args:
        env         - Odoo environment
        decision    - gdm.ai.decision record
        phase       - str: 'context_built' | 'rules_evaluated' | 'decision_composed' |
                           'action_routed' | 'blockchain_submitted' | 'blockchain_confirmed' |
                           'blockchain_failed' | 'manual_override' | 'error'
        message     - optional human-readable message
        extra       - optional dict with additional data for the log entry
    """
    entry = {
        'phase': phase,
        'decision_id': decision.id,
        'entity_model': decision.entity_model,
        'entity_res_id': decision.entity_res_id,
        'trigger_event': decision.trigger_event,
        'decision': decision.decision,
        'risk_level': decision.risk_level,
        'confidence': decision.confidence,
        'final_status': decision.final_status,
        'required_action': decision.required_action,
        'requires_onchain_action': decision.requires_onchain_action,
        'blockchain_sync_status': decision.blockchain_sync_status,
        'blockchain_tx_hash': decision.blockchain_tx_hash,
    }
    if extra:
        entry.update(extra)
    if message:
        entry['message'] = message

    _logger.info('[gdm_ai_orchestrator] %s | %s', phase, entry)


def post_chatter(env, decision, body):
    """
    Post a chatter message on the source entity (gdm.contract / gdm.snt / gdm.invoice)
    if the model supports mail.thread.
    """
    try:
        record = env[decision.entity_model].browse(decision.entity_res_id)
        if not record.exists():
            return
        if not hasattr(record, 'message_post'):
            return
        record.message_post(
            body=body,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
    except Exception:
        _logger.exception(
            '[gdm_ai_orchestrator] chatter post failed for decision=%s model=%s res_id=%s',
            decision.id, decision.entity_model, decision.entity_res_id,
        )


def audit_decision_created(env, decision):
    log_decision(env, decision, 'decision_composed',
                 message='AI decision created: %s / %s' % (decision.decision, decision.final_status))


def audit_action_routed(env, decision, route):
    log_decision(env, decision, 'action_routed',
                 message='Action routed: %s' % route,
                 extra={'route': route})


def audit_blockchain_submitted(env, decision, request_id, tx_hash=None):
    log_decision(env, decision, 'blockchain_submitted',
                 message='Blockchain tx submitted: request_id=%s tx_hash=%s' % (request_id, tx_hash),
                 extra={'request_id': request_id, 'tx_hash': tx_hash})
    post_chatter(
        env, decision,
        '🔗 <b>Blockchain:</b> транзакция отправлена.<br/>'
        'request_id: <code>%s</code><br/>'
        'tx_hash: <code>%s</code>' % (request_id or '—', tx_hash or '—'),
    )


def audit_blockchain_failed(env, decision, error_code=None, error_message=None):
    log_decision(env, decision, 'blockchain_failed',
                 message='Blockchain tx failed: %s %s' % (error_code, error_message),
                 extra={'error_code': error_code, 'error_message': error_message})
    post_chatter(
        env, decision,
        '❌ <b>Blockchain:</b> ошибка отправки транзакции.<br/>'
        'Код: <code>%s</code><br/>'
        'Сообщение: %s' % (error_code or '—', error_message or '—'),
    )


def audit_blockchain_confirmed(env, decision):
    log_decision(env, decision, 'blockchain_confirmed',
                 message='Blockchain tx confirmed: tx_hash=%s' % decision.blockchain_tx_hash)
    post_chatter(
        env, decision,
        '✅ <b>Blockchain:</b> транзакция подтверждена.<br/>'
        'tx_hash: <code>%s</code>' % (decision.blockchain_tx_hash or '—'),
    )


def audit_manual_override(env, decision, action, reason=None):
    log_decision(env, decision, 'manual_override',
                 message='Manual override: action=%s reason=%s' % (action, reason),
                 extra={'override_action': action, 'override_reason': reason})
    post_chatter(
        env, decision,
        '👤 <b>Manual override:</b> %s.<br/>'
        'Причина: %s' % (action, reason or '—'),
    )


def audit_error(env, decision, error):
    log_decision(env, decision, 'error',
                 message='Orchestrator error: %s' % error,
                 extra={'error': str(error)})
