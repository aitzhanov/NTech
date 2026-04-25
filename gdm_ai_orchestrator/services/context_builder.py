# -*- coding: utf-8 -*-


def build_contract_context(env, contract):
    invoices = env['account.move'].search([
        ('contract_id', '=', contract.id)
    ]) if 'contract_id' in env['account.move']._fields else env['account.move'].browse([])

    total_invoice_amount = sum(invoices.mapped('amount_total')) if invoices else 0.0

    readiness_flags = {
        'has_supplier': bool(contract.supplier_id),
        'has_dates': bool(contract.date_start and contract.date_end),
        'has_amount': bool(contract.amount_total),
        'has_volume': bool(contract.volume_total),
    }

    consistency_flags = {
        'date_valid': (
            not contract.date_start
            or not contract.date_end
            or contract.date_start <= contract.date_end
        ),
        'amount_vs_invoice': (
            not contract.amount_total
            or total_invoice_amount <= contract.amount_total * 1.2
        ),
    }

    return {
        'contract': {
            'id': contract.id,
            'number': contract.number,
            'supplier_id': contract.supplier_id.id if contract.supplier_id else False,
            'date_start': str(contract.date_start) if contract.date_start else False,
            'date_end': str(contract.date_end) if contract.date_end else False,
            'amount_total': contract.amount_total,
            'volume_total': contract.volume_total,
            'currency_id': contract.currency_id.id if contract.currency_id else False,
            'stage_id': contract.stage_id.id if contract.stage_id else False,
            'contract_type_id': contract.contract_type_id.id if contract.contract_type_id else False,
        },
        'invoice': {
            'count': len(invoices),
            'total_amount': total_invoice_amount,
        },
        'flags': {
            'readiness': readiness_flags,
            'consistency': consistency_flags,
        },
    }
