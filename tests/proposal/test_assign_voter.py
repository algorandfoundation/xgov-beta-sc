import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.client import XgovRegistryMockClient
from smart_contracts.errors import std_errors as err
from tests.proposal.common import (
    LOCKED_AMOUNT,
    assert_account_balance,
    assert_boxes,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_final_proposal_global_state,
    assert_voting_proposal_global_state,
    get_voter_box_key,
    logic_error_type,
    submit_proposal,
)

# TODO add tests for assign_voter on other statuses


def test_assign_voter_success(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
        ),
    )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    voter_box_key = get_voter_box_key(committee_member.address)

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
                    voter_box_key,
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voters_count=1,
        assigned_votes=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[(voter_box_key, "AAAAAAAAAAoA")],
    )


def test_assign_voter_assign_all_voters(
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

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
        ),
    )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

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


def test_assign_voter_not_committee_publisher(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
        ),
    )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[],  # no voter boxes
    )


def test_assign_voter_voter_already_assigned(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
        ),
    )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    voter_box_key = get_voter_box_key(committee_member.address)

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
                    voter_box_key,
                )
            ],
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=err.VOTER_ALREADY_ASSIGNED):
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
                        voter_box_key,
                    )
                ],
                suggested_params=sp,
                note="Assigning voter twice should fail",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voters_count=1,
        assigned_votes=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[(voter_box_key, "AAAAAAAAAAoA")],
    )


def test_assign_voter_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
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
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[],  # no voter box
    )


def test_assign_voter_draft_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
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
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[],  # no voter box
    )


def test_assign_voter_voting_power_mismatch(
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

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
        ),
    )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    for committee_member in committee_members[:-1]:
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
                suggested_params=sp,
            ),
        )

    with pytest.raises(logic_error_type, match=err.VOTING_POWER_MISMATCH):
        proposal_client.assign_voter(
            voter=committee_members[-1].address,
            voting_power=5,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_members[-1].address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voters_count=len(committee_members[:-1]),
        assigned_votes=10 * len(committee_members[:-1]),
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[:-1]
        ],
    )


def test_assign_voter_voting_open(
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

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
        ),
    )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

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
                suggested_params=sp,
            ),
        )

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.assign_voter(
            voter=proposer.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(proposer.address),
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
