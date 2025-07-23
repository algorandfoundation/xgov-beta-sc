from algokit_utils import AlgorandClient, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient


def test_funded_proposal(
    funded_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
) -> None:

    get_state_result = funded_proposal_client.send.get_state().abi_return

    global_state = funded_proposal_client.state.global_state

    assert global_state.approvals == get_state_result.approvals
    assert (
        global_state.funding_category == get_state_result.funding_category
    )
    assert global_state.focus == get_state_result.focus
    assert bytes(global_state.committee_id) == get_state_result.committee_id
    assert global_state.committee_members == get_state_result.committee_members
    assert global_state.committee_votes == get_state_result.committee_votes
    assert global_state.submission_ts == get_state_result.submission_ts
    assert global_state.funding_type == get_state_result.funding_type
    assert global_state.locked_amount == get_state_result.locked_amount
    assert global_state.nulls == get_state_result.nulls
    assert global_state.proposer == get_state_result.proposer
    assert global_state.registry_app_id == get_state_result.registry_app_id
    assert global_state.rejections == get_state_result.rejections
    assert (
        global_state.requested_amount == get_state_result.requested_amount
    )
    assert global_state.status == get_state_result.status
    assert global_state.open_ts == get_state_result.open_ts
    assert global_state.title == get_state_result.title
    assert global_state.vote_open_ts == get_state_result.vote_open_ts
    assert global_state.voted_members == get_state_result.voted_members
