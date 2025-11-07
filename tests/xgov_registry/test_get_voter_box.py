import pytest
from algosdk.constants import ZERO_ADDRESS
from algosdk.error import AlgodHTTPError
from smart_contracts.artifacts.proposal.proposal_client import GetVoterBoxArgs, ProposalClient

from tests.common import CommitteeMember


def test_get_voter_box(
    committee: list[CommitteeMember], voting_proposal_client: ProposalClient
) -> None:
    existing_box_result = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=committee[0].account.address)
    )
    votes, exists = existing_box_result.abi_return

    state_votes = voting_proposal_client.state.box.voters.get_value(
        committee[0].account.address
    )

    assert exists
    assert votes == state_votes

    not_existing_box_result = voting_proposal_client.send.get_voter_box(
        args=GetVoterBoxArgs(voter_address=ZERO_ADDRESS),
    )
    votes, exists = not_existing_box_result.abi_return

    assert not exists
    assert not votes

    with pytest.raises(AlgodHTTPError, match="box not found"):
        voting_proposal_client.state.box.voters.get_value(ZERO_ADDRESS)
