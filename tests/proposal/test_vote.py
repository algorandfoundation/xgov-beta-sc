import pytest
from algokit_utils import AlgorandClient, SigningAccount, LogicError, CommonAppCallParams, AlgoAmount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient, VoteArgs,
)
from smart_contracts.errors import std_errors as err
from tests.proposal.common import (
    assert_boxes,
    assert_voting_proposal_global_state,
    assign_voters,
    submit_proposal,
    get_voter_box_key
)
from tests.utils import ERROR_TO_REGEX, time_warp


def test_vote_success(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [(get_voter_box_key(committee_members[0].address), "AAAAAAAAAAqA")],
    )


def test_vote_not_committee_member(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTER_NOT_FOUND]):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=proposer.address,
                approvals=10,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )


def test_vote_already_voted(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTER_ALREADY_VOTED]):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_members[0].address,
                approvals=10,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [(get_voter_box_key(committee_members[0].address), "AAAAAAAAAAqA")],
    )


def test_vote_empty_proposal(
    min_fee_times_2: AlgoAmount,
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_members: list[SigningAccount],
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=proposal_client.app_id,
                voter=committee_members[0].address,
                approvals=10,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )


def test_vote_draft_proposal(
    min_fee_times_2: AlgoAmount,
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_members: list[SigningAccount],
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=draft_proposal_client.app_id,
                voter=committee_members[0].address,
                approvals=10,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )


def test_vote_submitted_proposal(
    min_fee_times_2: AlgoAmount,
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_members: list[SigningAccount],
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=submitted_proposal_client.app_id,
                voter=committee_members[0].address,
                approvals=10,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )


def test_vote_voting_expired(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small

    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.VOTING_PERIOD_EXPIRED]
    ):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_members[0].address,
                approvals=10,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members
        ],
    )


def test_vote_reject(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=0,
            rejections=10,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        rejections=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAqA",
            )
        ],
    )


def test_vote_null(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=0,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        nulls=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAqA",
            )
        ],
    )


def test_vote_mixed(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[1].address,
            approvals=0,
            rejections=10,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[2].address,
            approvals=0,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10,
        rejections=10,
        nulls=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[3:]
        ]
        + [
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAqA",
            )
            for committee_member in committee_members[:3]
        ],
    )


def test_vote_mixed_same_vote_call(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=6,
            rejections=4,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=6,
        rejections=4,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAqA",
            )
        ],
    )


def test_vote_exceeded(
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTES_EXCEEDED]):
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_members[0].address,
                approvals=6,
                rejections=5,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )

    assert_voting_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAoA",
            )
        ],
    )


# FIXME: This test is not testing a vote in paused conditions
@pytest.mark.skip
def test_vote_paused_registry_error(
    min_fee_times_2: AlgoAmount,
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    xgov_registry_mock_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_client=xgov_registry_mock_client,
            proposer=proposer,
        )

    xgov_registry_mock_client.send.resume_registry()

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_mock_client,
        proposer=proposer,
    )

    composer = draft_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )
    composer.send()

    xgov_registry_mock_client.send.vote(
        args=VoteArgs(
            proposal_app=draft_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    assert_voting_proposal_global_state(
        draft_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [(get_voter_box_key(committee_members[0].address), "AAAAAAAAAAqA")],
    )
