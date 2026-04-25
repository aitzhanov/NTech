# -*- coding: utf-8 -*-
import logging
from .audit_logger import audit_manual_override

_logger = logging.getLogger(__name__)


def handle_manual_approve(env, decision, reason=None):
    """
    User manually approves a decision.
    Re-routes to blockchain registration if the entity supports it.
    """
    decision.write({
        'manual_override': True,
        'override_reason': reason or 'manual_approved',
        'final_status': 'approved',
        'decision': 'manual_approved',
        'requires_manual_review': False,
    })
    audit_manual_override(env, decision, action='approve', reason=reason)

    # If entity is a contract and not yet on-chain — trigger blockchain
    if (
        decision.entity_model == 'gdm.contract'
        and decision.blockchain_sync_status in ('none', 'failed', 'resync_required')
    ):
        _logger.info(
            '[override_handler] manual approve triggers blockchain for decision=%s', decision.id
        )
        decision.write({
            'requires_onchain_action': True,
            'required_action': 'prepare_onchain',
        })
        orchestrator = env['gdm.ai.orchestrator.service']
        orchestrator._dispatch_blockchain(decision)


def handle_manual_reject(env, decision, reason=None):
    """
    User manually rejects a decision. No blockchain action.
    """
    decision.write({
        'manual_override': True,
        'override_reason': reason or 'manual_rejected',
        'final_status': 'rejected',
        'decision': 'manual_rejected',
        'requires_manual_review': False,
        'requires_onchain_action': False,
    })
    audit_manual_override(env, decision, action='reject', reason=reason)


def handle_manual_escalate(env, decision, reason=None):
    """
    User escalates a decision for further review.
    """
    decision.write({
        'manual_override': True,
        'override_reason': reason or 'escalated_by_user',
        'final_status': 'escalated',
        'decision': 'escalated',
        'requires_manual_review': True,
        'requires_onchain_action': False,
    })
    audit_manual_override(env, decision, action='escalate', reason=reason)


def handle_rerun(env, decision):
    """
    Re-runs the full orchestration pipeline for the entity.
    Used when data has been corrected and AI re-evaluation is needed.
    """
    _logger.info(
        '[override_handler] rerun orchestration for decision=%s model=%s res_id=%s',
        decision.id, decision.entity_model, decision.entity_res_id,
    )
    audit_manual_override(env, decision, action='rerun', reason='user triggered re-evaluation')
    orchestrator = env['gdm.ai.orchestrator.service']
    orchestrator.handle_event(decision.entity_model, decision.entity_res_id, 'manual_rerun')
