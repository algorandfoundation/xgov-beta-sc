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
    FundArgs,
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
    proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )


def test_fund_draft_proposal(
    draft_proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=draft_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )


def test_fund_submitted_proposal(
    submitted_proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=submitted_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )


def test_fund_voting_proposal(
    voting_proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=voting_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )


def test_fund_approved_proposal(
    approved_proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=approved_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )


def test_fund_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=rejected_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )


def test_fund_blocked_proposal(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    min_fee_times_2: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=blocked_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )


def test_fund_success(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee: list[CommitteeMember],
    min_fee_times_3: AlgoAmount,
) -> None:
    proposer_balance_before = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo
    locked_amount = reviewed_proposal_client.state.global_state.locked_amount

    xgov_registry_mock_client.send.fund(
        args=FundArgs(proposal_app=reviewed_proposal_client.app_id),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3),
    )

    assert_funded_proposal_global_state(
        reviewed_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by unanimity
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by unanimity
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before + locked_amount - min_fee_times_3.micro_algo,
    )


def test_fund_twice(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee: list[CommitteeMember],
    min_fee_times_3: AlgoAmount,
) -> None:
    proposer_balance_before = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo
    locked_amount = reviewed_proposal_client.state.global_state.locked_amount

    xgov_registry_mock_client.send.fund(
        args=FundArgs(proposal_app=reviewed_proposal_client.app_id),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3),
    )

    assert_funded_proposal_global_state(
        reviewed_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by unanimity
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by unanimity
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before + locked_amount - min_fee_times_3.micro_algo,
    )

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.fund(
            args=FundArgs(proposal_app=reviewed_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_3
            ),
        )


def test_fund_not_registry(
    reviewed_proposal_client: ProposalClient,
    proposer: SigningAccount,
    min_fee_times_3: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        reviewed_proposal_client.send.fund(
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_3
            ),
        )
