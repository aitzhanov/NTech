# -*- coding: utf-8 -*-
"""
gdm.claude.agent
================
Технический AI-адаптер к Anthropic Claude API.

Роль в архитектуре:
  - Этот модуль — ТЕХНИЧЕСКИЙ адаптер (аналог arch_openai_client).
  - Он НЕ принимает бизнес-решений самостоятельно.
  - Он вызывается из gdm_ai_orchestrator через claude_agent_adapter.
  - Возвращает структурированный JSON-ответ, который orchestrator
    интерпретирует и превращает в управленческое решение.

Конфигурация:
  - api_key хранится в ir.config_parameter: arch_claude.api_key
  - модель — в ir.config_parameter: arch_claude.model (default: claude-sonnet-4-5)
  - таймаут — в ir.config_parameter: arch_claude.timeout (default: 30)
  - включение/выключение — arch_claude.enabled (default: True)
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'
CLAUDE_API_VERSION = '2023-06-01'
DEFAULT_MODEL = 'claude-sonnet-4-5'
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_TOKENS = 1024

# ── Системный промпт для AI-анализа GDM-сущностей ─────────────────────────────
_SYSTEM_PROMPT = """You are a structured AI decision component for a gas delivery management system (GDM).

Your role is to analyse the provided business context and return a structured JSON decision.
You do NOT produce free text. You ONLY respond with a valid JSON object.

Required JSON structure:
{
  "decision_type": "contract_readiness" | "document_health" | "risk_assessment" | "compliance_check",
  "decision": "ready" | "not_ready" | "review" | "invalid" | "ok",
  "risk_level": "low" | "medium" | "high",
  "confidence": <float 0.0–1.0>,
  "reasons": [
    {"code": "<str>", "message": "<str>", "level": "info"|"warning"|"error", "field": "<str or null>"}
  ],
  "required_action": "none" | "complete_master_data" | "review_financials" | "fix_dates" |
                     "prepare_onchain" | "register_document" | "escalate_to_manager",
  "requires_manual_review": <bool>,
  "requires_onchain_action": <bool>,
  "reasoning_summary": "<one sentence summary in the same language as the context>"
}

Rules:
- Respond ONLY with the JSON object. No preamble, no markdown, no explanation.
- If context is insufficient, set decision="review", risk_level="medium", requires_manual_review=true.
- confidence must reflect your actual certainty (0.5–0.99 range in practice).
- reasons array may be empty if no issues found.
"""


class GdmClaudeAgent(models.AbstractModel):
    """
    Технический адаптер к Anthropic Claude API.

    Используется как AI-компонент в pipeline:
        gdm_ai_orchestrator → claude_agent_adapter → gdm.claude.agent.analyze()

    Метод analyze() принимает контекст бизнес-сущности и сценарий,
    возвращает структурированный словарь решения.
    """
    _name = 'gdm.claude.agent'
    _description = 'Arch Claude Agent — AI Adapter for Anthropic Claude API'

    # ── Публичный API ──────────────────────────────────────────────────────────

    @api.model
    def analyze(self, context, scenario='contract_readiness'):
        """
        Основной метод анализа. Вызывается из orchestrator.

        :param context: dict — нормализованный контекст сущности (из context_builder)
        :param scenario: str — тип анализа (используется как подсказка в промпте)
        :return: dict со структурой:
            {
              'decision_type', 'decision', 'risk_level', 'confidence',
              'reasons', 'required_action', 'requires_manual_review',
              'requires_onchain_action', 'reasoning_summary',
              'ai_model_used', 'ai_tokens_used',
            }
        """
        if not self._is_enabled():
            _logger.info('[claude_agent] disabled — returning fallback')
            return self._fallback_result(scenario, reason='agent_disabled')

        api_key = self._get_api_key()
        if not api_key:
            _logger.warning('[claude_agent] api_key not configured')
            return self._fallback_result(scenario, reason='no_api_key')

        user_prompt = self._build_user_prompt(context, scenario)
        model = self._get_param('arch_claude.model', DEFAULT_MODEL)
        timeout = int(self._get_param('arch_claude.timeout', DEFAULT_TIMEOUT))

        raw_response = self._call_api(api_key, model, user_prompt, timeout)
        if raw_response is None:
            return self._fallback_result(scenario, reason='api_call_failed')

        result = self._parse_response(raw_response)
        if result is None:
            return self._fallback_result(scenario, reason='parse_failed')

        # Обогащаем мета-данными
        result['ai_model_used'] = model
        result['ai_tokens_used'] = (
            raw_response.get('usage', {}).get('input_tokens', 0)
            + raw_response.get('usage', {}).get('output_tokens', 0)
        )

        self._log_call(scenario, context, result, raw_response)
        return result

    @api.model
    def ping(self):
        """
        Проверка связи с Claude API.
        Возвращает {'ok': True/False, 'model': '...', 'error': '...'}
        """
        api_key = self._get_api_key()
        if not api_key:
            return {'ok': False, 'error': 'api_key not configured'}
        model = self._get_param('arch_claude.model', DEFAULT_MODEL)
        payload = {
            'model': model,
            'max_tokens': 10,
            'messages': [{'role': 'user', 'content': 'ping'}],
        }
        try:
            resp = self._http_post(CLAUDE_API_URL, payload, api_key, timeout=10)
            return {'ok': True, 'model': model, 'response': resp.get('id', 'ok')}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            _logger.error('[claude_agent] ping HTTP %s: %s', exc.code, body)
            return {'ok': False, 'error': 'HTTP {}: {}'.format(exc.code, body)}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    # ── Внутренние методы ──────────────────────────────────────────────────────

    def _is_enabled(self):
        val = self._get_param('arch_claude.enabled', 'True')
        return str(val).lower() not in ('false', '0', 'no', '')

    def _get_api_key(self):
        return (self._get_param('arch_claude.api_key', '') or '').strip()

    def _get_param(self, key, default=None):
        return self.env['ir.config_parameter'].sudo().get_param(key, default)

    def _build_user_prompt(self, context, scenario):
        return (
            'Scenario: {}\n\n'
            'Business context (JSON):\n{}\n\n'
            'Analyse the context and return your structured JSON decision.'
        ).format(scenario, json.dumps(context, ensure_ascii=False, indent=2))

    def _call_api(self, api_key, model, user_prompt, timeout):
        payload = {
            'model': model,
            'max_tokens': DEFAULT_MAX_TOKENS,
            'system': _SYSTEM_PROMPT,
            'messages': [{'role': 'user', 'content': user_prompt}],
        }
        try:
            return self._http_post(CLAUDE_API_URL, payload, api_key, timeout)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            _logger.error('[claude_agent] HTTP %s: %s', exc.code, body)
            return None
        except Exception as exc:
            _logger.error('[claude_agent] call_api exception: %s', exc)
            return None

    def _http_post(self, url, payload, api_key, timeout):
        """Синхронный HTTP POST к Claude API через стандартную библиотеку urllib."""
        data = json.dumps(payload).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': CLAUDE_API_VERSION,
        }
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def _parse_response(self, raw):
        """
        Извлекает текстовый контент из ответа Claude и парсит JSON.
        Claude возвращает: {'content': [{'type': 'text', 'text': '...'}], ...}
        """
        try:
            content_blocks = raw.get('content', [])
            text = ''.join(
                b.get('text', '') for b in content_blocks if b.get('type') == 'text'
            ).strip()
            # Убираем возможные markdown-обёртки (```json ... ```)
            if text.startswith('```'):
                lines = text.splitlines()
                text = '\n'.join(
                    l for l in lines if not l.strip().startswith('```')
                ).strip()
            parsed = json.loads(text)
            return self._validate_result(parsed)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            _logger.error('[claude_agent] parse_response failed: %s', exc)
            return None

    def _validate_result(self, data):
        """Нормализует ответ — заполняет отсутствующие поля дефолтами."""
        valid_decisions = {'ready', 'not_ready', 'review', 'invalid', 'ok'}
        valid_risks = {'low', 'medium', 'high'}
        valid_actions = {
            'none', 'complete_master_data', 'review_financials', 'fix_dates',
            'prepare_onchain', 'register_document', 'escalate_to_manager',
        }
        return {
            'decision_type': data.get('decision_type', 'risk_assessment'),
            'decision': data.get('decision', 'review') if data.get('decision') in valid_decisions else 'review',
            'risk_level': data.get('risk_level', 'medium') if data.get('risk_level') in valid_risks else 'medium',
            'confidence': max(0.0, min(1.0, float(data.get('confidence', 0.5)))),
            'reasons': data.get('reasons', []) if isinstance(data.get('reasons'), list) else [],
            'required_action': data.get('required_action', 'none') if data.get('required_action') in valid_actions else 'none',
            'requires_manual_review': bool(data.get('requires_manual_review', False)),
            'requires_onchain_action': bool(data.get('requires_onchain_action', False)),
            'reasoning_summary': str(data.get('reasoning_summary', '')),
        }

    def _fallback_result(self, scenario, reason='unknown'):
        """
        Возвращается когда Claude недоступен.
        Orchestrator продолжает работу на основе rules engine.
        """
        _logger.info('[claude_agent] fallback triggered: %s', reason)
        return {
            'decision_type': scenario,
            'decision': 'review',
            'risk_level': 'medium',
            'confidence': 0.0,
            'reasons': [{'code': 'ai_unavailable', 'message': 'Claude AI unavailable: {}'.format(reason),
                         'level': 'warning', 'field': None}],
            'required_action': 'none',
            'requires_manual_review': True,
            'requires_onchain_action': False,
            'reasoning_summary': 'AI analysis unavailable ({}). Manual review recommended.'.format(reason),
            'ai_model_used': None,
            'ai_tokens_used': 0,
            'fallback': True,
        }

    def _log_call(self, scenario, context, result, raw):
        """Запись лога вызова в gdm.claude.agent.log."""
        try:
            self.env['gdm.claude.agent.log'].sudo().create({
                'scenario': scenario,
                'model_used': result.get('ai_model_used', ''),
                'tokens_used': result.get('ai_tokens_used', 0),
                'decision': result.get('decision', ''),
                'risk_level': result.get('risk_level', ''),
                'confidence': result.get('confidence', 0.0),
                'reasoning_summary': result.get('reasoning_summary', ''),
                'fallback': result.get('fallback', False),
                'context_snapshot': json.dumps(context, ensure_ascii=False),
                'raw_response': json.dumps(raw, ensure_ascii=False),
            })
        except Exception as exc:
            _logger.warning('[claude_agent] log_call failed: %s', exc)
