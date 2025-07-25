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

# TODO add tests for review on other statuses
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import assert_reviewed_proposal_global_state


def test_review_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: SigningAccount,
) -> None:
    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_review_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        draft_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_review_submitted_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        submitted_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_review_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        voting_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_review_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_council: SigningAccount,
) -> None:

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        rejected_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(sender=xgov_council.address),
        )


def test_review_success(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    xgov_council: SigningAccount,
) -> None:

    approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(sender=xgov_council.address),
    )

    assert_reviewed_proposal_global_state(
        approved_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by unanimity
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by unanimity
    )


def test_review_twice(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    xgov_council: SigningAccount,
) -> None:

    approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(sender=xgov_council.address),
    )

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        approved_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(sender=xgov_council.address),
        )

    assert_reviewed_proposal_global_state(
        approved_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(
            committee
        ),  # by default, the xGov Committee approves by unanimity
        approvals=DEFAULT_MEMBER_VOTES
        * len(committee),  # by default, the xGov Committee approves by unanimity
    )


def test_review_not_council(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    no_role_account: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        approved_proposal_client.send.review(
            args=ReviewArgs(block=False),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
