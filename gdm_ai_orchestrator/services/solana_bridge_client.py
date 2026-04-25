# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models

_logger = logging.getLogger(__name__)

# Real bridge endpoints — matching gdm_solana_bridge FastAPI routes
_ENDPOINT_REGISTER_AND_TRACK = '/tx/register_and_track'
_ENDPOINT_GET_CONTRACT = '/contract/{contract_id}'
_ENDPOINT_GET_TX = '/tx/{signature}'
_ENDPOINT_HEALTH = '/health'


class SolanaBridgeClient(models.AbstractModel):
    _name = 'gdm.solana.bridge.client'
    _description = 'GDM Solana Bridge Client'

    def _get_bridge_config(self):
        icp = self.env['ir.config_parameter'].sudo()
        base_url = (
            icp.get_param('gdm.solana_bridge_url')
            or icp.get_param('gdm_ai_orchestrator.solana_bridge_base_url')
            or 'http://172.17.0.1:8181'
        ).rstrip('/')
        timeout = int(icp.get_param('gdm_ai_orchestrator.solana_bridge_timeout') or 30)
        return {
            'base_url': base_url,
            'timeout': timeout,
        }

    def _normalize_contract_id(self, contract_id):
        """
        UUID without dashes = 32 hex chars = exactly 32 bytes.
        Must match _normalize_contract_id() in gdm_solana_bridge.
        """
        return str(contract_id).replace('-', '')

    def _normalize_error(self, code, message, details=None):
        return {
            'ok': False,
            'status': 'failed',
            'error_code': code,
            'error_message': message,
            'details': details or {},
        }

    def _post(self, endpoint, payload):
        config = self._get_bridge_config()
        url = '%s%s' % (config['base_url'], endpoint)
        _logger.info('[solana_bridge_client] POST %s payload=%s', url, payload)
        try:
            response = requests.post(url, json=payload, timeout=config['timeout'])
            response.raise_for_status()
            data = response.json()
            data.setdefault('ok', True)
            return data
        except requests.exceptions.RequestException as exc:
            _logger.exception('[solana_bridge_client] POST %s failed: %s', url, exc)
            return self._normalize_error('bridge_connection_error', str(exc))
        except ValueError as exc:
            return self._normalize_error('bridge_invalid_json', str(exc))

    def _get(self, endpoint):
        config = self._get_bridge_config()
        url = '%s%s' % (config['base_url'], endpoint)
        _logger.info('[solana_bridge_client] GET %s', url)
        try:
            response = requests.get(url, timeout=config['timeout'])
            response.raise_for_status()
            data = response.json()
            data.setdefault('ok', True)
            return data
        except requests.exceptions.RequestException as exc:
            _logger.exception('[solana_bridge_client] GET %s failed: %s', url, exc)
            return self._normalize_error('bridge_connection_error', str(exc))
        except ValueError as exc:
            return self._normalize_error('bridge_invalid_json', str(exc))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_contract_state(self, payload):
        """
        Register a contract on-chain via POST /tx/register_and_track.

        Expects payload to contain:
            contract_id  - str (uuid without dashes, 32 bytes)
            version      - int (default 1)

        Returns bridge response dict with keys: ok, tx, tx_status, onchain_state
        """
        entity_id = payload.get('entity_id') or payload.get('data', {}).get('contract_id')
        if not entity_id:
            return self._normalize_error('missing_contract_id', 'contract_id is required')

        contract_id = self._normalize_contract_id(entity_id)
        version = int(payload.get('data', {}).get('version') or 1)

        bridge_payload = {
            'type': 'register_contract',
            'contract_id': contract_id,
            'version': version,
            'wait_for': 'confirmed',
            'timeout_seconds': 30,
        }
        response = self._post(_ENDPOINT_REGISTER_AND_TRACK, bridge_payload)

        # Normalize response for orchestrator consumption
        if response.get('ok'):
            tx = response.get('tx') or {}
            tx_status = response.get('tx_status') or {}
            onchain = response.get('onchain_state') or {}
            return {
                'ok': True,
                'request_id': contract_id,
                'tx_hash': tx.get('signature'),
                'status': tx_status.get('status') or tx_status.get('confirmation_status'),
                'onchain_state': onchain,
                'skipped': tx.get('skipped', False),
                'action': 'register_contract_state',
            }
        return response

    def get_contract_state(self, contract_id):
        """
        GET /contract/{contract_id} — read current on-chain state.
        """
        safe_id = self._normalize_contract_id(contract_id)
        endpoint = _ENDPOINT_GET_CONTRACT.format(contract_id=safe_id)
        return self._get(endpoint)

    def get_tx_status(self, signature):
        """
        GET /tx/{signature} — check transaction confirmation status.
        """
        endpoint = _ENDPOINT_GET_TX.format(signature=signature)
        return self._get(endpoint)

    def health(self):
        """
        GET /health — check bridge and validator availability.
        """
        return self._get(_ENDPOINT_HEALTH)

    def change_contract_status(self, payload):
        """
        Change contract status on-chain.
        Currently maps to register_and_track with incremented version.
        Will use approve_contract / block_contract when Rust program exposes those endpoints.
        """
        entity_id = payload.get('entity_id') or payload.get('data', {}).get('contract_id')
        if not entity_id:
            return self._normalize_error('missing_contract_id', 'contract_id is required')

        contract_id = self._normalize_contract_id(entity_id)
        version = int(payload.get('data', {}).get('version') or 2)

        bridge_payload = {
            'type': 'register_contract',
            'contract_id': contract_id,
            'version': version,
            'wait_for': 'confirmed',
            'timeout_seconds': 30,
        }
        response = self._post(_ENDPOINT_REGISTER_AND_TRACK, bridge_payload)
        if response.get('ok'):
            tx = response.get('tx') or {}
            tx_status = response.get('tx_status') or {}
            return {
                'ok': True,
                'request_id': contract_id,
                'tx_hash': tx.get('signature'),
                'status': tx_status.get('status'),
                'action': 'change_contract_status',
            }
        return response

    def register_document_hash(self, payload):
        """
        Register document hash on-chain.
        Uses register_and_track with contract_id derived from document hash.
        """
        document_hash = payload.get('data', {}).get('document_hash')
        if not document_hash:
            return self._normalize_error('missing_document_hash', 'document_hash is required')

        # Use first 32 chars of sha256 hex as contract_id seed for the document PDA
        doc_seed = document_hash[:32]
        bridge_payload = {
            'type': 'register_contract',
            'contract_id': doc_seed,
            'version': 1,
            'wait_for': 'confirmed',
            'timeout_seconds': 30,
        }
        response = self._post(_ENDPOINT_REGISTER_AND_TRACK, bridge_payload)
        if response.get('ok'):
            tx = response.get('tx') or {}
            tx_status = response.get('tx_status') or {}
            return {
                'ok': True,
                'request_id': doc_seed,
                'tx_hash': tx.get('signature'),
                'status': tx_status.get('status'),
                'action': 'register_document_hash',
            }
        return response

    def verify_document_state(self, payload):
        """
        Verify document on-chain by reading its PDA state.
        """
        document_hash = payload.get('data', {}).get('document_hash')
        if not document_hash:
            return self._normalize_error('missing_document_hash', 'document_hash is required')

        doc_seed = document_hash[:32]
        response = self.get_contract_state(doc_seed)
        if response.get('ok'):
            return {
                'ok': True,
                'request_id': doc_seed,
                'found': response.get('found', False),
                'onchain_state': response,
                'action': 'verify_document_state',
            }
        return response

    def get_onchain_state(self, payload):
        """
        Get current on-chain state for a previously submitted request.
        Used by reconciliation service.
        """
        request_id = payload.get('request_id')
        tx_hash = payload.get('tx_hash')

        if tx_hash:
            response = self.get_tx_status(tx_hash)
            if response.get('ok'):
                status = response.get('status') or response.get('confirmation_status')
                return {
                    'ok': True,
                    'request_id': request_id,
                    'tx_hash': tx_hash,
                    'status': 'confirmed' if status == 'finalized' else status,
                    'confirmed_at': None,
                    'action': 'get_onchain_state',
                }
            return response

        if request_id:
            # request_id is normalized contract_id — read PDA state
            response = self.get_contract_state(request_id)
            if response.get('ok'):
                found = response.get('found', False)
                return {
                    'ok': True,
                    'request_id': request_id,
                    'tx_hash': None,
                    'status': 'confirmed' if found else 'not_found',
                    'confirmed_at': None,
                    'action': 'get_onchain_state',
                }
            return response

        return self._normalize_error('missing_identifiers', 'request_id or tx_hash is required')
