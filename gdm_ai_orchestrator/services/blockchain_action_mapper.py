# -*- coding: utf-8 -*-


def map_action(decision):
    if not decision.requires_onchain_action:
        return None

    # CONTRACT
    if decision.entity_model == 'gdm.contract':
        if decision.required_action == 'prepare_onchain':
            return {
                'method': 'register_contract_state',
                'action': 'register'
            }
        if decision.final_status == 'approved':
            return {
                'method': 'change_contract_status',
                'action': 'update'
            }

    # DOCUMENTS
    if decision.entity_model in ('gdm.snt', 'gdm.invoice'):
        if decision.required_action == 'register_document':
            return {
                'method': 'register_document_hash',
                'action': 'register'
            }
        if decision.required_action == 'verify_document':
            return {
                'method': 'verify_document_state',
                'action': 'verify'
            }

    return None
