import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import (
    GetVoterBoxArgs,
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    VoteProposalArgs,
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_boxes,
    assert_voting_proposal_global_state,
    get_voter_box_key,
)
from tests.utils import time_warp


def test_vote_success(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=committee[0].votes,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )
    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=committee[0].votes,
        assigned_members=assigned_members - 1,
        assigned_votes=assigned_votes - committee[0].votes,
    )

    _, exists = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address),
        params=CommonAppCallParams(sender=proposer.address),
    ).abi_return
    assert not exists


def test_vote_not_committee_member(
    min_fee_times_2: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.VOTER_NOT_FOUND):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=proposer.address,
                approval_votes=42,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )


def test_vote_already_voted(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=committee[0].votes,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    with pytest.raises(LogicError, match=err.VOTER_NOT_FOUND):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=committee[0].votes,
        assigned_members=assigned_members - 1,
        assigned_votes=assigned_votes - committee[0].votes,
    )

    _, exists = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address),
        params=CommonAppCallParams(sender=proposer.address),
    ).abi_return
    assert not exists


def test_vote_empty_proposal(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )


def test_vote_draft_proposal(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=draft_proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )


def test_vote_submitted_proposal(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=submitted_proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )


def test_vote_voting_expired(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small

    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    with pytest.raises(LogicError, match=err.VOTING_PERIOD_EXPIRED):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_members=len(committee),
        assigned_votes=DEFAULT_MEMBER_VOTES * len(committee),
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(cm.account.address),
                "AAAAAAAAAAo=",
            )
            for cm in committee
        ],
    )


def test_vote_reject(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=0,
            rejection_votes=committee[0].votes,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        rejections=committee[0].votes,
        assigned_members=assigned_members - 1,
        assigned_votes=assigned_votes - committee[0].votes,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(cm.account.address),
                "AAAAAAAAAAo=",
            )
            for cm in committee[1:]
        ],
    )

    _, exists = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address),
        params=CommonAppCallParams(sender=proposer.address),
    ).abi_return
    assert not exists


def test_vote_null(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=0,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        nulls=committee[0].votes,
        assigned_members=assigned_members - 1,
        assigned_votes=assigned_votes - committee[0].votes,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(cm.account.address),
                "AAAAAAAAAAo=",
            )
            for cm in committee[1:]
        ],
    )

    _, exists = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address),
        params=CommonAppCallParams(sender=proposer.address),
    ).abi_return
    assert not exists


def test_vote_mixed(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=committee[0].votes,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[1].account.address,
            approval_votes=0,
            rejection_votes=committee[0].votes,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[2].account.address,
            approval_votes=0,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=committee[0].votes,
        rejections=committee[0].votes,
        nulls=committee[0].votes,
        assigned_members=assigned_members - 3,
        assigned_votes=assigned_votes
        - committee[0].votes
        - committee[1].votes
        - committee[2].votes,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(cm.account.address),
                "AAAAAAAAAAo=",
            )
            for cm in committee[3:]
        ],
    )

    for cm in committee[:3]:
        _, exists = voting_proposal_client.send.get_voter_box(
            args=GetVoterBoxArgs(voter_address=cm.account.address),
            params=CommonAppCallParams(sender=proposer.address),
        ).abi_return
        assert not exists


def test_vote_mixed_same_vote_call(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=6,
            rejection_votes=4,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=6,
        rejections=4,
        assigned_members=assigned_members - 1,
        assigned_votes=assigned_votes - committee[0].votes,
    )

    _, exists = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address),
        params=CommonAppCallParams(sender=proposer.address),
    ).abi_return
    assert not exists


def test_vote_boycotted(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=6,
            rejection_votes=5,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        boycotted_members=1,
        assigned_members=len(committee) - 1,
        assigned_votes=DEFAULT_MEMBER_VOTES * (len(committee) - 1),
    )

    _, exists = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address),
        params=CommonAppCallParams(sender=proposer.address),
    ).abi_return
    assert not exists
