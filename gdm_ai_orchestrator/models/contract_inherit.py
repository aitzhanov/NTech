# -*- coding: utf-8 -*-
from odoo import models, api


class ContractAI(models.Model):
    _inherit = 'contract.contract'

    def _ai_trigger_event(self, event):
        if self.env.context.get('skip_ai_trigger'):
            return
        service = self.env['gdm.ai.orchestrator.service']
        for rec in self:
            service.handle_event('contract.contract', rec.id, event)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_ai_trigger'):
            for rec in records:
                rec._ai_trigger_event('create')
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_ai_trigger'):
            self._ai_trigger_event('write')
        return res