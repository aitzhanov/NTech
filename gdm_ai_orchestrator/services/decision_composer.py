# -*- coding: utf-8 -*-
"""
decision_composer.py
====================
Формирует итоговые vals для gdm.ai.decision на основе:
  - merged_result (rules + AI после merge_results)
  - контекста сущности
  - события

Этот компонент НЕ принимает решений — он только формализует
уже принятое системой решение в структуру для сохранения в БД.
"""


def compose_decision_vals(contract, event, result, context):
    """
    :param contract: Odoo record (gdm.contract / contract.contract)
    :param event: str — trigger event name
    :param result: dict — merged result из merge_results()
                   (содержит как rules, так и AI данные)
    :param context: dict — context snapshot из context_builder
    :return: dict — vals для gdm.ai.decision.create()
    """
    decision_val = result.get('decision', 'review')
    final_status = _resolve_final_status(decision_val)

    vals = {
        'entity_model': 'contract.contract',
        'entity_res_id': contract.id,
        'trigger_event': event,
        'decision_type': result.get('decision_type', 'contract_readiness'),
        'decision': decision_val,
        'risk_level': result.get('risk_level', 'low'),
        'confidence': result.get('confidence', 0.5),
        'reasoning_summary': result.get('reasoning_summary') or '',
        'reasons_json': result.get('reasons') or [],
        'required_action': result.get('required_action', 'none'),
        'requires_onchain_action': result.get('requires_onchain_action', False),
        'requires_manual_review': result.get('requires_manual_review', False),
        'context_snapshot_json': context,
        'final_status': final_status,
        # AI-мета поля (заполняются если AI был задействован)
        'ai_used': result.get('ai_used', False),
        'ai_fallback': result.get('ai_fallback', False),
        'ai_model_used': result.get('ai_model_used') or '',
        'ai_tokens_used': result.get('ai_tokens_used', 0),
    }
    return vals


def _resolve_final_status(decision: str) -> str:
    """Маппинг decision → final_status для gdm.ai.decision."""
    mapping = {
        'ready': 'approved',
        'ok': 'approved',
        'not_ready': 'rejected',
        'invalid': 'rejected',
        'review': 'evaluated',
    }
    return mapping.get(decision, 'evaluated')
