# -*- coding: utf-8 -*-
"""
claude_agent_adapter.py
=======================
AI Adapter — связующее звено между gdm_ai_orchestrator и arch_claude_client.

Место в pipeline:
    rules_engine.evaluate_rules()
        ↓
    claude_agent_adapter.analyze_with_claude()   ← этот файл
        ↓
    decision_composer.compose_decision_vals()

Принцип работы:
  - Вызывается ТОЛЬКО если rules engine не закрыл кейс окончательно
    (т.е. decision не 'invalid' и не 'not_ready' с высоким риском).
  - Возвращает обогащённый result, который decision_composer
    объединяет с rules-результатом.
  - Если Claude недоступен — возвращает fallback и orchestrator
    продолжает работу только на основе rules.
"""
import logging

_logger = logging.getLogger(__name__)

# Сценарии по типу сущности
_SCENARIO_MAP = {
    'gdm.contract': 'contract_readiness',
    'contract.contract': 'contract_readiness',
    'gdm.snt': 'document_health',
    'gdm.invoice': 'document_health',
}

# Решения, при которых AI-вызов нецелесообразен (правила уже дали ответ)
_SKIP_DECISIONS = {'invalid'}


def analyze_with_claude(env, context: dict, rules_result: dict, entity_model: str = None) -> dict:
    """
    Вызывает gdm.claude.agent.analyze() и возвращает AI-результат.

    :param env: Odoo Environment
    :param context: нормализованный контекст сущности (из context_builder)
    :param rules_result: результат rules_engine.evaluate_rules()
    :param entity_model: модель сущности для выбора сценария
    :return: dict с ключами AI-решения или пустой dict при пропуске
    """
    # Не вызываем AI если правила дали финальный негативный ответ
    if rules_result.get('decision') in _SKIP_DECISIONS:
        _logger.debug('[claude_adapter] skipped — rules decision=%s', rules_result.get('decision'))
        return {}

    scenario = _SCENARIO_MAP.get(entity_model or '', 'risk_assessment')

    # Строим контекст для AI: добавляем результат rules для enrichment
    ai_context = dict(context)
    ai_context['_rules_summary'] = {
        'decision': rules_result.get('decision'),
        'risk_level': rules_result.get('risk_level'),
        'reasons_count': len(rules_result.get('reasons', [])),
        'required_action': rules_result.get('required_action'),
    }

    try:
        agent = env['gdm.claude.agent']
        result = agent.analyze(ai_context, scenario)
        _logger.info(
            '[claude_adapter] AI result: decision=%s risk=%s confidence=%.2f fallback=%s',
            result.get('decision'), result.get('risk_level'),
            result.get('confidence', 0), result.get('fallback', False),
        )
        return result
    except Exception as exc:
        _logger.error('[claude_adapter] analyze_with_claude failed: %s', exc)
        return {}


def merge_results(rules_result: dict, ai_result: dict) -> dict:
    """
    Объединяет результат rules engine и AI-анализа в единый merged result.

    Логика приоритетов:
      - Если AI недоступен (пустой ai_result) — возвращаем rules_result as-is.
      - Risk level: берём наибольший из двух.
      - Decision: если AI предлагает более строгое решение — применяем его.
      - Confidence: берём AI confidence если AI доступен.
      - Reasons: объединяем (rules + AI reasons).
      - requires_onchain_action: True если хотя бы один источник требует.
      - requires_manual_review: True если AI требует ревью.
      - reasoning_summary: AI summary имеет приоритет.
    """
    if not ai_result or ai_result.get('fallback'):
        merged = dict(rules_result)
        merged['ai_used'] = False
        merged['ai_fallback'] = bool(ai_result.get('fallback'))
        return merged

    _RISK_ORDER = {'low': 0, 'medium': 1, 'high': 2}
    _DECISION_ORDER = {'ready': 0, 'ok': 0, 'review': 1, 'not_ready': 2, 'invalid': 3}

    rules_risk = rules_result.get('risk_level', 'low')
    ai_risk = ai_result.get('risk_level', 'low')
    merged_risk = ai_risk if _RISK_ORDER.get(ai_risk, 0) > _RISK_ORDER.get(rules_risk, 0) else rules_risk

    rules_dec = rules_result.get('decision', 'ready')
    ai_dec = ai_result.get('decision', 'ready')
    merged_decision = ai_dec if _DECISION_ORDER.get(ai_dec, 0) > _DECISION_ORDER.get(rules_dec, 0) else rules_dec

    merged_reasons = list(rules_result.get('reasons', []))
    for r in ai_result.get('reasons', []):
        # не дублируем если такой код уже есть
        if not any(x.get('code') == r.get('code') for x in merged_reasons):
            merged_reasons.append(r)

    merged_onchain = rules_result.get('requires_onchain_action', False) or \
        ai_result.get('requires_onchain_action', False)

    # Если AI повысил риск до high — onchain только если оба согласны
    if merged_risk == 'high' and ai_result.get('risk_level') == 'high':
        merged_onchain = False

    reasoning = ai_result.get('reasoning_summary') or rules_result.get('reasoning_summary', '')

    return {
        'decision': merged_decision,
        'risk_level': merged_risk,
        'confidence': ai_result.get('confidence', rules_result.get('confidence', 0.5)),
        'reasons': merged_reasons,
        'required_action': ai_result.get('required_action') or rules_result.get('required_action', 'none'),
        'requires_onchain_action': merged_onchain,
        'requires_manual_review': ai_result.get('requires_manual_review', False),
        'reasoning_summary': reasoning,
        'ai_used': True,
        'ai_fallback': False,
        'ai_model_used': ai_result.get('ai_model_used'),
        'ai_tokens_used': ai_result.get('ai_tokens_used', 0),
    }
