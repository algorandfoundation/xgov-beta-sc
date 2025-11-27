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
    PayGrantProposalArgs,
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_account_balance,
    assert_funded_proposal_global_state,
)

# TODO add tests for fund on other statuses


def test_fund_empty_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_draft_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=draft_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_submitted_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=submitted_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_voting_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=voting_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_approved_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    approved_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=approved_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_rejected_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=rejected_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_blocked_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    blocked_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=blocked_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_success(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    reviewed_proposal_client: ProposalClient,
) -> None:
    proposer_balance_before = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    xgov_registry_mock_client.send.pay_grant_proposal(
        args=PayGrantProposalArgs(proposal_app=reviewed_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_payor.address, static_fee=min_fee_times_3
        ),
    )

    voted_members = reviewed_proposal_client.state.global_state.voted_members
    assert_funded_proposal_global_state(
        reviewed_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=voted_members,
        approvals=DEFAULT_MEMBER_VOTES * voted_members,
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before,
    )


def test_fund_twice(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_payor: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    reviewed_proposal_client: ProposalClient,
) -> None:
    proposer_balance_before = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    xgov_registry_mock_client.send.pay_grant_proposal(
        args=PayGrantProposalArgs(proposal_app=reviewed_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_payor.address, static_fee=min_fee_times_3
        ),
    )

    voted_members = reviewed_proposal_client.state.global_state.voted_members
    assert_funded_proposal_global_state(
        reviewed_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=voted_members,
        approvals=DEFAULT_MEMBER_VOTES * voted_members,
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before,
    )

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_app=reviewed_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_not_registry(
    min_fee_times_3: AlgoAmount,
    xgov_payor: SigningAccount,
    reviewed_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        reviewed_proposal_client.send.fund(
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_3
            ),
        )
