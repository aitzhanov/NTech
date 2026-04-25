# -*- coding: utf-8 -*-
from odoo import models, fields


class BlockchainCallbackService(models.AbstractModel):
    _name = 'gdm.blockchain.callback.service'
    _description = 'Blockchain Callback Processor'

    def process_callback(self, payload):
        request_id = payload.get('request_id')
        decision_id = payload.get('decision_id')
        status = payload.get('status')

        if not request_id:
            return {'ok': False, 'error': 'missing_request_id'}

        decision = self.env['gdm.ai.decision'].search([
            ('blockchain_request_id', '=', request_id)
        ], limit=1)

        if not decision:
            return {'ok': False, 'error': 'decision_not_found'}

        if decision_id and str(decision.id) != str(decision_id):
            return {'ok': False, 'error': 'decision_id_mismatch'}

        # idempotency: ignore identical final states
        if decision.blockchain_sync_status in ('confirmed', 'failed') and decision.blockchain_sync_status == status:
            return {'ok': True, 'skipped': True}

        values = {
            'blockchain_tx_hash': payload.get('tx_hash') or decision.blockchain_tx_hash,
            'blockchain_last_sync_at': fields.Datetime.now(),
        }

        if status == 'confirmed':
            values.update({
                'blockchain_sync_status': 'confirmed',
                'blockchain_error_code': False,
                'blockchain_error_message': False,
            })

        elif status == 'failed':
            error = payload.get('error') or {}
            values.update({
                'blockchain_sync_status': 'failed',
                'blockchain_error_code': error.get('code') if isinstance(error, dict) else None,
                'blockchain_error_message': error.get('message') if isinstance(error, dict) else str(error),
            })

        else:
            values['blockchain_sync_status'] = status

        decision.write(values)
        return {'ok': True}


class BlockchainReconciliationService(models.AbstractModel):
    _name = 'gdm.blockchain.reconciliation.service'
    _description = 'Blockchain Reconciliation Service'

    def resync_decision_blockchain_state(self, decision):
        if not decision.blockchain_request_id:
            return {'ok': False, 'error': 'missing_request_id'}

        client = self.env['gdm.solana.bridge.client']
        response = client.get_onchain_state({
            'request_id': decision.blockchain_request_id
        })

        if not response.get('ok'):
            decision.write({
                'blockchain_sync_status': 'resync_required',
                'blockchain_error_code': response.get('error_code'),
                'blockchain_error_message': response.get('error_message'),
            })
            return response

        return self.env['gdm.blockchain.callback.service'].process_callback(response)

    def resync_by_request_id(self, request_id):
        decision = self.env['gdm.ai.decision'].search([
            ('blockchain_request_id', '=', request_id)
        ], limit=1)

        if not decision:
            return {'ok': False, 'error': 'decision_not_found'}

        return self.resync_decision_blockchain_state(decision)

    def resync_pending(self):
        decisions = self.env['gdm.ai.decision'].search([
            ('blockchain_sync_status', 'in', ['submitted', 'resync_required'])
        ])

        results = []
        for decision in decisions:
            results.append(self.resync_decision_blockchain_state(decision))

        return results
