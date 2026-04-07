# -*- coding: utf-8 -*-
"""
gdm.claude.agent.log
====================
Лог вызовов Claude API. Хранит трассировку каждого AI-запроса.
Используется для аудита, диагностики и анализа производительности.
"""
import json
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class GdmClaudeAgentLog(models.Model):
    _name = 'gdm.claude.agent.log'
    _description = 'Claude Agent Call Log'
    _order = 'create_date desc'
    _rec_name = 'scenario'

    # ── Идентификация вызова ───────────────────────────────────────────────────
    scenario = fields.Char(
        string='Scenario',
        required=True,
        help='Тип анализа: contract_readiness, document_health, etc.',
    )
    model_used = fields.Char(string='Model', help='Claude model name used for this call')
    tokens_used = fields.Integer(string='Tokens Used', default=0)
    fallback = fields.Boolean(string='Fallback', default=False,
                              help='True = Claude был недоступен, вернули fallback')

    # ── Результат ─────────────────────────────────────────────────────────────
    decision = fields.Selection([
        ('ready', 'Ready'),
        ('not_ready', 'Not Ready'),
        ('review', 'Review'),
        ('invalid', 'Invalid'),
        ('ok', 'OK'),
    ], string='Decision')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Level')
    confidence = fields.Float(string='Confidence', digits=(5, 3))
    reasoning_summary = fields.Text(string='Reasoning Summary')

    # ── Трассировка ───────────────────────────────────────────────────────────
    context_snapshot = fields.Text(string='Context Snapshot (JSON)')
    raw_response = fields.Text(string='Raw API Response (JSON)')

    create_date = fields.Datetime(string='Called At', readonly=True)
