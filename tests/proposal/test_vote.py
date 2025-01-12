import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err

# TODO add tests for vote on other statuses
from tests.common import get_voter_box_key
from tests.proposal.common import (
    assert_boxes,
    assert_voting_proposal_global_state,
    logic_error_type,
    submit_proposal,
)
from tests.utils import time_warp


def test_vote_success(
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

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
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

    with pytest.raises(logic_error_type, match=err.VOTER_NOT_FOUND):
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=proposer.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
                boxes=[(proposal_client.app_id, get_voter_box_key(proposer.address))],
                suggested_params=sp,
            ),
        )


def test_vote_already_voted(
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

    with pytest.raises(logic_error_type, match=err.VOTER_ALREADY_VOTED):
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
                note="Second vote",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
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
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
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


def test_vote_draft_proposal(
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

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
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


def test_vote_finalized_proposal(
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

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
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


def test_vote_voting_expired(
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

    voting_duration = reg_gs.voting_duration_small

    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    with pytest.raises(logic_error_type, match=err.VOTING_PERIOD_EXPIRED):
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

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members
        ],
    )


def test_vote_reject(
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

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        rejections=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=0,
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

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        nulls=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[1].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[1].address,
            signer=committee_members[1].signer,
            foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
            boxes=[
                (
                    proposal_client.app_id,
                    get_voter_box_key(committee_members[1].address),
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

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10,
        rejections=10,
        nulls=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
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

    xgov_registry_mock_client.vote(
        proposal_app=proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=6,
        rejections=4,
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

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=6,
        rejections=4,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAqA",
            )
        ],
    )


def test_vote_exceeded(
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

    with pytest.raises(logic_error_type, match=err.VOTES_EXCEEDED):
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=6,
            rejections=5,
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

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAoA",
            )
        ],
    )
