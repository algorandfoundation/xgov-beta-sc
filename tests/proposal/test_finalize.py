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
    FinalizeProposalArgs,
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_account_balance,
    assert_blocked_proposal_global_state,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_funded_proposal_global_state,
    assert_rejected_proposal_global_state,
    finalize_proposal,
    unassign_absentees,
)

# TODO add tests for finalize on other statuses


def assert_min_balance(
    algorand_client: AlgorandClient, proposal_client: ProposalClient
) -> None:
    """Assert that the proposal account has exactly the minimum balance."""
    min_balance = algorand_client.account.get_information(
        proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(algorand_client, proposal_client.app_address, min_balance)


def assert_finalize_replay_fails(
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_app_id: int,
    xgov_daemon: SigningAccount,
) -> None:
    """Assert that finalize cannot be replayed from this state."""
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        finalize_proposal(xgov_registry_mock_client, proposal_app_id, xgov_daemon)


def test_finalize_empty_proposal(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
) -> None:
    xgov_registry_mock_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_id=proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_3
        ),
    )

    assert_empty_proposal_global_state(
        proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )
    assert_min_balance(algorand_client, proposal_client)
    assert_finalize_replay_fails(
        xgov_registry_mock_client, proposal_client.app_id, xgov_daemon
    )


def test_finalize_draft_proposal(
    algorand_client: AlgorandClient,
    min_fee_times_4: AlgoAmount,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:
    locked_amount = draft_proposal_client.state.global_state.locked_amount
    proposer_balance = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    xgov_registry_mock_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_id=draft_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_4
        ),
    )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
        metadata_uploaded=True,
    )
    assert_min_balance(algorand_client, draft_proposal_client)
    assert_account_balance(
        algorand_client, proposer.address, proposer_balance + locked_amount
    )
    assert_finalize_replay_fails(
        xgov_registry_mock_client, draft_proposal_client.app_id, xgov_daemon
    )


@pytest.mark.parametrize(
    "proposal_fixture,fee_fixture",
    [
        ("submitted_proposal_client", "min_fee_times_2"),
        ("voting_proposal_client", "min_fee_times_2"),
        ("approved_proposal_client", "min_fee_times_3"),
        ("reviewed_proposal_client", "min_fee_times_3"),
    ],
)
def test_finalize_wrong_status_proposal(
    request: pytest.FixtureRequest,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_fixture: str,
    fee_fixture: str,
) -> None:
    proposal_client: ProposalClient = request.getfixturevalue(proposal_fixture)
    static_fee: AlgoAmount = request.getfixturevalue(fee_fixture)

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_id=proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=static_fee
            ),
        )


def test_finalize_success_rejected_proposal(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = xgov_registry_mock_client.new_group()
    unassign_absentees(composer, rejected_proposal_client.app_id, committee)
    composer.send()

    finalize_proposal(
        xgov_registry_mock_client, rejected_proposal_client.app_id, xgov_daemon
    )

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )
    assert_min_balance(algorand_client, rejected_proposal_client)
    assert_finalize_replay_fails(
        xgov_registry_mock_client, rejected_proposal_client.app_id, xgov_daemon
    )


def test_finalize_success_blocked_proposal(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    blocked_proposal_client: ProposalClient,
) -> None:
    finalize_proposal(
        xgov_registry_mock_client, blocked_proposal_client.app_id, xgov_daemon
    )

    voted_members = blocked_proposal_client.state.global_state.voted_members
    assert_blocked_proposal_global_state(
        blocked_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
        voted_members=voted_members,
        approvals=DEFAULT_MEMBER_VOTES * voted_members,
    )
    assert_min_balance(algorand_client, blocked_proposal_client)
    assert_finalize_replay_fails(
        xgov_registry_mock_client, blocked_proposal_client.app_id, xgov_daemon
    )


def test_finalize_success_funded_proposal(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    funded_proposal_client: ProposalClient,
) -> None:
    finalize_proposal(
        xgov_registry_mock_client, funded_proposal_client.app_id, xgov_daemon
    )

    voted_members = funded_proposal_client.state.global_state.voted_members
    assert_funded_proposal_global_state(
        funded_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
        voted_members=voted_members,
        approvals=DEFAULT_MEMBER_VOTES * voted_members,
    )
    assert_min_balance(algorand_client, funded_proposal_client)
    assert_finalize_replay_fails(
        xgov_registry_mock_client, funded_proposal_client.app_id, xgov_daemon
    )


def test_finalize_not_registry(
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = xgov_registry_mock_client.new_group()
    unassign_absentees(composer, rejected_proposal_client.app_id, committee[:-1])
    composer.send()

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rejected_proposal_client.send.finalize(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_finalize_wrong_box_ref(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = xgov_registry_mock_client.new_group()
    unassign_absentees(composer, rejected_proposal_client.app_id, committee[:-1])
    composer.send()

    with pytest.raises(LogicError, match=err.VOTERS_ASSIGNED):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_id=rejected_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_2
            ),
        )
