# -*- coding: utf-8 -*-
import hashlib
import json


def build_document_hash(document):
    if document._name == 'gdm.snt':
        payload = {
            'model': document._name,
            'id': document.id,
            'number': document.accounting_number or document.name,
            'date': str(document.shipping_date or ''),
            'contract_id': document.contract_id.id if document.contract_id else None,
            'volume': sum(document.line_ids.mapped('quantity')) if hasattr(document.line_ids, 'mapped') else 0,
            'line_count': len(document.line_ids),
        }
    else:
        payload = {
            'model': document._name,
            'id': document.id,
            'number': document.esf_reg_number or document.esf_local_number or document.name,
            'date': str(document.esf_date or document.turnover_date or ''),
            'contract_id': document.contract_id.id if document.contract_id else None,
            'amount_total': document.amount_total or 0.0,
            'currency_id': document.currency_id.id if document.currency_id else None,
            'line_count': len(document.line_ids),
            'snt_id': document.snt_id.id if getattr(document, 'snt_id', False) else None,
        }

    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
