import pytest
from algokit_utils import (
    AlgoAmount,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import (
    AssignVotersArgs,
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    VoteProposalArgs,
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_approved_proposal_global_state,
    assert_rejected_proposal_global_state,
    members_for_both_quorums,
    quorums_reached,
    scrutinize_proposal,
)


def cast_votes(
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_id: int,
    committee: list[CommitteeMember],
    num_approvals: int,
    num_rejections: int,
    num_boycott: int,
    min_fee_times_2: AlgoAmount,
) -> None:
    """Cast approval, rejection, and abstention votes for committee members."""
    # Approvals
    for cm in committee[:num_approvals]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=proposal_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    # Rejections
    for cm in committee[num_approvals : num_approvals + num_rejections]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=proposal_id,
                xgov_address=cm.account.address,
                approval_votes=0,
                rejection_votes=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    # Boycotts
    for cm in committee[
        num_approvals + num_rejections : num_approvals + num_rejections + num_boycott
    ]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=proposal_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    # Abstentions
    for cm in committee[num_approvals + num_rejections + num_boycott :]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=proposal_id,
                xgov_address=cm.account.address,
                approval_votes=0,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )


# --- Status validation tests ---


@pytest.mark.parametrize(
    "client_fixture",
    ["proposal_client", "draft_proposal_client", "submitted_proposal_client"],
)
def test_scrutiny_wrong_status(
    client_fixture: str,
    no_role_account: SigningAccount,
    request: pytest.FixtureRequest,
) -> None:
    client = request.getfixturevalue(client_fixture)
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        client.send.scrutiny(params=CommonAppCallParams(sender=no_role_account.address))


@pytest.mark.parametrize("votes_cast", [0, 1, -1])  # -1 means all but last
def test_scrutiny_voting_ongoing(
    votes_cast: int,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """Voting is ongoing when not all members have voted."""
    if votes_cast == -1:
        members_to_vote = committee[:-1]
    else:
        members_to_vote = committee[:votes_cast]

    for cm in members_to_vote:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    with pytest.raises(LogicError, match=err.VOTING_ONGOING):
        voting_proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_scrutiny_twice(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    cast_votes(
        xgov_registry_mock_client,
        voting_proposal_client.app_id,
        committee,
        len(committee),
        0,
        0,
        min_fee_times_2,
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


# --- All members voted: Approved ---


@pytest.mark.parametrize(
    "num_approvals,num_rejections,num_boycotts",
    [
        (1, 0, 0),  # 1 approves, rest abstain
        (1, 0, 1),  # 1 approves, rest abstain but one boycotts
        (2, 1, 0),  # 2 approve, 1 rejects, rest abstain
        (2, 1, 2),  # 2 approve, 1 rejects, rest abstain but two boycott
        (11, 9, 0),  # 11 approve, 9 reject
    ],
)
def test_scrutiny_all_voted_approved(
    num_approvals: int,
    num_rejections: int,
    num_boycotts: int,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """All committee members vote, proposal is approved."""
    cast_votes(
        xgov_registry_mock_client,
        voting_proposal_client.app_id,
        committee,
        num_approvals,
        num_rejections,
        num_boycotts,
        min_fee_times_2,
    )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    num_nulls = len(committee) - num_approvals - num_rejections
    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        boycotted_members=num_boycotts,
        approvals=DEFAULT_MEMBER_VOTES * num_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_rejections,
        nulls=DEFAULT_MEMBER_VOTES * max(num_nulls - num_boycotts, 0),
    )


# --- All members voted: Rejected ---


@pytest.mark.parametrize(
    "num_approvals,num_rejections,num_boycotts",
    [
        (0, 0, 0),  # All abstain
        (0, 0, 1),  # All abstain but one boycotts
        (0, 1, 0),  # 1 rejects, rest abstain
        (0, 1, 2),  # 1 rejects, rest abstain but two boycott
        (1, 1, 0),  # 1 approves, 1 rejects, rest abstain (tie)
        (1, 1, 3),  # 1 approves, 1 rejects, rest abstain (tie) but three boycott
        (1, 2, 4),  # 1 approves, 2 reject, rest abstain but four boycott
        (10, 10, 0),  # 10 approve, 10 reject (tie)
    ],
)
def test_scrutiny_all_voted_rejected(
    num_approvals: int,
    num_rejections: int,
    num_boycotts: int,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """All committee members vote, proposal is rejected."""
    cast_votes(
        xgov_registry_mock_client,
        voting_proposal_client.app_id,
        committee,
        num_approvals,
        num_rejections,
        num_boycotts,
        min_fee_times_2,
    )

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(
            sender=no_role_account.address, static_fee=min_fee_times_2
        )
    )

    num_nulls = len(committee) - num_approvals - num_rejections
    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee),
        boycotted_members=num_boycotts,
        approvals=DEFAULT_MEMBER_VOTES * num_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_rejections,
        nulls=DEFAULT_MEMBER_VOTES * max(num_nulls - num_boycotts, 0),
    )


# --- After time: Approved (quorums reached) ---


def test_scrutiny_after_time_approve_quorum_reached(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """Quorums reached, all voters approve."""
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    voted_members, total_votes, member_idx = 0, 0, 0

    while not quorums_reached(
        voting_proposal_client, voted_members, total_votes, plebiscite=False
    ):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=committee[member_idx].account.address,
                approval_votes=committee[member_idx].votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )
        voted_members += 1
        total_votes += committee[member_idx].votes
        member_idx += 1

    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)

    members_quorum = members_for_both_quorums(voting_proposal_client, committee)
    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=members_quorum,
        approvals=DEFAULT_MEMBER_VOTES * members_quorum,
        assigned_members=assigned_members - members_quorum,
        assigned_votes=assigned_votes - DEFAULT_MEMBER_VOTES * members_quorum,
    )


@pytest.mark.parametrize(
    "num_rejections,num_abstains",
    [
        (1, 0),  # Majority approves, 1 rejects
        (1, 1),  # Majority approves, 1 rejects, 1 abstains
    ],
)
def test_scrutiny_after_time_approve_with_minority(
    num_rejections: int,
    num_abstains: int,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """Quorums reached with some rejections/abstentions, still approved."""
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    voting_members = members_for_both_quorums(voting_proposal_client, committee)
    num_approvals = voting_members - num_rejections - num_abstains

    # Approvals
    for cm in committee[:num_approvals]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    # Rejections (from end)
    for i in range(num_rejections):
        cm = committee[-(num_rejections + num_abstains) + i]
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=0,
                rejection_votes=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    # Abstentions (from end)
    for i in range(num_abstains):
        cm = committee[-num_abstains + i]
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=0,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)

    assert_approved_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=voting_members,
        approvals=DEFAULT_MEMBER_VOTES * num_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_rejections,
        nulls=DEFAULT_MEMBER_VOTES * num_abstains,
        assigned_members=assigned_members - voting_members,
        assigned_votes=assigned_votes - DEFAULT_MEMBER_VOTES * voting_members,
    )


# --- After time: Rejected (quorums not reached or no majority) ---


@pytest.mark.parametrize(
    "num_approvals,num_rejections,description",
    [
        (0, 0, "no votes"),
        (0, 1, "1 rejection, no quorum"),
        (0, 2, "2 rejections, regular quorum only"),
        (1, 2, "1 approval 2 rejections, no weighted quorum"),
        (1, 0, "1 approval, no quorum"),
        (2, 0, "2 approvals, no weighted quorum"),
        (3, 0, "3 approvals, no weighted quorum"),
        (2, 1, "2 approvals 1 rejection, no weighted quorum"),
    ],
)
def test_scrutiny_after_time_rejected_no_quorum(
    num_approvals: int,
    num_rejections: int,
    description: str,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """Rejected due to not reaching quorums."""
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    voted_members = num_approvals + num_rejections

    # Approvals
    for cm in committee[:num_approvals]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    # Rejections
    for cm in committee[num_approvals:voted_members]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=0,
                rejection_votes=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=voted_members,
        approvals=DEFAULT_MEMBER_VOTES * num_approvals,
        rejections=DEFAULT_MEMBER_VOTES * num_rejections,
        assigned_members=assigned_members - voted_members,
        assigned_votes=assigned_votes - DEFAULT_MEMBER_VOTES * voted_members,
    )


def test_scrutiny_after_time_rejected_with_abstain(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """2 approvals, 1 abstain - no weighted quorum."""
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes

    for cm in committee[:2]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
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

    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=DEFAULT_MEMBER_VOTES * 2,
        nulls=DEFAULT_MEMBER_VOTES,
        assigned_members=assigned_members - 3,
        assigned_votes=assigned_votes - DEFAULT_MEMBER_VOTES * 3,
    )


def test_scrutiny_after_time_rejected_majority_rejects(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    voting_proposal_client: ProposalClient,
) -> None:
    """10 reject, 9 approve - quorums reached but no approval majority."""
    assigned_members = voting_proposal_client.state.global_state.assigned_members
    assigned_votes = voting_proposal_client.state.global_state.assigned_votes
    num_rejections = len(committee) // 2
    num_approvals = num_rejections - 1
    voted_members = len(committee) - 1

    for cm in committee[:num_rejections]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=0,
                rejection_votes=cm.votes,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    for cm in committee[num_rejections:-1]:
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )

    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)

    assert_rejected_proposal_global_state(
        voting_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=voted_members,
        rejections=DEFAULT_MEMBER_VOTES * num_rejections,
        approvals=DEFAULT_MEMBER_VOTES * num_approvals,
        assigned_members=assigned_members - voted_members,
        assigned_votes=assigned_votes - DEFAULT_MEMBER_VOTES * voted_members,
    )


def test_scrutiny_after_time_rejected_weighted_quorum_only(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    """1 member with 48 votes approves - weighted quorum but not regular quorum."""
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

    assigned_members = submitted_proposal_client.state.global_state.assigned_members
    assigned_votes = submitted_proposal_client.state.global_state.assigned_votes

    xgov_registry_mock_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=submitted_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=48,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(static_fee=min_fee_times_2),
    )

    scrutinize_proposal(no_role_account, submitted_proposal_client, min_fee_times_2)

    assert_rejected_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=48,
        assigned_members=assigned_members - 1,
        assigned_votes=assigned_votes - 48,
    )


def test_scrutiny_paused_registry_error(
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
) -> None:
    xgov_registry_mock_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )

    xgov_registry_mock_client.send.resume_registry()

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.send.scrutiny(
            params=CommonAppCallParams(sender=no_role_account.address)
        )
