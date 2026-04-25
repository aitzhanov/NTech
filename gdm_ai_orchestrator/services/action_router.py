# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

_ROUTE_TABLE = [
    {
        'model': 'contract.contract',
        'required_action': 'prepare_onchain',
        'final_status': 'approved',
        'route': 'prepare_onchain',
        'bridge_method': 'register_contract_state',
        'bridge_action': 'register',
        'notify': True,
    },
    {
        'model': 'contract.contract',
        'required_action': 'complete_master_data',
        'final_status': 'rejected',
        'route': 'blocked_until_fix',
        'bridge_method': None,
        'notify': True,
    },
    {
        'model': 'contract.contract',
        'required_action': 'fix_dates',
        'final_status': 'rejected',
        'route': 'blocked_until_fix',
        'bridge_method': None,
        'notify': True,
    },
    {
        'model': 'contract.contract',
        'required_action': 'review_financials',
        'final_status': None,
        'route': 'manual_review',
        'bridge_method': None,
        'notify': True,
    },
    {
        'model': 'contract.contract',
        'required_action': 'manual_review',
        'final_status': None,
        'route': 'manual_review',
        'bridge_method': None,
        'notify': True,
    },
    {
        'model': 'gdm.snt',
        'required_action': 'register_document',
        'final_status': None,
        'route': 'prepare_onchain',
        'bridge_method': 'register_document_hash',
        'bridge_action': 'register',
        'notify': False,
    },
    {
        'model': 'gdm.snt',
        'required_action': 'verify_document',
        'final_status': None,
        'route': 'prepare_onchain',
        'bridge_method': 'verify_document_state',
        'bridge_action': 'verify',
        'notify': False,
    },
    {
        'model': 'gdm.invoice',
        'required_action': 'register_document',
        'final_status': None,
        'route': 'prepare_onchain',
        'bridge_method': 'register_document_hash',
        'bridge_action': 'register',
        'notify': False,
    },
    {
        'model': 'gdm.invoice',
        'required_action': 'verify_document',
        'final_status': None,
        'route': 'prepare_onchain',
        'bridge_method': 'verify_document_state',
        'bridge_action': 'verify',
        'notify': False,
    },
]

_DEFAULT_ROUTE = {
    'route': 'notify_only',
    'bridge_method': None,
    'notify': False,
}


def resolve_route(decision):
    model = decision.entity_model
    required_action = decision.required_action
    final_status = decision.final_status

    for rule in _ROUTE_TABLE:
        if rule['model'] != model:
            continue
        if rule['required_action'] != required_action:
            continue
        if rule.get('final_status') is not None and rule['final_status'] != final_status:
            continue
        _logger.debug(
            'action_router: matched model=%s required_action=%s -> route=%s bridge=%s',
            model, required_action, rule['route'], rule.get('bridge_method'),
        )
        return rule

    _logger.debug(
        'action_router: no rule matched model=%s required_action=%s — default',
        model, required_action,
    )
    return _DEFAULT_ROUTE
