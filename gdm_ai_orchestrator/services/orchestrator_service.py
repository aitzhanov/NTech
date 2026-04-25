# -*- coding: utf-8 -*-
import logging
from odoo import models
from .context_builder import build_contract_context
from .rules_engine import evaluate_rules
from .ai_service_adapter import analyze_with_claude, merge_results
from .decision_composer import compose_decision_vals
from .action_router import resolve_route
from .blockchain_payload_builder import build_payload
from .document_hash_service import build_document_hash
from .audit_logger import (
    audit_decision_created,
    audit_action_routed,
    audit_blockchain_submitted,
    audit_blockchain_failed,
)

_logger = logging.getLogger(__name__)

# Models handled as "contracts" — support both standalone and gdm-full
_CONTRACT_MODELS = {'contract.contract', 'gdm.contract'}
# Models handled as "documents"
_DOCUMENT_MODELS = {'gdm.snt', 'gdm.invoice'}


class GDMOrchestratorService(models.AbstractModel):
    _name = 'gdm.ai.orchestrator.service'
    _description = 'GDM AI Orchestrator Service'

    def _is_duplicate(self, model, res_id, event, decision_vals):
        domain = [
            ('entity_model', '=', model),
            ('entity_res_id', '=', res_id),
            ('trigger_event', '=', event),
            ('decision', '=', decision_vals.get('decision')),
            ('final_status', '=', decision_vals.get('final_status')),
        ]
        existing = self.env['gdm.ai.decision'].search(domain, limit=1, order='id desc')
        return bool(existing)

    def handle_event(self, model, res_id, event):
        try:
            if model in _CONTRACT_MODELS:
                self._handle_contract_event(model, res_id, event)
            elif model in _DOCUMENT_MODELS:
                self._handle_document_event(model, res_id, event)
            else:
                _logger.debug('[orchestrator] unsupported model=%s — skipped', model)
        except Exception:
            _logger.exception(
                '[orchestrator] handle_event failed model=%s res_id=%s event=%s',
                model, res_id, event,
            )

    # ── Contract pipeline ──────────────────────────────────────────────────────

    def _handle_contract_event(self, model, res_id, event):
        contract = self.env[model].browse(res_id)
        if not contract.exists():
            return

        # 3.2 Context Building
        context = build_contract_context(self.env, contract)

        # 3.3 Rule Pre-Check
        rules_result = evaluate_rules(context, env=self.env)

        # 3.4 AI Analysis (через arch_claude_client)
        ai_result = analyze_with_claude(
            env=self.env,
            context=context,
            rules_result=rules_result,
            entity_model=model,
        )

        # 3.5 Decision Composition (rules + AI → merged)
        merged = merge_results(rules_result, ai_result)
        vals = compose_decision_vals(contract, event, merged, context)
        vals['entity_model'] = model

        if self._is_duplicate(model, res_id, event, vals):
            _logger.debug('[orchestrator] duplicate skipped model=%s res_id=%s', model, res_id)
            return

        decision = self.env['gdm.ai.decision'].create(vals)
        audit_decision_created(self.env, decision)

        # 3.6 Action Routing
        route_cfg = resolve_route(decision)
        action_route = route_cfg.get('route', 'notify_only')
        decision.write({'action_route': action_route})
        audit_action_routed(self.env, decision, action_route)

        # Blockchain dispatch если нужно
        if decision.requires_onchain_action and route_cfg.get('bridge_method'):
            self._dispatch_blockchain(decision, route_cfg)

    # ── Document pipeline ──────────────────────────────────────────────────────

    def _handle_document_event(self, model, res_id, event):
        document = self.env[model].browse(res_id)
        if not document.exists():
            return

        context = {
            'model': model,
            'id': res_id,
            'contract_id': document.contract_id.id if document.contract_id else None,
        }

        has_contract = bool(document.contract_id)

        # Базовый rules-результат для документа
        rules_result = {
            'decision': 'ready' if has_contract else 'not_ready',
            'risk_level': 'low' if has_contract else 'high',
            'confidence': 0.95 if has_contract else 0.99,
            'reasons': [] if has_contract else [
                {'code': 'no_parent_contract', 'message': 'Document has no parent contract.',
                 'level': 'error', 'field': 'contract_id'}
            ],
            'required_action': 'register_document' if has_contract else 'complete_master_data',
            'requires_onchain_action': has_contract,
            'requires_manual_review': False,
            'reasoning_summary': 'Document linked to contract.' if has_contract
            else 'Document has no parent contract.',
        }

        # AI Analysis для документа
        ai_result = analyze_with_claude(
            env=self.env,
            context=context,
            rules_result=rules_result,
            entity_model=model,
        )

        merged = merge_results(rules_result, ai_result)

        vals = {
            'entity_model': model,
            'entity_res_id': res_id,
            'trigger_event': event,
            'decision_type': 'document_health',
            'decision': merged.get('decision'),
            'risk_level': merged.get('risk_level'),
            'confidence': merged.get('confidence', 0.5),
            'reasoning_summary': merged.get('reasoning_summary', ''),
            'reasons_json': merged.get('reasons', []),
            'required_action': merged.get('required_action', 'none'),
            'requires_onchain_action': merged.get('requires_onchain_action', False),
            'requires_manual_review': merged.get('requires_manual_review', False),
            'context_snapshot_json': context,
            'final_status': 'approved' if merged.get('decision') in ('ready', 'ok') else 'rejected',
            'ai_used': merged.get('ai_used', False),
            'ai_fallback': merged.get('ai_fallback', False),
            'ai_model_used': merged.get('ai_model_used') or '',
            'ai_tokens_used': merged.get('ai_tokens_used', 0),
        }

        if self._is_duplicate(model, res_id, event, vals):
            return

        decision = self.env['gdm.ai.decision'].create(vals)
        audit_decision_created(self.env, decision)

        route_cfg = resolve_route(decision)
        decision.write({'action_route': route_cfg.get('route', 'notify_only')})
        audit_action_routed(self.env, decision, route_cfg.get('route'))

        if decision.requires_onchain_action and route_cfg.get('bridge_method'):
            self._dispatch_blockchain(decision, route_cfg, document=document)

    # ── Blockchain dispatch ────────────────────────────────────────────────────

    def _dispatch_blockchain(self, decision, route_cfg=None, document=None):
        if route_cfg is None:
            route_cfg = resolve_route(decision)

        bridge_method_name = route_cfg.get('bridge_method')
        bridge_action = route_cfg.get('bridge_action', 'register')
        if not bridge_method_name:
            return

        payload = build_payload(decision, bridge_action)

        # Enrich for contracts
        if decision.entity_model in _CONTRACT_MODELS:
            contract = self.env[decision.entity_model].browse(decision.entity_res_id)
            if contract.exists():
                contract_key = (contract.uuid or contract.number or '').replace('-', '')
                payload['entity_id'] = contract_key
                payload['data']['contract_id'] = contract_key
                payload['data']['version'] = (contract.onchain_version or 0) + 1

        # Enrich for documents
        if decision.entity_model in _DOCUMENT_MODELS:
            if document is None:
                document = self.env[decision.entity_model].browse(decision.entity_res_id)
            if document.exists():
                payload['data']['document_hash'] = build_document_hash(document)
                if document.contract_id:
                    payload['data']['contract_id'] = (
                        document.contract_id.uuid.replace('-', '')
                        if document.contract_id.uuid
                        else str(document.contract_id.id)
                    )

        decision.write({
            'blockchain_sync_status': 'prepared',
            'blockchain_payload_json': payload,
        })

        client = self.env['gdm.solana.bridge.client']
        method = getattr(client, bridge_method_name, None)
        if method is None:
            _logger.error('[orchestrator] bridge method not found: %s', bridge_method_name)
            return

        try:
            response = method(payload)
        except Exception as exc:
            _logger.exception('[orchestrator] bridge call failed: %s', exc)
            decision.write({
                'blockchain_sync_status': 'failed',
                'blockchain_error_code': 'exception',
                'blockchain_error_message': str(exc),
            })
            audit_blockchain_failed(self.env, decision, 'exception', str(exc))
            return

        if response.get('ok'):
            request_id = response.get('request_id')
            tx_hash = response.get('tx_hash')
            sync_status = 'confirmed' if response.get('status') in ('confirmed', 'finalized') else 'submitted'
            if response.get('skipped'):
                sync_status = 'confirmed'

            decision.write({
                'blockchain_request_id': request_id,
                'blockchain_tx_hash': tx_hash,
                'blockchain_action': bridge_method_name,
                'blockchain_sync_status': sync_status,
                'blockchain_action_status': 'done' if sync_status == 'confirmed' else 'pending',
                'final_status': 'completed' if sync_status == 'confirmed' else 'pending_onchain',
            })
            audit_blockchain_submitted(self.env, decision, request_id, tx_hash)

            if decision.entity_model in _CONTRACT_MODELS:
                self._sync_contract_blockchain_fields(decision, response)
        else:
            error_code = response.get('error_code', 'bridge_error')
            error_message = response.get('error_message', str(response))
            decision.write({
                'blockchain_sync_status': 'failed',
                'blockchain_action_status': 'failed',
                'blockchain_error_code': error_code,
                'blockchain_error_message': error_message,
            })
            audit_blockchain_failed(self.env, decision, error_code, error_message)

    def _sync_contract_blockchain_fields(self, decision, response):
        try:
            contract = self.env[decision.entity_model].browse(decision.entity_res_id)
            if not contract.exists():
                return
            onchain = response.get('onchain_state') or {}
            write_vals = {}
            if response.get('tx_hash') and not contract.blockchain_tx:
                write_vals['blockchain_tx'] = response['tx_hash']
            if response.get('status'):
                write_vals['blockchain_status'] = response['status']
            if onchain.get('version'):
                write_vals['onchain_version'] = onchain['version']
            if write_vals:
                contract.write(write_vals)
        except Exception:
            _logger.exception(
                '[orchestrator] _sync_contract_blockchain_fields failed decision=%s', decision.id
            )
