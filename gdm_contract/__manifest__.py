# -*- coding: utf-8 -*-
# Copyright (C) 2019-2026 NeuroTech(<https://neurotech.kz>).
{
    'name': 'GDM Contract',
    'version': '15.0.1.0.0',
    'summary': 'Standalone contract management module — works without the full GDM suite',
    'description': (
        'Self-contained contract module with blockchain integration. '
        'Provides gdm.contract, gdm.contract.stage, gdm.contract.type models '
        'and a dedicated menu. Compatible with gdm_ai_orchestrator and gdm_solana_bridge.'
    ),
    'author': 'NeuroTech LLC',
    'license': 'OPL-1',
    'website': 'https://neurotech.kz',
    'category': 'Industries',
    'depends': [
        'base',
        'mail',
        'uom',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/contract_sequence.xml',
        'views/contract_stage_views.xml',
        'views/contract_type_views.xml',
        'views/contract_views.xml',
        'views/blockchain_dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
