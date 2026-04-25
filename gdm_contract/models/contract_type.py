# -*- coding: utf-8 -*-
# Copyright (C) 2019-2026 NeuroTech(<https://neurotech.kz>).
from odoo import models, fields


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'
    _order = 'name, id'

    active = fields.Boolean(default=True)
    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, index=True)
    is_purchase = fields.Boolean(string='Is purchase type')
    is_lease = fields.Boolean(string='Is lease type')
    is_supply = fields.Boolean(string='Is supply type')
    description = fields.Text(string='Description')
