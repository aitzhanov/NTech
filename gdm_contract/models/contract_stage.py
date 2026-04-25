# -*- coding: utf-8 -*-
# Copyright (C) 2019-2026 NeuroTech(<https://neurotech.kz>).
from odoo import models, fields


class ContractStage(models.Model):
    _name = 'contract.stage'
    _description = 'Contract Stage'
    _order = 'sequence, id'

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=50)
    name = fields.Char(required=True, translate=True)
    code = fields.Char(string='Stage code')
    fold = fields.Boolean(string='Folded in Kanban')
