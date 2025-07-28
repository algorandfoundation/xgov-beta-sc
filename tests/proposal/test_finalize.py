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
    unassign_voters,
)

# TODO add tests for finalize on other statuses


def test_finalize_empty_proposal(
    proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    min_fee_times_3: AlgoAmount,
) -> None:
    xgov_registry_mock_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_app=proposal_client.app_id),
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
    min_balance = algorand_client.account.get_information(
        proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(algorand_client, proposal_client.app_address, min_balance)

    # Test that finalize cannot be replayed from this state
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_3
            ),
        )


def test_finalize_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    proposer: SigningAccount,
    min_fee_times_4: AlgoAmount,
) -> None:
    locked_amount = draft_proposal_client.state.global_state.locked_amount
    proposer_balance = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    xgov_registry_mock_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_app=draft_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_4
        ),
    )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )

    min_balance = algorand_client.account.get_information(
        draft_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, draft_proposal_client.app_address, min_balance
    )
    assert_account_balance(
        algorand_client, proposer.address, proposer_balance + locked_amount
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=draft_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_4
            ),
        )


def test_finalize_submitted_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    proposer: SigningAccount,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=submitted_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_2
            ),
        )


def test_finalize_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=voting_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_2
            ),
        )


def test_finalize_approved_proposal(
    approved_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
    min_fee_times_3: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=approved_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_3
            ),
        )


def test_finalize_reviewed_proposal(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
    min_fee_times_3: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=reviewed_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_3
            ),
        )


def test_finalize_success_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.send()

    finalize_proposal(
        xgov_registry_mock_client,
        rejected_proposal_client.app_id,
        xgov_daemon,
    )

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )

    min_balance = algorand_client.account.get_information(
        rejected_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, rejected_proposal_client.app_address, min_balance
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        finalize_proposal(
            xgov_registry_mock_client,
            rejected_proposal_client.app_id,
            xgov_daemon,
        )


def test_finalize_success_blocked_proposal(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
) -> None:
    composer = blocked_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.send()

    finalize_proposal(
        xgov_registry_mock_client,
        blocked_proposal_client.app_id,
        xgov_daemon,
    )

    assert_blocked_proposal_global_state(
        blocked_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by plebiscite
    )

    min_balance = algorand_client.account.get_information(
        blocked_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, blocked_proposal_client.app_address, min_balance
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        finalize_proposal(
            xgov_registry_mock_client,
            blocked_proposal_client.app_id,
            xgov_daemon,
        )


def test_finalize_success_funded_proposal(
    funded_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
) -> None:
    composer = funded_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.send()

    finalize_proposal(
        xgov_registry_mock_client,
        funded_proposal_client.app_id,
        xgov_daemon,
    )

    assert_funded_proposal_global_state(
        funded_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by plebiscite
    )

    min_balance = algorand_client.account.get_information(
        funded_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, funded_proposal_client.app_address, min_balance
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        finalize_proposal(
            xgov_registry_mock_client,
            funded_proposal_client.app_id,
            xgov_daemon,
        )


def test_finalize_not_registry(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:-1],
        xgov_daemon,
    )
    composer.send()

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rejected_proposal_client.send.finalize(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_finalize_wrong_box_ref(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:-1],
        xgov_daemon,
    )
    composer.send()

    with pytest.raises(LogicError, match=err.VOTERS_ASSIGNED):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=rejected_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_2
            ),
        )
