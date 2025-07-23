import pytest
from algokit_utils import AlgorandClient, SigningAccount, CommonAppCallParams, LogicError

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient, FinalizeProposalArgs,
)
from smart_contracts.errors import std_errors as err
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
from tests.utils import ERROR_TO_REGEX

# TODO add tests for finalize on other statuses


def test_finalize_empty_proposal(
    proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
) -> None:
    xgov_registry_mock_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_app=proposal_client.app_id),
        params=CommonAppCallParams(sender=xgov_daemon.address)
    )

    assert_empty_proposal_global_state(
        proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )
    min_balance = algorand_client.account.get_information(proposal_client.app_address).min_balance.micro_algo
    assert_account_balance(algorand_client, proposal_client.app_address, min_balance)  # type: ignore

    # Test that finalize cannot be replayed from this state
    with pytest.raises(
        LookupError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=proposal_client.app_id),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_finalize_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    proposer: SigningAccount,
) -> None:
    locked_amount = draft_proposal_client.state.global_state.locked_amount
    proposer_balance = algorand_client.account.get_information(proposer.address).amount.micro_algo

    xgov_registry_mock_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_app=draft_proposal_client.app_id),
        params=CommonAppCallParams(sender=xgov_daemon.address)
    )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )

    min_balance = algorand_client.account.get_information(  # type: ignore
        draft_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, draft_proposal_client.app_address, min_balance  # type: ignore
    )
    assert_account_balance(
        algorand_client, proposer.address, proposer_balance + locked_amount  # type: ignore
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(
        LookupError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=draft_proposal_client.app_id),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_finalize_submitted_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    proposer: SigningAccount,
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=submitted_proposal_client.app_id),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_finalize_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=voting_proposal_client.app_id),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_finalize_approved_proposal(
    approved_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=approved_proposal_client.app_id),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_finalize_reviewed_proposal(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=reviewed_proposal_client.app_id),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_finalize_success_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members,
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

    min_balance = algorand_client.account.get_information(  # type: ignore
        rejected_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, rejected_proposal_client.app_address, min_balance  # type: ignore
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
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
    committee_members: list[SigningAccount],
) -> None:
    composer = blocked_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members,
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
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    min_balance = algorand_client.account.get_information(  # type: ignore
        blocked_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, blocked_proposal_client.app_address, min_balance  # type: ignore
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
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
    committee_members: list[SigningAccount],
) -> None:
    composer = funded_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members,
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
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    min_balance = algorand_client.account.get_information(  # type: ignore
        funded_proposal_client.app_address
    ).min_balance.micro_algo
    assert_account_balance(
        algorand_client, funded_proposal_client.app_address, min_balance  # type: ignore
    )

    # Test that finalize cannot be replayed from this state
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
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
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:-1],
        xgov_daemon,
    )
    composer.send()

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        rejected_proposal_client.send.finalize(
            args=FinalizeProposalArgs(proposal_app=rejected_proposal_client.app_id),
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_finalize_wrong_box_ref(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:-1],
        xgov_daemon,
        xgov_registry_mock_client.app_id,
    )
    composer.send()

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTERS_ASSIGNED]):
        xgov_registry_mock_client.send.finalize_proposal(
            args=FinalizeProposalArgs(proposal_app=rejected_proposal_client.app_id),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )
