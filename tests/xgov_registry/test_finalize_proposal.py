import pytest
from algokit_utils import AlgoAmount, CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    FinalizeProposalArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal import enums as enm
from tests.common import DEFAULT_COMMITTEE_MEMBERS, DEFAULT_MEMBER_VOTES
from tests.proposal.common import (
    REQUESTED_AMOUNT,
    assert_blocked_proposal_global_state,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_funded_proposal_global_state,
    assert_rejected_proposal_global_state,
)


def test_finalize_funded_proposal_success(
    min_fee_times_3: AlgoAmount,
    xgov_daemon: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    funded_unassigned_voters_proposal_client: ProposalClient,
) -> None:
    proposer_address = (
        funded_unassigned_voters_proposal_client.state.global_state.proposer
    )
    pending_proposals_before = xgov_registry_client.state.global_state.pending_proposals

    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(
            proposal_id=funded_unassigned_voters_proposal_client.app_id
        ),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_3
        ),
    )

    assert_funded_proposal_global_state(
        funded_unassigned_voters_proposal_client,
        proposer_address,
        xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        voted_members=DEFAULT_COMMITTEE_MEMBERS,
        approvals=DEFAULT_MEMBER_VOTES * DEFAULT_COMMITTEE_MEMBERS,
    )

    pending_proposals_after = xgov_registry_client.state.global_state.pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_empty_proposal_not_xgov_daemon(
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_id=proposal_client.app_id),
            params=CommonAppCallParams(
                sender=no_role_account.address, static_fee=min_fee_times_3
            ),
        )


def test_finalize_empty_proposal_xgov_daemon(
    min_fee_times_3: AlgoAmount,
    xgov_daemon: SigningAccount,
    proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient
) -> None:
    proposer_address = proposal_client.state.global_state.proposer
    pending_proposals_before = xgov_registry_client.state.global_state.pending_proposals

    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_id=proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_3
        ),
    )

    assert_empty_proposal_global_state(
        proposal_client,
        proposer_address=proposer_address,
        registry_app_id=xgov_registry_client.app_id,
        finalized=True,
    )

    pending_proposals_after = xgov_registry_client.state.global_state.pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_draft_proposal_not_xgov_daemon(
    min_fee_times_4: AlgoAmount,
    no_role_account: SigningAccount,
    draft_proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_id=draft_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=no_role_account.address, static_fee=min_fee_times_4
            ),
        )


def test_finalize_draft_proposal_xgov_daemon(
    min_fee_times_4: AlgoAmount,
    xgov_daemon: SigningAccount,
    draft_proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient
) -> None:
    proposer_address = draft_proposal_client.state.global_state.proposer
    pending_proposals_before = xgov_registry_client.state.global_state.pending_proposals

    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_id=draft_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_4
        ),
    )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        proposer_address=proposer_address,
        registry_app_id=xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
    )

    pending_proposals_after = xgov_registry_client.state.global_state.pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_rejected_proposal_not_xgov_daemon(
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    rejected_unassigned_voters_proposal_client: ProposalClient,
) -> None:
    proposer_address = (
        rejected_unassigned_voters_proposal_client.state.global_state.proposer
    )
    pending_proposals_before = xgov_registry_client.state.global_state.pending_proposals

    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(
            proposal_id=rejected_unassigned_voters_proposal_client.app_id
        ),
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_3
        ),
    )

    assert_rejected_proposal_global_state(
        rejected_unassigned_voters_proposal_client,
        proposer_address=proposer_address,
        registry_app_id=xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
    )

    pending_proposals_after = xgov_registry_client.state.global_state.pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_funded_proposal_not_xgov_daemon(
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    funded_unassigned_voters_proposal_client: ProposalClient,
) -> None:
    proposer_address = (
        funded_unassigned_voters_proposal_client.state.global_state.proposer
    )
    pending_proposals_before = xgov_registry_client.state.global_state.pending_proposals

    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(
            proposal_id=funded_unassigned_voters_proposal_client.app_id
        ),
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_3
        ),
    )

    assert_funded_proposal_global_state(
        funded_unassigned_voters_proposal_client,
        proposer_address,
        xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        voted_members=DEFAULT_COMMITTEE_MEMBERS,
        approvals=DEFAULT_MEMBER_VOTES * DEFAULT_COMMITTEE_MEMBERS,
    )

    pending_proposals_after = xgov_registry_client.state.global_state.pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_blocked_proposal_not_xgov_daemon(
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    blocked_unassigned_voters_proposal_client: ProposalClient,
) -> None:
    proposer_address = (
        blocked_unassigned_voters_proposal_client.state.global_state.proposer
    )
    pending_proposals_before = xgov_registry_client.state.global_state.pending_proposals

    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(
            proposal_id=blocked_unassigned_voters_proposal_client.app_id
        ),
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_3
        ),
    )

    assert_blocked_proposal_global_state(
        blocked_unassigned_voters_proposal_client,
        proposer_address,
        xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        voted_members=DEFAULT_COMMITTEE_MEMBERS,
        approvals=DEFAULT_MEMBER_VOTES * DEFAULT_COMMITTEE_MEMBERS,
    )

    pending_proposals_after = xgov_registry_client.state.global_state.pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


# TODO: Reintroduce the alternative registry client
# def test_finalize_invalid_proposal(
#     min_fee_times_3: AlgoAmount,
#     xgov_daemon: SigningAccount,
#     xgov_registry_client: XGovRegistryClient,
#     funded_unassigned_voters_proposal_client: ProposalClient,
# ) -> None:
#     with pytest.raises(LogicError, match=err.INVALID_PROPOSAL):
#         xgov_registry_client.send.finalize_proposal(
#             args=FinalizeProposalArgs(proposal_id=funded_unassigned_voters_proposal_client.app_id),
#             params=CommonAppCallParams(sender=xgov_daemon.address, static_fee=min_fee_times_3)
#         )
