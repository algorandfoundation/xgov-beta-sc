from algokit_utils import CommonAppCallParams, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient


def test_funded_proposal(
    proposer: SigningAccount, funded_proposal_client: ProposalClient
) -> None:

    get_state_result = funded_proposal_client.send.get_state(
        params=CommonAppCallParams(sender=proposer.address)
    ).abi_return

    global_state = funded_proposal_client.state.global_state

    assert global_state.approvals == get_state_result.approvals  # type: ignore
    assert global_state.funding_category == get_state_result.funding_category  # type: ignore
    assert global_state.focus == get_state_result.focus  # type: ignore
    assert global_state.committee_id == get_state_result.committee_id  # type: ignore
    assert global_state.committee_members == get_state_result.committee_members  # type: ignore
    assert global_state.committee_votes == get_state_result.committee_votes  # type: ignore
    assert global_state.submission_ts == get_state_result.submission_ts  # type: ignore
    assert global_state.funding_type == get_state_result.funding_type  # type: ignore
    assert global_state.locked_amount == get_state_result.locked_amount  # type: ignore
    assert global_state.nulls == get_state_result.nulls  # type: ignore
    assert global_state.proposer == get_state_result.proposer  # type: ignore
    assert global_state.registry_app_id == get_state_result.registry_app_id  # type: ignore
    assert global_state.rejections == get_state_result.rejections  # type: ignore
    assert global_state.requested_amount == get_state_result.requested_amount  # type: ignore
    assert global_state.status == get_state_result.status  # type: ignore
    assert global_state.open_ts == get_state_result.open_ts  # type: ignore
    assert global_state.title == get_state_result.title  # type: ignore
    assert global_state.vote_open_ts == get_state_result.vote_open_ts  # type: ignore
    assert global_state.voted_members == get_state_result.voted_members  # type: ignore
