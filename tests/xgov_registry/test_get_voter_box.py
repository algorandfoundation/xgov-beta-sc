import pytest
from algosdk.constants import ZERO_ADDRESS
from algosdk.error import AlgodHTTPError
from artifacts.proposal.proposal_client import GetVoterBoxArgs, ProposalClient, VoterBox

from tests.common import CommitteeMember


def test_get_voter_box_exists_success(
    voting_proposal_client: ProposalClient,
    committee: list[CommitteeMember],
) -> None:
    result = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address)
    )
    get_voter_box, exists = result.abi_return

    state_voter_box = voting_proposal_client.state.box.voters.get_value(
        committee[0].account.address
    )

    assert exists
    assert VoterBox(
        votes=get_voter_box[0],
        voted=get_voter_box[1],
    ) == VoterBox(
        votes=state_voter_box.votes,
        voted=state_voter_box.voted,
    )  # Note: comparing directly VoterBox(...) == state_voter_box fails


def test_get_voter_box_not_exists_success(
    voting_proposal_client: ProposalClient,
    committee: list[CommitteeMember],
) -> None:
    result = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=ZERO_ADDRESS),
    )
    get_voter_box, exists = result.abi_return

    assert not exists
    assert VoterBox(
        votes=get_voter_box[0],
        voted=get_voter_box[1],
    ) == VoterBox(
        votes=0,
        voted=False,
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):
        voting_proposal_client.state.box.voters.get_value(ZERO_ADDRESS)
