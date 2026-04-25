# -*- coding: utf-8 -*-
"""
res.config.settings — расширение для настроек Claude API.

Поля отображаются в Настройки → Claude AI.
Значения хранятся в ir.config_parameter (те же ключи,
что использует gdm.claude.agent при вызове API).
"""
from odoo import models, fields, api


class ClaudeAgentSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ── Подключение ────────────────────────────────────────────────────────────
    arch_claude_api_key = fields.Char(
        string='API Key',
        config_parameter='arch_claude.api_key',
        help='Секретный ключ Anthropic. Получить на https://console.anthropic.com',
    )
    arch_claude_model = fields.Selection(
        selection=[
            ('claude-opus-4-5',          'Claude Opus 4.5'),
            ('claude-sonnet-4-5',        'Claude Sonnet 4.5 (рекомендуется)'),
            ('claude-haiku-4-5',         'Claude Haiku 4.5 (быстрый)'),
            ('claude-opus-4-20250514',   'Claude Opus 4 (legacy)'),
            ('claude-sonnet-4-20250514', 'Claude Sonnet 4 (legacy)'),
        ],
        string='Model',
        config_parameter='arch_claude.model',
        default='claude-sonnet-4-5',
        help='Модель Claude для AI-анализа. Sonnet 4.5 — оптимальный баланс качества и скорости.',
    )
    arch_claude_timeout = fields.Integer(
        string='Timeout (сек)',
        config_parameter='arch_claude.timeout',
        default=30,
        help='Максимальное время ожидания ответа от Claude API в секундах.',
    )
    arch_claude_enabled = fields.Boolean(
        string='Включить Claude AI',
        config_parameter='arch_claude.enabled',
        default=True,
        help='Если выключено — orchestrator работает только на правилах, AI не вызывается.',
    )

    # ── Ping-кнопка ───────────────────────────────────────────────────────────
    def action_claude_ping(self):
        """Проверить связь с Claude API и показать результат."""
        self.ensure_one()
        result = self.env['gdm.claude.agent'].ping()
        if result.get('ok'):
            msg = 'Соединение успешно. Модель: {}'.format(result.get('model', '—'))
            msg_type = 'success'
        else:
            msg = 'Ошибка: {}'.format(result.get('error', 'неизвестная ошибка'))
            msg_type = 'danger'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Claude API Ping',
                'message': msg,
                'type': msg_type,
                'sticky': False,
            },
        }
