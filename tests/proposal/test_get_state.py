from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.encoding import encode_address

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from tests.proposal.common import (
    get_voter_box_key,
    submit_proposal,
)
from tests.utils import time_warp


def test_funded_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
                boxes=[
                    (
                        proposal_client.app_id,
                        get_voter_box_key(committee_member.address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    proposal_client.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_reviewer.address,
            signer=xgov_reviewer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    xgov_registry_mock_client.fund(
        proposal_app=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[proposal_client.app_id],
        ),
    )

    get_state_result = proposal_client.get_state(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        )
    )

    global_state = proposal_client.get_global_state()

    assert global_state.approvals == get_state_result.return_value.approvals
    assert (
        global_state.funding_category == get_state_result.return_value.funding_category
    )
    assert global_state.focus.as_bytes == get_state_result.return_value.focus.to_bytes(
        1, "big"
    )
    assert global_state.cid.as_bytes == bytes(get_state_result.return_value.cid)
    assert global_state.committee_id.as_bytes == bytes(
        get_state_result.return_value.committee_id
    )
    assert (
        global_state.committee_members
        == get_state_result.return_value.committee_members
    )
    assert global_state.committee_votes == get_state_result.return_value.committee_votes
    assert (
        global_state.cool_down_start_ts
        == get_state_result.return_value.cool_down_start_ts
    )
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
