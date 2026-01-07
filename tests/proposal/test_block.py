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
from tests.common import DEFAULT_MEMBER_VOTES
from tests.proposal.common import (
    assert_account_balance,
    assert_blocked_proposal_global_state,
)


@pytest.mark.parametrize(
    "client_fixture",
    [
        "proposal_client",  # empty
        "draft_proposal_client",
        "submitted_proposal_client",  # final
        "voting_proposal_client",
        "rejected_proposal_client",
        "reviewed_proposal_client",
    ],
)
def test_block_wrong_status(
    xgov_council: SigningAccount, client_fixture: str, request: pytest.FixtureRequest
) -> None:
    """Test that blocking fails for proposals not in approved status."""
    proposal_client: ProposalClient = request.getfixturevalue(client_fixture)
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_twice(
    xgov_council: SigningAccount,
    blocked_proposal_client: ProposalClient,
) -> None:
    """Test that blocking an already blocked proposal fails."""
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        blocked_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_block_success(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    blocked_proposal_client: ProposalClient,
) -> None:
    """Test that blocking an approved proposal succeeds and transfers funds."""
    xgov_treasury_balance_before = algorand_client.account.get_information(
        xgov_registry_mock_client.app_address
    ).amount.micro_algo

    state = blocked_proposal_client.state.global_state
    locked_amount = state.locked_amount
    voted_members = state.voted_members

    assert_blocked_proposal_global_state(
        blocked_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=voted_members,
        approvals=DEFAULT_MEMBER_VOTES * voted_members,
    )

    assert_account_balance(
        algorand_client,
        xgov_registry_mock_client.app_address,
        xgov_treasury_balance_before + locked_amount,
    )


def test_block_not_council(
    no_role_account: SigningAccount,
    approved_proposal_client: ProposalClient,
) -> None:
    """Test that non-council members cannot block proposals."""
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        approved_proposal_client.send.review(
            args=ReviewArgs(block=True),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
