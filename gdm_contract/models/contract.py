# -*- coding: utf-8 -*-
# Copyright (C) 2019-2026 NeuroTech(<https://neurotech.kz>).
# gdm_contract/models/contract.py
import logging
import uuid
import calendar
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Contract(models.Model):
    _name = 'contract.contract'
    _description = 'Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    # ------------------------------------------------------------------ #
    # Fields                                                               #
    # ------------------------------------------------------------------ #

    uuid = fields.Char(string='UUID', readonly=True, store=True)
    active = fields.Boolean(default=True, tracking=True)
    name = fields.Char(string='Contract name', required=True, tracking=True)
    number = fields.Char(string='Contract number', index=True, tracking=True)

    stage_id = fields.Many2one(
        'contract.stage', string='Stage',
        ondelete='restrict', tracking=True,
    )
    stage_sequence = fields.Integer(
        string='Stage Sequence',
        compute='_compute_stage_sequence', store=True,
    )
    contract_type_id = fields.Many2one(
        'contract.type', string='Contract Type',
        ondelete='restrict', index=True, tracking=True,
    )

    # Parties
    operator_comp_id = fields.Many2one(
        'res.company', string='Operator Company',
        required=True, default=lambda self: self.env.company.id,
        tracking=True,
    )
    operator_comp_ceo_id = fields.Many2one('res.users', string='CEO', tracking=True)
    operator_comp_executor_id = fields.Many2one('res.users', string='Executor')

    supplier_id = fields.Many2one(
        'res.partner', string='Supplier',
        ondelete='restrict', index=True, tracking=True,
    )

    # Dates & Financials
    date = fields.Date(string='Contract date', default=fields.Date.today, tracking=True)
    date_start = fields.Date(string='Start date', tracking=True)
    date_end = fields.Date(string='End date', tracking=True)

    volume_total = fields.Float(string='Total volume')
        # AI quarterly request generation
    ai_generated = fields.Boolean(string='AI Generated', default=False, tracking=True)
    volume_locked = fields.Boolean(string='Volume Locked', default=False, tracking=True)

    allocation_quarter = fields.Selection(
        [('1', 'Q1'), ('2', 'Q2'), ('3', 'Q3'), ('4', 'Q4')],
        string='Allocation Quarter',
        tracking=True,
    )
    allocation_year = fields.Integer(string='Allocation Year', tracking=True)

    source_contract_id = fields.Many2one(
        'contract.contract',
        string='Source Approved Contract',
        readonly=True,
        tracking=True,
    )

    generation_reason = fields.Text(
        string='Generation Reason',
        readonly=True,
    )

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id.id,
    )
    amount_total = fields.Monetary(string='Total amount', currency_field='currency_id')

    note = fields.Html(string='Internal notes')

    # Blockchain
    blockchain_tx = fields.Char(string='Blockchain TX')
    blockchain_status = fields.Char(string='Blockchain Status')
    onchain_version = fields.Integer(string='On-chain Version')

    _sql_constraints = [
        (
            'contract_unique_number_operator_supplier',
            'unique(number, operator_comp_id, supplier_id)',
            'Contract with this number already exists for this operator and supplier.',
        ),
    ]

    # ------------------------------------------------------------------ #
    # Compute                                                              #
    # ------------------------------------------------------------------ #

    @api.depends('stage_id.sequence')
    def _compute_stage_sequence(self):
        for rec in self:
            rec.stage_sequence = rec.stage_id.sequence if rec.stage_id else 0

    # ------------------------------------------------------------------ #
    # UUID generation                                                      #
    # ------------------------------------------------------------------ #

    def _generate_uuid(self):
        self.ensure_one()
        unique_parts = [
            self.number or '',
            str(self.operator_comp_id.id) if self.operator_comp_id else '',
            str(self.supplier_id.id) if self.supplier_id else '',
            str(self.date) if self.date else '',
        ]
        unique_string = ''.join(unique_parts)
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, 'energytech.kz')
        return str(uuid.uuid5(namespace, unique_string))

    # ------------------------------------------------------------------ #
    # Sequence                                                             #
    # ------------------------------------------------------------------ #

    @api.model
    def _format_seq(self, n):
        return f'CTR{int(n):08d}'

    @api.model
    def _get_next_sequence(self):
        seq = self.env['ir.sequence'].sudo().next_by_code('contract.contract')
        if seq:
            return seq
        count = self.sudo().search_count([])
        return self._format_seq(count + 1)

    # ------------------------------------------------------------------ #
    # ORM overrides                                                        #
    # ------------------------------------------------------------------ #

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('number'):
                vals['number'] = self._get_next_sequence()
        records = super().create(vals_list)
        for rec in records:
            rec.with_context(skip_uuid_update=True).write({
                'uuid': rec._generate_uuid(),
                'stage_id': self.env['contract.stage'].search(
                    [('sequence', '=', 1)], limit=1
                ).id or False,
            })
        return records

    def write(self, vals):
        if self.env.context.get('skip_uuid_update'):
            return super().write(vals)
        res = super().write(vals)
        try:
            for rec in self:
                rec.with_context(skip_uuid_update=True).write(
                    {'uuid': rec._generate_uuid()}
                )
        except Exception:
            _logger.exception('[contract] uuid refresh failed ids=%s', self.ids)
        return res

       
    # ------------------------------------------------------------------ #
    # AI quarterly generation                                              #
    # ------------------------------------------------------------------ #

    def _get_next_quarter_period(self):
        self.ensure_one()

        base = self.date_end or self.date_start or self.date or fields.Date.today()
        if isinstance(base, str):
            base = fields.Date.from_string(base)

        current_quarter = ((base.month - 1) // 3) + 1
        next_quarter = current_quarter + 1
        year = base.year

        if next_quarter > 4:
            next_quarter = 1
            year += 1

        start_month = (next_quarter - 1) * 3 + 1
        end_month = start_month + 2
        last_day = calendar.monthrange(year, end_month)[1]

        date_start = date(year, start_month, 1)
        date_end = date(year, end_month, last_day)

        return str(next_quarter), year, date_start, date_end

    def action_generate_next_quarter_request(self):
        for rec in self:
            if not rec.volume_total:
                raise UserError(_('Cannot generate request: previous approved volume is empty.'))

            quarter, year, date_start, date_end = rec._get_next_quarter_period()

            existing = self.search([
                ('source_contract_id', '=', rec.id),
                ('allocation_quarter', '=', quarter),
                ('allocation_year', '=', year),
            ], limit=1)

            if existing:
                return existing.action_open_contract()

            new_contract = self.create({
                'name': 'AI Generated LPG Request Q%s %s' % (quarter, year),
                'contract_type_id': rec.contract_type_id.id if rec.contract_type_id else False,
                'operator_comp_id': rec.operator_comp_id.id if rec.operator_comp_id else self.env.company.id,
                'operator_comp_ceo_id': rec.operator_comp_ceo_id.id if rec.operator_comp_ceo_id else False,
                'operator_comp_executor_id': rec.operator_comp_executor_id.id if rec.operator_comp_executor_id else False,
                'supplier_id': rec.supplier_id.id if rec.supplier_id else False,
                'date': fields.Date.today(),
                'date_start': date_start,
                'date_end': date_end,
                'volume_total': rec.volume_total,
                'uom_id': rec.uom_id.id if rec.uom_id else False,
                'currency_id': rec.currency_id.id if rec.currency_id else self.env.company.currency_id.id,
                'amount_total': rec.amount_total,
                'ai_generated': True,
                'volume_locked': True,
                'allocation_quarter': quarter,
                'allocation_year': year,
                'source_contract_id': rec.id,
                'generation_reason': (
                    'Generated automatically from previous approved contract %s. '
                    'Approved volume was preserved: %s.'
                ) % (rec.number or rec.name, rec.volume_total),
                'note': (
                    '<p><b>AI-generated quarterly request.</b></p>'
                    '<p>Volume was copied from previous approved contract and locked '
                    'to reduce manual manipulation and corruption risk.</p>'
                ),
            })

            return new_contract.action_open_contract()

    # ------------------------------------------------------------------ #
    # Blockchain helpers                                                   #
    # ------------------------------------------------------------------ #

    def _contract_key(self):
        """
        Normalized contract_id for Solana PDA seed.
        UUID without dashes = 32 hex chars = exactly 32 bytes.
        Must match _normalize_contract_id() in gdm_solana_bridge.
        """
        self.ensure_one()
        raw = (self.uuid or self.number or '').strip()
        return raw.replace('-', '')

    def _get_bridge_base_url(self):
        icp = self.env['ir.config_parameter'].sudo()
        candidates = [
            icp.get_param('gdm.solana_bridge_url'),
            icp.get_param('solana_bridge_url'),
            'http://172.17.0.1:8181',
            'http://gdm-solana-bridge:8080',
            'http://host.docker.internal:8181',
            'http://localhost:8181',
        ]
        urls = [u.strip().rstrip('/') for u in candidates if u and u.strip()]
        preferred = 'http://172.17.0.1:8181'
        if preferred in urls:
            if icp.get_param('gdm.solana_bridge_url') != preferred:
                try:
                    icp.set_param('gdm.solana_bridge_url', preferred)
                except Exception:
                    pass
            urls = [preferred] + [u for u in urls if u != preferred]
        return urls

    def _bridge_request(self, method, path, payload=None):
        try:
            import requests as _requests
        except ImportError as exc:
            raise UserError(_('Python package requests is not available: %s') % exc)

        errors = []
        for base_url in self._get_bridge_base_url():
            url = '%s%s' % (base_url, path)
            try:
                if method == 'POST':
                    resp = _requests.post(url, json=payload, timeout=10)
                else:
                    resp = _requests.get(url, timeout=10)
                resp.raise_for_status()
                try:
                    return resp.json()
                except Exception as exc:
                    raise UserError(_('Bridge returned invalid JSON from %s: %s') % (url, exc))
            except Exception as exc:
                errors.append('%s -> %s' % (url, exc))

        preferred = [e for e in errors if '172.17.0.1:8181' in e]
        if preferred:
            raise UserError(preferred[0])
        raise UserError(_('Bridge unavailable. Tried:\n%s') % '\n'.join(errors))

    # ------------------------------------------------------------------ #
    # Actions                                                              #
    # ------------------------------------------------------------------ #

    def action_ai_blockchain_approve(self):
        for rec in self:
            try:
                contract_key = rec._contract_key()
                if not contract_key:
                    raise UserError(_('Contract has no UUID or number — cannot register on blockchain.'))

                try:
                    existing = rec._bridge_request('GET', '/contract/%s' % contract_key)
                except Exception as exc:
                    if '404 Client Error' in str(exc):
                        existing = {'found': False}
                    else:
                        raise

                if existing.get('found'):
                    rec.onchain_version = existing.get('version') or 0
                    rec.blockchain_status = 'skipped'
                    if not rec.blockchain_tx:
                        rec.blockchain_tx = existing.get('contract_pda') or False
                    continue

                data = rec._bridge_request(
                    'POST',
                    '/tx/register_and_track',
                    {'type': 'register_contract', 'contract_id': contract_key, 'version': 1},
                )
                tx = data.get('tx') or {}
                tx_status = data.get('tx_status') or {}
                state = data.get('onchain_state') or {}

                rec.blockchain_tx = tx.get('signature') or False
                rec.blockchain_status = (
                    tx_status.get('status') or tx_status.get('confirmation_status') or False
                )
                rec.onchain_version = state.get('version') or 0

            except Exception as exc:
                rec.blockchain_status = 'error'
                raise UserError(str(exc))

    def action_verify_onchain(self):
        for rec in self:
            try:
                contract_key = rec._contract_key()
                data = rec._bridge_request('GET', '/contract/%s' % contract_key)
                rec.onchain_version = data.get('version') or 0
                rec.blockchain_status = 'verified' if data.get('found') else 'not_found'
                if data.get('found') and not rec.blockchain_tx:
                    rec.blockchain_tx = data.get('contract_pda') or rec.blockchain_tx
            except Exception as exc:
                rec.blockchain_status = 'error'
                raise UserError(str(exc))

    def action_open_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'contract.contract',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
