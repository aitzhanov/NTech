# -*- coding: utf-8 -*-
from odoo import models, api


class GDMInvoiceAI(models.Model):
    _inherit = 'gdm.invoice'

    def _ai_trigger_event(self, event):
        service = self.env['gdm.ai.orchestrator.service']
        for rec in self:
            service.handle_event('gdm.invoice', rec.id, event)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._ai_trigger_event('create')
        return records

    def write(self, vals):
        res = super().write(vals)
        self._ai_trigger_event('write')
        return res
