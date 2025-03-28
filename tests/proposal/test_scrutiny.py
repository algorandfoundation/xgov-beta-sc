import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import get_voter_box_key
from tests.proposal.common import (
    assert_approved_proposal_global_state,
    assert_rejected_proposal_global_state,
    logic_error_type,
    submit_proposal,
)
from tests.utils import ERROR_TO_REGEX, time_warp
from tests.xgov_registry.common import LogicErrorType


def test_scrutiny_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_scrutiny_draft_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    submit_proposal(
        proposal_client=proposal_client,
        algorand_client=algorand_client,
        proposer=proposer,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_scrutiny_final_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_scrutiny_voting_ongoing_1(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Proposal is in voting status, and no votes have been cast yet.
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTING_ONGOING]):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_scrutiny_voting_ongoing_2(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Proposal is in voting status, and not all committee members have voted yet.
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=10,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTING_ONGOING]):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_scrutiny_voting_ongoing_3(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Proposal is in voting status, and there is 1 vote missing.
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:-1]:
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

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTING_ONGOING]):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_scrutiny_twice(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members:
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * len(committee_members),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_1(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 1 committee member approves, the rest abstain
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 1
    num_of_rejections = 0

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_2(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 2 committee members approve, 1 committee member rejects, the rest abstain
    """
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 2
    num_of_rejections = 1

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_approve_3(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is approved
    All committee members vote, 11 committee members approve, 9 committee members reject
    """
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 11
    num_of_rejections = 9

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_1(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, all of them abstain
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 0
    num_of_rejections = 0

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_2(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 of them rejects, the rest abstain
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 0
    num_of_rejections = 1

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_3(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 approves, 1 rejects, the rest abstain
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 1
    num_of_rejections = 1

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_4(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 1 approves, 2 rejects, the rest abstain
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 1
    num_of_rejections = 2

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_voting_completed_ahead_of_time_reject_5(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called when voting is completed ahead of time and the proposal is rejected
    All committee members vote, 10 approve, 10 reject
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    num_of_approvals = 10
    num_of_rejections = 10

    for committee_member in committee_members[:num_of_approvals]:
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

    for committee_member in committee_members[
        num_of_approvals : num_of_approvals + num_of_rejections
    ]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[num_of_approvals + num_of_rejections :]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members),
        approvals=10 * num_of_approvals,
        rejections=10 * num_of_rejections,
        nulls=10 * (len(committee_members) - num_of_approvals - num_of_rejections),
    )


def test_scrutiny_after_time_approve_small_1(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    4 committee members vote and approve, reaching the regular and weighted quorums and relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=4,
        approvals=10 * 4,
    )


def test_scrutiny_after_time_approve_small_2(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    4 committee members vote, reaching the regular and weighted quorums
    3 approve and 1 rejects, reaching the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:3]:
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[4].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[4].address,
            signer=committee_members[4].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[4].address),
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

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=4,
        approvals=10 * 3,
        rejections=10,
    )


def test_scrutiny_after_time_approve_small_3(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    4 committee members vote, reaching the regular and weighted quorums
    2 approve, 1 rejects and 1 abstains, reaching the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:2]:
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[4].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[4].address,
            signer=committee_members[4].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[4].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[5].address,
        approvals=0,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[5].address,
            signer=committee_members[5].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[5].address),
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

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=4,
        approvals=10 * 2,
        rejections=10,
        nulls=10,
    )


def test_scrutiny_after_time_approve_small_4(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    19 committee members vote, reaching the regular and weighted quorums
    2 approve, 1 rejects and 16 abstain, reaching the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:2]:
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[2].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[2].address,
            signer=committee_members[2].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[2].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    for committee_member in committee_members[3:-1]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
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

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members) - 1,
        approvals=10 * 2,
        rejections=10,
        nulls=10 * (len(committee_members) - 3 - 1),
    )


def test_scrutiny_after_time_approve_small_5(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is approved
    19 committee members vote, reaching the regular and weighted quorums
    10 approve and 9 abstain, reaching the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[: len(committee_members) // 2]:
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

    for committee_member in committee_members[len(committee_members) // 2 : -1]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    global_state = proposal_client.get_global_state()

    assert_approved_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members) - 1,
        approvals=10 * (len(committee_members) // 2),
        rejections=10 * ((len(committee_members) // 2) - 1),
    )


def test_scrutiny_after_time_reject_small_1(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    no committee members vote
    did not reach the regular and weighted quorums and the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_scrutiny_after_time_reject_small_2(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes and rejects
    did not reach the regular and weighted quorums and the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        rejections=10,
    )


def test_scrutiny_after_time_reject_small_3(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    2 committee members vote and reject
    reached the regular quorum but did not reach the weighted quorum and the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=2,
        rejections=10 * 2,
    )


def test_scrutiny_after_time_reject_small_4(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 vote reject and 1 approve
    did not reach the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:2]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[2].address,
        approvals=10,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[2].address,
            signer=committee_members[2].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[2].address),
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        rejections=10 * 2,
        approvals=10,
    )


def test_scrutiny_after_time_reject_small_5(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    19 committee members vote, reaching the regular quorum and the weighted quorum
    10 vote reject and 9 approve
    did not reach the relative majority of approvals
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[: len(committee_members) // 2]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=0,
            rejections=10,
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

    for committee_member in committee_members[len(committee_members) // 2 : -1]:
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members) - 1,
        rejections=10 * (len(committee_members) // 2),
        approvals=10 * ((len(committee_members) // 2) - 1),
    )


def test_scrutiny_after_time_reject_small_6(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes, not reaching the regular quorum and the weighted quorum
    1 vote approve
    relative majority of approvals is reached
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=10,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )


def test_scrutiny_after_time_reject_small_7(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """ "
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    2 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    relative majority of approvals is reached
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:2]:
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=2,
        approvals=10 * 2,
    )


def test_scrutiny_after_time_reject_small_8(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    3 votes approve
    relative majority of approvals is reached
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:3]:
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10 * 3,
    )


def test_scrutiny_after_time_reject_small_9(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    1 vote reject
    relative majority of approvals is reached
    """

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:2]:
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[2].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[2].address,
            signer=committee_members[2].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[2].address),
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10 * 2,
        rejections=10,
    )


def test_scrutiny_after_time_reject_small_10(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    3 committee members vote, reaching the regular quorum but not the weighted quorum
    2 votes approve
    1 vote abstain
    relative majority of approvals is reached
    """
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    for committee_member in committee_members[:2]:
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[2].address,
        approvals=0,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[2].address,
            signer=committee_members[2].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[2].address),
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10 * 2,
        nulls=10,
    )


def test_scrutiny_after_time_reject_small_11(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    """
    Test that scrutiny can be called after the time has passed and the proposal is rejected
    1 committee member votes, not reaching the regular quorum
    1 vote approve with voting power 48, reaching the weighted quorum
    relative majority of approvals is reached
    """
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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

    proposal_client.assign_voter(
        voter=committee_members[0].address,
        voting_power=48,
        transaction_parameters=TransactionParameters(
            sender=committee_publisher.address,
            signer=committee_publisher.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            boxes=[
                (
                    0,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
        ),
    )

    for committee_member in committee_members[1:]:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=8,
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=48,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
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
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=48,
    )


def test_scrutiny_paused_registry_error(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: AddressAndSigner,
) -> None:

    xgov_registry_mock_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    xgov_registry_mock_client.resume_registry()
    # Should fail for non-paused_registry related reasons

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.scrutiny(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )
