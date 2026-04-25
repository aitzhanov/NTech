# -*- coding: utf-8 -*-
from odoo import models, fields, api


class GDMAIRule(models.Model):
    _name = 'gdm.ai.rule'
    _description = 'GDM AI Rule'
    _order = 'sequence asc, id asc'

    name = fields.Char(string='Rule Name', required=True)
    code = fields.Char(
        string='Rule Code', required=True, index=True,
        help='Unique technical code used in rules_engine. Example: missing_supplier'
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # Scope
    entity_model = fields.Selection([
        ('gdm.contract', 'Contract'),
        ('gdm.snt', 'SNT'),
        ('gdm.invoice', 'Invoice'),
    ], string='Entity Model', required=True, default='gdm.contract', index=True)

    # What to check
    check_type = fields.Selection([
        ('field_required', 'Field Required'),
        ('date_range', 'Date Range Valid'),
        ('amount_consistency', 'Amount Consistency'),
        ('custom', 'Custom (code only)'),
    ], string='Check Type', required=True, default='field_required')

    field_name = fields.Char(
        string='Field Name',
        help='Odoo field name to check. Example: supplier_id, date_start'
    )
    threshold = fields.Float(
        string='Threshold',
        default=1.0,
        help='Numeric threshold for amount consistency checks. Example: 1.2 = 120%'
    )

    # Outcome
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Level', required=True, default='high')

    decision_on_fail = fields.Selection([
        ('not_ready', 'Not Ready'),
        ('invalid', 'Invalid'),
        ('review', 'Review'),
    ], string='Decision on Fail', required=True, default='not_ready')

    required_action_on_fail = fields.Selection([
        ('none', 'None'),
        ('complete_master_data', 'Complete Master Data'),
        ('fix_dates', 'Fix Dates'),
        ('attach_documents', 'Attach Documents'),
        ('review_financials', 'Review Financials'),
        ('manual_review', 'Manual Review'),
        ('escalate', 'Escalate'),
    ], string='Required Action on Fail', required=True, default='complete_master_data')

    message = fields.Char(
        string='Failure Message', required=True,
        help='Human-readable message shown in decision reasons when rule fails.'
    )

    # Onchain trigger
    trigger_onchain_on_pass = fields.Boolean(
        string='Trigger Blockchain on Pass',
        default=False,
        help='If this rule passes and all other rules pass — trigger on-chain registration.'
    )

    description = fields.Text(string='Description')

    _sql_constraints = [
        ('code_model_unique', 'unique(code, entity_model)',
         'Rule code must be unique per entity model.'),
    ]

    @api.constrains('check_type', 'field_name')
    def _check_field_name(self):
        for rec in self:
            if rec.check_type == 'field_required' and not rec.field_name:
                raise models.ValidationError(
                    'Field Name is required for check type "Field Required".'
                )
