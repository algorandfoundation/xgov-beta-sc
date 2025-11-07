import pytest
from algokit_utils import (
    AlgoAmount,
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

# TODO add tests for review on other statuses
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_account_balance,
    assert_reviewed_proposal_global_state,
)


def test_review_empty_proposal(
    min_fee_times_2: AlgoAmount,
    xgov_council: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(
                sender=xgov_council.address, static_fee=min_fee_times_2
            ),
        )


def test_review_draft_proposal(
    min_fee_times_2: AlgoAmount,
    xgov_council: SigningAccount,
    draft_proposal_client: ProposalClient,
) -> None:

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        draft_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(
                sender=xgov_council.address, static_fee=min_fee_times_2
            ),
        )


def test_review_submitted_proposal(
    min_fee_times_2: AlgoAmount,
    xgov_council: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> None:

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        submitted_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(
                sender=xgov_council.address, static_fee=min_fee_times_2
            ),
        )


def test_review_voting_proposal(
    min_fee_times_2: AlgoAmount,
    xgov_council: SigningAccount,
    voting_proposal_client: ProposalClient,
) -> None:

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        voting_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(
                sender=xgov_council.address, static_fee=min_fee_times_2
            ),
        )


def test_review_rejected_proposal(
    min_fee_times_2: AlgoAmount,
    xgov_council: SigningAccount,
    rejected_proposal_client: ProposalClient,
) -> None:

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        rejected_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(
                sender=xgov_council.address, static_fee=min_fee_times_2
            ),
        )


def test_review_success(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_council: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    approved_proposal_client: ProposalClient,
) -> None:
    algorand_client = approved_proposal_client.algorand
    proposer_balance_before = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo
    locked_amount = approved_proposal_client.state.global_state.locked_amount
    voters_count = approved_proposal_client.state.global_state.voters_count
    assigned_votes = approved_proposal_client.state.global_state.assigned_votes

    approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(
            sender=xgov_council.address, static_fee=min_fee_times_2
        ),
    )

    assert_reviewed_proposal_global_state(
        approved_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by plebiscite
        voters_count=voters_count,
        assigned_votes=assigned_votes,
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before + locked_amount,
    )


def test_review_twice(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_council: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    approved_proposal_client: ProposalClient,
) -> None:

    approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(
            sender=xgov_council.address, static_fee=min_fee_times_2
        ),
    )

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        approved_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(
                sender=xgov_council.address, static_fee=min_fee_times_2
            ),
        )

    voters_count = approved_proposal_client.state.global_state.voters_count
    assigned_votes = approved_proposal_client.state.global_state.assigned_votes
    assert_reviewed_proposal_global_state(
        approved_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by plebiscite
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by plebiscite
        voters_count=voters_count,
        assigned_votes=assigned_votes,
    )


def test_review_not_council(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    approved_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        approved_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(
                sender=no_role_account.address, static_fee=min_fee_times_2
            ),
        )
