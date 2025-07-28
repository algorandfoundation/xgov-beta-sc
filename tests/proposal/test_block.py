import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
    ReviewArgs,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_account_balance,
    assert_blocked_proposal_global_state,
)

# TODO add tests for block on other statuses


def test_block_empty_proposal(
    proposal_client: ProposalClient,
    xgov_council: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        draft_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_final_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        submitted_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        voting_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        rejected_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_reviewed_proposal(
    reviewed_proposal_client: ProposalClient,
    xgov_council: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        reviewed_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_success(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
) -> None:

    xgov_treasury_balance_before = algorand_client.account.get_information(
        xgov_registry_mock_client.app_address
    ).amount.micro_algo

    locked_amount = blocked_proposal_client.state.global_state.locked_amount

    assert_blocked_proposal_global_state(
        blocked_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, xGov Committee approves by plebiscite
    )

    assert_account_balance(
        algorand_client,
        xgov_registry_mock_client.app_address,
        xgov_treasury_balance_before + locked_amount,
    )


def test_block_twice(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    xgov_council: SigningAccount,
) -> None:

    xgov_treasury_balance_before = algorand_client.account.get_information(
        xgov_registry_mock_client.app_address
    ).amount.micro_algo

    locked_amount = blocked_proposal_client.state.global_state.locked_amount

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        blocked_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )

    assert_blocked_proposal_global_state(
        blocked_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  #  by default, the xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  #  by default, the xGov Committee approves by plebiscite
    )

    assert_account_balance(
        algorand_client,
        xgov_registry_mock_client.app_address,
        xgov_treasury_balance_before + locked_amount,
    )


def test_block_not_council(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    no_role_account: SigningAccount,
) -> None:

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        approved_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
