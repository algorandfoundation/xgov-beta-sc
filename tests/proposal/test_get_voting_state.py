from algokit_utils import CommonAppCallParams, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
)

from .common import get_proposal_values_from_registry


def test_get_voting_state_empty_proposal(
    no_role_account: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    result = proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    assert result.quorum_voters == 0
    assert result.weighted_quorum_votes == 0
    assert result.total_voters == 0
    assert result.total_approvals == 0
    assert result.total_rejections == 0
    assert result.total_nulls == 0
    assert not result.quorum_reached
    assert not result.weighted_quorum_reached
    assert not result.majority_approved
    assert not result.plebiscite


def test_get_voting_state_draft_proposal(
    no_role_account: SigningAccount,
    draft_proposal_client: ProposalClient,
) -> None:
    result = draft_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(draft_proposal_client)

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == 0
    assert result.total_approvals == 0
    assert result.total_rejections == 0
    assert result.total_nulls == 0
    assert not result.quorum_reached
    assert not result.weighted_quorum_reached
    assert not result.majority_approved
    assert not result.plebiscite


def test_get_voting_state_submitted_proposal(
    no_role_account: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> None:
    result = submitted_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(submitted_proposal_client)

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == 0
    assert result.total_approvals == 0
    assert result.total_rejections == 0
    assert result.total_nulls == 0
    assert not result.quorum_reached
    assert not result.weighted_quorum_reached
    assert not result.majority_approved
    assert not result.plebiscite


def test_get_voting_state_voting_proposal(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
) -> None:
    result = voting_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(voting_proposal_client)

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == 0
    assert result.total_approvals == 0
    assert result.total_rejections == 0
    assert result.total_nulls == 0
    assert not result.quorum_reached
    assert not result.weighted_quorum_reached
    assert not result.majority_approved
    assert not result.plebiscite


def test_get_voting_state_rejected_proposal(
    no_role_account: SigningAccount,
    rejected_proposal_client: ProposalClient,
) -> None:
    result = rejected_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(rejected_proposal_client)

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == 0
    assert result.total_approvals == 0
    assert result.total_rejections == 0
    assert result.total_nulls == 0
    assert not result.quorum_reached
    assert not result.weighted_quorum_reached
    assert not result.majority_approved
    assert not result.plebiscite


def test_get_voting_state_approved_proposal(
    no_role_account: SigningAccount,
    approved_proposal_client: ProposalClient,
) -> None:
    result = approved_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(approved_proposal_client)
    proposal_state = approved_proposal_client.state.global_state

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == proposal_state.voted_members
    assert result.total_approvals == proposal_state.approvals
    assert result.total_rejections == proposal_state.rejections
    assert result.total_nulls == proposal_state.nulls
    assert result.quorum_reached
    assert result.weighted_quorum_reached
    assert result.majority_approved
    if proposal_state.voters_count == proposal_values.members_quorum:
        assert result.plebiscite
    else:
        assert not result.plebiscite


def test_get_voting_state_reviewed_proposal(
    no_role_account: SigningAccount,
    reviewed_proposal_client: ProposalClient,
) -> None:
    result = reviewed_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(
        reviewed_proposal_client)
    proposal_state = reviewed_proposal_client.state.global_state

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == proposal_state.voted_members
    assert result.total_approvals == proposal_state.approvals
    assert result.total_rejections == proposal_state.rejections
    assert result.total_nulls == proposal_state.nulls
    assert result.quorum_reached
    assert result.weighted_quorum_reached
    assert result.majority_approved
    if proposal_state.voters_count == proposal_values.members_quorum:
        assert result.plebiscite
    else:
        assert not result.plebiscite


def test_get_voting_state_blocked_proposal(
    no_role_account: SigningAccount,
    blocked_proposal_client: ProposalClient,
) -> None:
    result = blocked_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(
        blocked_proposal_client)
    proposal_state = blocked_proposal_client.state.global_state

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == proposal_state.voted_members
    assert result.total_approvals == proposal_state.approvals
    assert result.total_rejections == proposal_state.rejections
    assert result.total_nulls == proposal_state.nulls
    assert result.quorum_reached
    assert result.weighted_quorum_reached
    assert result.majority_approved
    if proposal_state.voters_count == proposal_values.members_quorum:
        assert result.plebiscite
    else:
        assert not result.plebiscite


def test_get_voting_state_funded_proposal(
    no_role_account: SigningAccount,
    funded_proposal_client: ProposalClient,
) -> None:
    result = funded_proposal_client.send.get_voting_state(
        params=CommonAppCallParams(sender=no_role_account.address)
    ).abi_return

    proposal_values = get_proposal_values_from_registry(
        funded_proposal_client)
    proposal_state = funded_proposal_client.state.global_state

    assert result.quorum_voters == proposal_values.members_quorum
    assert result.weighted_quorum_votes == proposal_values.votes_quorum
    assert result.total_voters == proposal_state.voted_members
    assert result.total_approvals == proposal_state.approvals
    assert result.total_rejections == proposal_state.rejections
    assert result.total_nulls == proposal_state.nulls
    assert result.quorum_reached
    assert result.weighted_quorum_reached
    assert result.majority_approved
    if proposal_state.voters_count == proposal_values.members_quorum:
        assert result.plebiscite
    else:
        assert not result.plebiscite
