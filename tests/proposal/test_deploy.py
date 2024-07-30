from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk.encoding import encode_address

from smart_contracts.artifacts.proposal.client import ProposalClient


def test_empty_proposal(
    proposal_client: ProposalClient, proposer: AddressAndSigner
) -> None:
    global_state = proposal_client.get_global_state()

    assert (
        encode_address(global_state.proposer.as_bytes)  # type: ignore
        == proposer.address
    )

    assert global_state.title.as_str == ""
    assert global_state.cid.as_bytes == b""
    assert global_state.submission_ts == 0
    assert global_state.finalization_ts == 0
    assert global_state.status == 0
    assert global_state.category == 0
    assert global_state.funding_type == 0
    assert global_state.requested_amount == 0
    assert global_state.locked_amount == 0
    assert global_state.committee_id.as_bytes == b""
    assert global_state.committee_members == 0
    assert global_state.committee_votes == 0
    assert global_state.voted_members == 0
    assert global_state.approvals == 0
    assert global_state.rejections == 0
