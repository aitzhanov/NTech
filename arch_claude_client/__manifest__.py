# -*- coding: utf-8 -*-
# Copyright (C) 2019-2026 NeuroTech(<https://neurotech.kz>).
{
    'name': 'Arch Claude Client',
    'version': '15.0.1.1.0',
    'summary': 'Technical adapter for Anthropic Claude API',
    'description': (
        'Low-level adapter to Anthropic Claude API. '
        'Provides gdm.claude.agent — a structured AI analysis service '
        'used by gdm_ai_orchestrator as its AI decision component.'
    ),
    'author': 'NeuroTech LLC',
    'license': 'OPL-1',
    'website': 'https://neurotech.kz',
    'category': 'Technical',
    'depends': [
        'base',
        'base_setup',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/claude_agent_views.xml',
    ],
    'installable': True,
    'application': False,
}
