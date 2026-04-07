# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class GDMAIDecision(models.Model):
    _name = 'gdm.ai.decision'
    _description = 'GDM AI Decision'
    _order = 'create_date desc, id desc'

    entity_model = fields.Char(required=True, index=True)
    entity_res_id = fields.Integer(required=True, index=True)

    trigger_event = fields.Char(index=True)
    decision_type = fields.Selection([
        ('contract_readiness', 'Contract Readiness'),
        ('contract_consistency', 'Contract Consistency'),
        ('contract_compliance', 'Contract Compliance'),
        ('document_health', 'Document Health'),
        ('document_consistency', 'Document Consistency'),
        ('document_verification', 'Document Verification'),
        ('risk_assessment', 'Risk Assessment'),
        ('manual_review', 'Manual Review'),
    ], required=True, default='contract_readiness', index=True)
    decision = fields.Text()

    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], index=True)
    severity = fields.Selection([
        ('info', 'Info'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='info', required=True, index=True)
    score = fields.Integer(default=0, index=True)

    confidence = fields.Float(digits=(16, 4))

    reasoning_summary = fields.Text()
    reasons_json = fields.Text()

    required_action = fields.Selection([
        ('none', 'None'),
        ('complete_master_data', 'Complete Master Data'),
        ('fix_dates', 'Fix Dates'),
        ('attach_documents', 'Attach Documents'),
        ('review_financials', 'Review Financials'),
        ('manual_review', 'Manual Review'),
        ('escalate', 'Escalate'),
        ('escalate_to_manager', 'Escalate to Manager'),
        ('prepare_onchain', 'Prepare Onchain'),
        ('register_document', 'Register Document'),
        ('verify_document', 'Verify Document'),
    ], default='none', required=True, index=True)
    action_route = fields.Selection([
        ('none', 'None'),
        ('notify_only', 'Notify Only'),
        ('create_task', 'Create Task'),
        ('manual_review', 'Manual Review'),
        ('prepare_onchain', 'Prepare Onchain'),
        ('blocked_until_fix', 'Blocked Until Fix'),
    ], default='none', required=True, index=True)
    requires_manual_review = fields.Boolean()
    requires_onchain_action = fields.Boolean()

    policy_rule_code = fields.Char(index=True)

    context_snapshot_json = fields.Text()
    context_hash = fields.Char(index=True)

    manual_override = fields.Boolean()
    override_reason = fields.Text()

    # ── AI-мета поля ──────────────────────────────────────────────────────────
    ai_used = fields.Boolean(
        string='AI Used', default=False, index=True,
        help='True если gdm.claude.agent был задействован в pipeline',
    )
    ai_fallback = fields.Boolean(
        string='AI Fallback', default=False,
        help='True если Claude был недоступен и решение принято только по rules',
    )
    ai_model_used = fields.Char(
        string='AI Model',
        help='Имя модели Claude, использованной для анализа',
    )
    ai_tokens_used = fields.Integer(
        string='Tokens Used', default=0,
        help='Количество токенов использованных в AI-вызове',
    )

    # ── Blockchain поля ────────────────────────────────────────────────────────
    blockchain_action_status = fields.Selection([
        ('none', 'None'),
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('failed', 'Failed')
    ], default='none')

    blockchain_tx_hash = fields.Char()
    blockchain_request_id = fields.Char()
    blockchain_action = fields.Char()
    blockchain_sync_status = fields.Selection([
        ('none', 'None'),
        ('prepared', 'Prepared'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('timed_out', 'Timed Out'),
        ('resync_required', 'Resync Required'),
    ], default='none')
    blockchain_payload_json = fields.Text()
    blockchain_last_sync_at = fields.Datetime()
    blockchain_error_code = fields.Char()
    blockchain_error_message = fields.Text()

    final_status = fields.Selection([
        ('draft', 'Draft'),
        ('collected', 'Collected'),
        ('evaluated', 'Evaluated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
        ('pending_onchain', 'Pending Onchain'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='draft', required=True, index=True)

    @api.model
    def _json_dump(self, value):
        if not value:
            return False
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['reasons_json'] = self._json_dump(vals.get('reasons_json'))
            vals['context_snapshot_json'] = self._json_dump(vals.get('context_snapshot_json'))
            vals['blockchain_payload_json'] = self._json_dump(vals.get('blockchain_payload_json'))
        return super().create(vals_list)

    def write(self, vals):
        if 'reasons_json' in vals:
            vals['reasons_json'] = self._json_dump(vals.get('reasons_json'))
        if 'context_snapshot_json' in vals:
            vals['context_snapshot_json'] = self._json_dump(vals.get('context_snapshot_json'))
        if 'blockchain_payload_json' in vals:
            vals['blockchain_payload_json'] = self._json_dump(vals.get('blockchain_payload_json'))
        return super().write(vals)

    def action_manual_approve(self):
        from ..services.override_handler import handle_manual_approve
        for rec in self:
            handle_manual_approve(self.env, rec)
        return True

    def action_manual_reject(self):
        from ..services.override_handler import handle_manual_reject
        for rec in self:
            handle_manual_reject(self.env, rec)
        return True

    def action_manual_escalate(self):
        from ..services.override_handler import handle_manual_escalate
        for rec in self:
            handle_manual_escalate(self.env, rec)
        return True

    def action_resync_blockchain(self):
        service = self.env['gdm.blockchain.reconciliation.service']
        for rec in self:
            service.resync_decision_blockchain_state(rec)
        return True

    def action_rerun_ai(self):
        from ..services.override_handler import handle_rerun
        for rec in self:
            handle_rerun(self.env, rec)
        return True
