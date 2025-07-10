from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.encoding import encode_address

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient


def test_funded_proposal(
    funded_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    get_state_result = funded_proposal_client.get_state(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        )
    )

    global_state = funded_proposal_client.get_global_state()

    assert global_state.approvals == get_state_result.return_value.approvals
    assert (
        global_state.funding_category == get_state_result.return_value.funding_category
    )
    assert global_state.focus == get_state_result.return_value.focus
    assert global_state.committee_id.as_bytes == bytes(
        get_state_result.return_value.committee_id
    )
    assert (
        global_state.committee_members
        == get_state_result.return_value.committee_members
    )
    assert global_state.committee_votes == get_state_result.return_value.committee_votes
    assert global_state.finalization_ts == get_state_result.return_value.finalization_ts
    assert global_state.funding_type == get_state_result.return_value.funding_type
    assert global_state.locked_amount == get_state_result.return_value.locked_amount
    assert global_state.nulls == get_state_result.return_value.nulls
    assert (
        encode_address(global_state.proposer.as_bytes)  # type: ignore
        == get_state_result.return_value.proposer
    )
    assert global_state.registry_app_id == get_state_result.return_value.registry_app_id
    assert global_state.rejections == get_state_result.return_value.rejections
    assert (
        global_state.requested_amount == get_state_result.return_value.requested_amount
    )
    assert global_state.status == get_state_result.return_value.status
    assert global_state.submission_ts == get_state_result.return_value.submission_ts
    assert global_state.title.as_bytes == get_state_result.return_value.title.encode()
    assert global_state.vote_open_ts == get_state_result.return_value.vote_open_ts
    assert global_state.voted_members == get_state_result.return_value.voted_members
