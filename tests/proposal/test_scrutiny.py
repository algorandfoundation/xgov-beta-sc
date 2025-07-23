import pytest
from algokit_utils import AlgorandClient, SigningAccount, LogicError

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient, AssignVotersArgs
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient, VoteArgs,
)
from smart_contracts.errors import std_errors as err
from tests.proposal.common import (
    assert_approved_proposal_global_state,
    assert_rejected_proposal_global_state,
)
from tests.utils import ERROR_TO_REGEX, time_warp


def test_scrutiny_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.send.send.scrutiny()


def test_scrutiny_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
) -> None:

    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        draft_proposal_client.send.scrutiny()


def test_scrutiny_final_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
) -> None:

    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        submitted_proposal_client.send.scrutiny()


def test_scrutiny_voting_ongoing_1(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
) -> None:
    """
    Proposal is in voting status, and no votes have been cast yet.
    """

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTING_ONGOING]):
        voting_proposal_client.send.scrutiny()


def test_scrutiny_voting_ongoing_2(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount]
) -> None:
    """
    Proposal is in voting status, and not all committee members have voted yet.
    """
    xgov_registry_mock_client.send.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
        ),
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTING_ONGOING]):
        voting_proposal_client.send.scrutiny()


def test_scrutiny_voting_ongoing_3(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Proposal is in voting status, and there is 1 vote missing.
    """
    for committee_member in committee_members[:-1]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTING_ONGOING]):
        voting_proposal_client.send.scrutiny()


def test_scrutiny_twice(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    for committee_member in committee_members:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * len(committee_members),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_1(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 1 committee member approves, the rest abstain
    """
    num_of_approvals = 1
    num_of_rejections = 0

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_2(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 2 committee members approve, 1 committee member rejects, the rest abstain
    """
    num_of_approvals = 2
    num_of_rejections = 1

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_3(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 11 committee members approve, 9 committee members reject
    """
    num_of_approvals = 11
    num_of_rejections = 9

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_1(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, all of them abstain
    """
    num_of_approvals = 0
    num_of_rejections = 0

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_2(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 of them rejects, the rest abstain
    """
    num_of_approvals = 0
    num_of_rejections = 1

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_3(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 approves, 1 rejects, the rest abstain
    """
    num_of_approvals = 1
    num_of_rejections = 1

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            ),
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            ),
        )

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_4(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 approves, 2 rejects, the rest abstain
    """
    num_of_approvals = 1
    num_of_rejections = 2

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_5(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 10 approve, 10 reject
    """
    num_of_approvals = 10
    num_of_rejections = 10

    for committee_member in committee_members[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_after_time_approve_small_1(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    4 committee members vote and approve, reaching the regular and weighted quorums and relative majority of approvals
    """
    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=4,
        approvals=10 * 4,
    )


def test_scrutiny_after_time_approve_small_2(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    4 committee members vote, reaching the regular and weighted quorums
    3 approve and 1 rejects, reaching the relative majority of approvals
    """
    for committee_member in committee_members[:3]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[4].address,
            approvals=0,
            rejections=10,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=4,
        approvals=10 * 3,
        rejections=10,
    )


def test_scrutiny_after_time_approve_small_3(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    4 committee members vote, reaching the regular and weighted quorums
    2 approve, 1 rejects and 1 abstains, reaching the relative majority of approvals
    """
    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[4].address,
            approvals=0,
            rejections=10,
        )
    )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[5].address,
            approvals=0,
            rejections=0,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=4,
        approvals=10 * 2,
        rejections=10,
        nulls=10,
    )


def test_scrutiny_after_time_approve_small_4(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    19 committee members vote, reaching the regular and weighted quorums
    2 approve, 1 rejects and 16 abstain, reaching the relative majority of approvals
    """
    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[2].address,
            approvals=0,
            rejections=10,
        )
    )

    for committee_member in committee_members[3:-1]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=0,
            )
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members) - 1,
        approvals=10 * 2,
        rejections=10,
        nulls=10 * (len(committee_members) - 3 - 1),
    )


def test_scrutiny_after_time_approve_small_5(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    19 committee members vote, reaching the regular and weighted quorums
    10 approve and 9 abstain, reaching the relative majority of approvals
    """
    for committee_member in committee_members[: len(committee_members) // 2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    for committee_member in committee_members[len(committee_members) // 2 : -1]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members) - 1,
        approvals=10 * (len(committee_members) // 2),
        rejections=10 * ((len(committee_members) // 2) - 1),
    )


def test_scrutiny_after_time_reject_small_1(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    no committee members vote
    did not reach the regular and weighted quorums and the relative majority of approvals
    """
    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_scrutiny_after_time_reject_small_2(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes and rejects
    did not reach the regular and weighted quorums and the relative majority of approvals
    """
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=0,
            rejections=10,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        rejections=10,
    )


def test_scrutiny_after_time_reject_small_3(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    2 committee members vote and reject
    reached the regular quorum but did not reach the weighted quorum and the relative majority of approvals
    """
    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=2,
        rejections=10 * 2,
    )


def test_scrutiny_after_time_reject_small_4(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 vote reject and 1 approve
    did not reach the relative majority of approvals
    """
    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[2].address,
            approvals=10,
            rejections=0,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        rejections=10 * 2,
        approvals=10,
    )


def test_scrutiny_after_time_reject_small_5(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    19 committee members vote, reaching the regular quorum and the weighted quorum
    10 vote reject and 9 approve
    did not reach the relative majority of approvals
    """
    for committee_member in committee_members[: len(committee_members) // 2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=0,
                rejections=10,
            )
        )

    for committee_member in committee_members[len(committee_members) // 2 : -1]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members) - 1,
        rejections=10 * (len(committee_members) // 2),
        approvals=10 * ((len(committee_members) // 2) - 1),
    )


def test_scrutiny_after_time_reject_small_6(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes, not reaching the regular quorum and the weighted quorum
    1 vote approve
    relative majority of approvals is reached
    """
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )


def test_scrutiny_after_time_reject_small_7(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """ "
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    2 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    relative majority of approvals is reached
    """
    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=2,
        approvals=10 * 2,
    )


def test_scrutiny_after_time_reject_small_8(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    3 votes approve
    relative majority of approvals is reached
    """
    for committee_member in committee_members[:3]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10 * 3,
    )


def test_scrutiny_after_time_reject_small_9(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    1 vote reject
    relative majority of approvals is reached
    """
    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[2].address,
            approvals=0,
            rejections=10,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10 * 2,
        rejections=10,
    )


def test_scrutiny_after_time_reject_small_10(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    1 vote abstain
    relative majority of approvals is reached
    """
    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            )
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[2].address,
            approvals=0,
            rejections=0,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10 * 2,
        nulls=10,
    )


def test_scrutiny_after_time_reject_small_11(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes, not reaching the regular quorum
    1 vote approve with voting power 48, reaching the weighted quorum
    relative majority of approvals is reached
    """
    submitted_proposal_client.send.assign_voters(
        args=AssignVotersArgs(voters=[(committee_members[0].address, 48)]),
    )

    for committee_member in committee_members[1:]:
        submitted_proposal_client.send.assign_voters(
            args=AssignVotersArgs(voters=[(committee_member.address, 8)]),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=submitted_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=48,
            rejections=0,
        )
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = submitted_proposal_client.state.global_state.send.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    submitted_proposal_client.send.scrutiny()

    assert_rejected_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=48,
    )


def test_scrutiny_paused_registry_error(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
) -> None:
    xgov_registry_mock_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        proposal_client.send.scrutiny()

    xgov_registry_mock_client.send.resume_registry()
    # Should fail for non-paused_registry related reasons

    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.send.scrutiny()
