# -*- coding: utf-8 -*-
import uuid
from datetime import datetime


def build_payload(decision, action, entity_type='contract', data=None):
    data = data or {}

    return {
        'request_id': str(uuid.uuid4()),
        'decision_id': decision.id,
        'entity_type': entity_type,
        'entity_id': str(decision.entity_res_id),
        'action': action,
        'data': data,
        'metadata': {
            'version': 1,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'gdm_ai_orchestrator'
        }
    }
