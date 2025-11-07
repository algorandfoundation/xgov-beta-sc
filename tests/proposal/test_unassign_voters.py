import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_blocked_proposal_global_state,
    assert_final_proposal_global_state,
    assert_funded_proposal_global_state,
    assert_rejected_proposal_global_state,
    assign_voters,
    unassign_voters,
)
from tests.utils import time_warp

# TODO add tests for unassign on other statuses


def test_unassign_empty_proposal(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        composer = proposal_client.new_group()
        unassign_voters(
            composer,
            committee,
            xgov_daemon,
        )
        composer.send()


def test_unassign_unauthorized(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        composer = submitted_proposal_client.new_group()
        unassign_voters(
            composer,
            [],
            proposer,
        )
        composer.send()


def test_unassign_no_voters(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        [],
        xgov_daemon,
    )
    composer.send()

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign_one_voter(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:1],
        xgov_daemon,
    )
    composer.send()

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=DEFAULT_MEMBER_VOTES * (len(committee) - 1),
        voters_count=len(committee) - 1,
    )


def test_unassign_rejected_not_daemon(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:1],
        no_role_account,
    )
    composer.send()

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=DEFAULT_MEMBER_VOTES * (len(committee) - 1),
        voters_count=len(committee) - 1,
    )


def test_unassign_funded_not_daemon(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    funded_proposal_client: ProposalClient,
) -> None:
    voters_count = funded_proposal_client.state.global_state.voters_count
    assigned_votes = funded_proposal_client.state.global_state.assigned_votes
    composer = funded_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:1],
        no_role_account,
    )
    composer.send()

    assert_funded_proposal_global_state(
        funded_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by plebiscite
        voters_count=0 if not voters_count else voters_count - 1,
        assigned_votes=(
            0 if not assigned_votes else assigned_votes - DEFAULT_MEMBER_VOTES
        ),
    )


def test_unassign_blocked_not_daemon(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    blocked_proposal_client: ProposalClient,
) -> None:
    voters_count = blocked_proposal_client.state.global_state.voters_count
    assigned_votes = blocked_proposal_client.state.global_state.assigned_votes
    composer = blocked_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:1],
        no_role_account,
    )
    composer.send()

    assert_blocked_proposal_global_state(
        blocked_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by plebiscite
        voters_count=0 if not voters_count else voters_count - 1,
        assigned_votes=(
            0 if not assigned_votes else assigned_votes - DEFAULT_MEMBER_VOTES
        ),
    )


def test_unassign_all_voters(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.send()

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=0,
        voters_count=0,
    )


def test_unassign_not_same_app(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
    alternative_submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee=committee,
    )
    composer.send()

    composer = alternative_submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee=committee,
    )
    composer.send()

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = max(
        submitted_proposal_client.state.global_state.vote_open_ts,
        alternative_submitted_proposal_client.state.global_state.vote_open_ts,
    )
    time_warp(vote_open_ts + voting_duration + 1)

    submitted_proposal_client.send.scrutiny(
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_2
        )
    )
    alternative_submitted_proposal_client.send.scrutiny(
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_2
        )
    )

    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.composer().build()

    alternative_composer = alternative_submitted_proposal_client.new_group()
    unassign_voters(
        alternative_composer,
        committee,
        xgov_daemon,
    )
    alternative_composer.composer().build()

    alternative_composer.composer()._atc.txn_list[
        0
    ] = composer.composer()._atc.txn_list[0]
    alternative_composer.composer()._atc.method_dict[
        0
    ] = composer.composer()._atc.method_dict[0]

    with pytest.raises(LogicError, match=err.WRONG_APP_ID):
        alternative_composer.send()


def test_unassign_not_same_method(
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    composer.get_state(params=CommonAppCallParams(sender=xgov_daemon.address))
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )

    with pytest.raises(LogicError, match=err.WRONG_METHOD_CALL):
        composer.send()


def test_unassign_not_same_method_2(
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.get_state(params=CommonAppCallParams(sender=xgov_daemon.address))

    with pytest.raises(LogicError, match=err.WRONG_METHOD_CALL):
        composer.send()


def test_unassign_one_call_not_xgov_daemon(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:-1],
        xgov_daemon,
    )
    unassign_voters(
        composer,
        committee[-1:],
        proposer,
    )
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        composer.send()


def test_unassign_final_proposal(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee=committee[:1],
    )
    composer.send()

    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:1],
        xgov_daemon,
    )
    composer.send()

    assert_final_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
