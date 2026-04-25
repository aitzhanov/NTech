# -*- coding: utf-8 -*-
# Copyright (C) 2019-2026 NeuroTech(<https://neurotech.kz>).
{
    'name': 'GDM AI Orchestrator',
    'version': '15.0.1.3.0',
    'summary': 'AI orchestration and decision management layer',
    'description': (
        'Non-invasive orchestration layer for AI-ready decision management. '
        'Works with gdm_contract (standalone) or full gdm suite. '
        'Uses arch_claude_client (gdm.claude.agent) as the AI analysis component.'
    ),
    'author': 'NeuroTech LLC',
    'license': 'OPL-1',
    'website': 'https://neurotech.kz',
    'category': 'Industries',
    'depends': [
        'base',
        'mail',
        'gdm_contract',
        'arch_claude_client',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/gdm_ai_rule_views.xml',
        'views/gdm_ai_decision_views.xml',
        'views/gdm_contract_ai_views.xml',
        'data/gdm_ai_rule_data.xml',
    ],
    'installable': True,
    'application': False,
}
