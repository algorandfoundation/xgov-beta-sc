import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import (
    AssignVotersArgs,
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    VoteArgs,
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_approved_proposal_global_state,
    assert_rejected_proposal_global_state,
    members_for_both_quorums,
    quorums_reached,
)
from tests.utils import time_warp


def test_scrutiny_empty_proposal(
    no_role_account: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_scrutiny_draft_proposal(
    no_role_account: SigningAccount,
    draft_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        draft_proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_scrutiny_final_proposal(
    no_role_account: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        submitted_proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_scrutiny_voting_ongoing_1(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
) -> None:
    """
    Proposal is in voting status, and no votes have been cast yet.
    """
    with pytest.raises(LogicError, match=err.VOTING_ONGOING):
        voting_proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_scrutiny_voting_ongoing_2(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Proposal is in voting status, and not all committee members have voted yet.
    """
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[0].account.address,
            approvals=committee[0].votes,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    with pytest.raises(LogicError, match=err.VOTING_ONGOING):
        voting_proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_scrutiny_voting_ongoing_3(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Proposal is in voting status, and there is 1 vote missing.
    """
    for cm in committee[:-1]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    with pytest.raises(LogicError, match=err.VOTING_ONGOING):
        voting_proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_scrutiny_twice(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    for cm in committee:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        voting_proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * len(committee),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_1(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 1 committee member approves, the rest abstain
    """
    num_of_approvals = 1
    num_of_rejections = 0

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_2(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 2 committee members approve, 1 committee member rejects, the rest abstain
    """
    num_of_approvals = 2
    num_of_rejections = 1

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_3(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 11 committee members approve, 9 committee members reject
    """
    num_of_approvals = 11
    num_of_rejections = 9

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_1(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, all of them abstain
    """
    num_of_approvals = 0
    num_of_rejections = 0

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_2
        )
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_2(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 of them rejects, the rest abstain
    """
    num_of_approvals = 0
    num_of_rejections = 1

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_2
        )
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_3(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 approves, 1 rejects, the rest abstain
    """
    num_of_approvals = 1
    num_of_rejections = 1

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_2
        )
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_4(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 approves, 2 rejects, the rest abstain
    """
    num_of_approvals = 1
    num_of_rejections = 2

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_2
        )
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_5(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 10 approve, 10 reject
    """
    num_of_approvals = 10
    num_of_rejections = 10

    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (len(committee) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_after_time_approve_small_1(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    Members vote and approve, reaching the regular and weighted quorums and relative majority of approvals
    """
    voted_members, total_votes, member_idx = 0, 0, 0
    while not quorums_reached(
        voting_proposal_client, voted_members, total_votes, plebiscite=False
    ):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee[member_idx].account.address,
                approvals=committee[member_idx].votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )
        voted_members += 1
        total_votes += committee[member_idx].votes
        member_idx += 1

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    members_quorum = members_for_both_quorums(voting_proposal_client, committee)
    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=members_quorum,
        approvals=DEFAULT_MEMBER_VOTES * members_quorum,
    )


def test_scrutiny_after_time_approve_small_2(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    Members vote, reaching the regular and weighted quorums
    Majority approves, 1 rejects, reaching the relative majority of approvals
    """
    num_of_rejections = 1

    voting_members = members_for_both_quorums(voting_proposal_client, committee)
    assert (
        voting_members <= len(committee) - num_of_rejections
    )  # We need at least 1 voting member to reject
    for cm in committee[: voting_members - num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[-1].account.address,
            approvals=0,
            rejections=committee[-1].votes,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=voting_members,
        approvals=DEFAULT_MEMBER_VOTES * (voting_members - num_of_rejections),
        rejections=DEFAULT_MEMBER_VOTES,
    )


def test_scrutiny_after_time_approve_small_3(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    Members vote, reaching the regular and weighted quorums
    Majority approves, 1 rejects, and 1 abstains, reaching the relative majority of approvals
    """
    num_of_rejections = 1
    num_of_abstains = 1

    voting_members = members_for_both_quorums(voting_proposal_client, committee)
    assert (
        voting_members <= len(committee) - num_of_rejections - num_of_abstains
    )  # We need at least 1 voting member to reject and 1 to abstain
    for cm in committee[: voting_members - (num_of_rejections + num_of_abstains)]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[-(num_of_rejections + num_of_abstains)].account.address,
            approvals=0,
            rejections=committee[-(num_of_rejections + num_of_abstains)].votes,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[-num_of_abstains].account.address,
            approvals=0,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=voting_members,
        approvals=DEFAULT_MEMBER_VOTES
        * (voting_members - num_of_rejections - num_of_abstains),
        rejections=DEFAULT_MEMBER_VOTES,
        nulls=DEFAULT_MEMBER_VOTES,
    )


def test_scrutiny_after_time_approve_small_4(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    Members vote, reaching the regular and weighted quorums
    2 approve, 1 rejects, and the majority abstain, reaching the relative majority of approvals
    """
    num_of_approvals = 2
    num_of_rejections = 1

    voting_members = members_for_both_quorums(voting_proposal_client, committee)
    assert (
        voting_members <= len(committee) - num_of_approvals - num_of_rejections
    )  # We need at least 2 voting members to approve and 1 to reject
    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[num_of_approvals].account.address,
            approvals=0,
            rejections=committee[num_of_approvals].votes,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    for cm in committee[(num_of_approvals + num_of_rejections) : voting_members]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=voting_members,
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
        nulls=DEFAULT_MEMBER_VOTES
        * (voting_members - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_after_time_approve_small_5(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    Members vote, reaching the regular and weighted quorums
    10 approve and 9 reject, reaching the relative majority of approvals
    """
    num_of_approvals = 10
    num_of_rejections = 9

    members_for_quorums = members_for_both_quorums(voting_proposal_client, committee)
    assert num_of_approvals + num_of_rejections >= members_for_quorums
    assert num_of_approvals + num_of_rejections <= len(
        committee
    )  # We need at least 10 voting members to approve and 9 to abstain
    for cm in committee[:num_of_approvals]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_of_approvals : num_of_approvals + num_of_rejections]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=num_of_approvals + num_of_rejections,
        approvals=DEFAULT_MEMBER_VOTES * num_of_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_of_rejections,
    )


def test_scrutiny_after_time_reject_small_1(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    no committee members vote
    did not reach the regular and weighted quorums and the relative majority of approvals
    """
    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_scrutiny_after_time_reject_small_2(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes and rejects
    did not reach the regular and weighted quorums and the relative majority of approvals
    """
    # TODO: Parametrize this test with dynamic quorums
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[0].account.address,
            approvals=0,
            rejections=committee[0].votes,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        rejections=committee[0].votes,
    )


def test_scrutiny_after_time_reject_small_3(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    2 committee members vote and reject
    reached the regular quorum but did not reach the weighted quorum and the relative majority of approvals
    """
    # TODO: Parametrize this test with dynamic quorums
    for cm in committee[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=2,
        rejections=DEFAULT_MEMBER_VOTES * 2,
    )


def test_scrutiny_after_time_reject_small_4(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 vote reject and 1 approve
    did not reach the relative majority of approvals
    """
    # TODO: Parametrize this test with dynamic quorums
    for cm in committee[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[2].account.address,
            approvals=committee[2].votes,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        rejections=DEFAULT_MEMBER_VOTES * 2,
        approvals=DEFAULT_MEMBER_VOTES,
    )


def test_scrutiny_after_time_reject_small_5(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    19 committee members vote, reaching the regular quorum and the weighted quorum
    10 vote reject and 9 approve
    did not reach the relative majority of approvals
    """
    # TODO: Parametrize this test with dynamic quorums
    for cm in committee[: len(committee) // 2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=0,
                rejections=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[len(committee) // 2 : -1]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee) - 1,
        rejections=DEFAULT_MEMBER_VOTES * (len(committee) // 2),
        approvals=DEFAULT_MEMBER_VOTES * ((len(committee) // 2) - 1),
    )


def test_scrutiny_after_time_reject_small_6(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes, not reaching the regular quorum and the weighted quorum
    1 vote approve
    relative majority of approvals is reached
    """
    # TODO: Parametrize this test with dynamic quorums
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[0].account.address,
            approvals=committee[0].votes,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=DEFAULT_MEMBER_VOTES,
    )


def test_scrutiny_after_time_reject_small_7(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """ "
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    2 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    relative majority of approvals is reached
    """
    # TODO: Parametrize this test with dynamic quorums
    for cm in committee[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=2,
        approvals=DEFAULT_MEMBER_VOTES * 2,
    )


def test_scrutiny_after_time_reject_small_8(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    3 votes approve
    relative majority of approvals is reached
    """
    # TODO: Parametrize this test with dynamic quorums
    for cm in committee[:3]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=DEFAULT_MEMBER_VOTES * 3,
    )


def test_scrutiny_after_time_reject_small_9(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    1 vote reject
    relative majority of approvals is reached
    """
    # TODO: Parametrize this test with dynamic quorums
    for cm in committee[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[2].account.address,
            approvals=0,
            rejections=committee[2].votes,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=DEFAULT_MEMBER_VOTES * 2,
        rejections=DEFAULT_MEMBER_VOTES,
    )


def test_scrutiny_after_time_reject_small_10(
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    1 vote abstain
    relative majority of approvals is reached
    """
    # TODO: Parametrize this test with dynamic quorums
    for cm in committee[:2]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=cm.account.address,
                approvals=cm.votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee[2].account.address,
            approvals=0,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=DEFAULT_MEMBER_VOTES * 2,
        nulls=DEFAULT_MEMBER_VOTES,
    )


def test_scrutiny_after_time_reject_small_11(
    no_role_account: SigningAccount,
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes, not reaching the regular quorum
    1 vote approve with voting power 48, reaching the weighted quorum
    relative majority of approvals is reached
    """
    # TODO: Parametrize this test with dynamic quorums
    submitted_proposal_client.send.assign_voters(
        args=AssignVotersArgs(voters=[(committee[0].account.address, 48)]),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, signer=xgov_daemon.signer
        ),
    )

    for cm in committee[1:]:
        submitted_proposal_client.send.assign_voters(
            args=AssignVotersArgs(voters=[(cm.account.address, 8)]),
            params=CommonAppCallParams(
                sender=xgov_daemon.address, signer=xgov_daemon.signer
            ),
        )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=submitted_proposal_client.app_id,
            voter=committee[0].account.address,
            approvals=48,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = submitted_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    submitted_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
    )

    assert_rejected_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=48,
    )


def test_scrutiny_paused_registry_error(
    no_role_account: SigningAccount,
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    xgov_registry_mock_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )

    xgov_registry_mock_client.send.resume_registry()
    # Should fail for non-paused_registry related reasons

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )
