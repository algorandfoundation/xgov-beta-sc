import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.encoding import decode_address

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.client import XgovRegistryMockClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import VOTER_BOX_KEY_PREFIX
from smart_contracts.proposal.enums import (
    CATEGORY_SMALL,
    FUNDING_PROACTIVE,
    STATUS_DRAFT,
    STATUS_FINAL,
    STATUS_VOTING,
)
from tests.proposal.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    LOCKED_AMOUNT,
    REQUESTED_AMOUNT,
    assert_account_balance,
    assert_proposal_global_state,
    logic_error_type,
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
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
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
                    VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                    + decode_address(committee_member.address),  # type: ignore
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_FINAL,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
        voters_count=1,
        assigned_votes=10,
    )


def test_assign_voter_assign_all_voters(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_member.address),  # type: ignore
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_VOTING,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
        voters_count=len(committee_members),
        assigned_votes=10 * len(committee_members),
    )


def test_assign_voter_not_committee_publisher(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_member.address),  # type: ignore
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_FINAL,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
    )


def test_assign_voter_voter_already_assigned(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
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
                    VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                    + decode_address(committee_member.address),  # type: ignore
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_member.address),  # type: ignore
                    )
                ],
                suggested_params=sp,
                note="Assigning voter twice should fail",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_FINAL,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
        voters_count=1,
        assigned_votes=10,
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_member.address),  # type: ignore
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state=global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_assign_voter_draft_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_member.address),  # type: ignore
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_DRAFT,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT,
    )


def test_assign_voter_voting_power_mismatch(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_member.address),  # type: ignore
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_members[-1].address),  # type: ignore
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_FINAL,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
        voters_count=len(committee_members[:-1]),
        assigned_votes=10 * len(committee_members[:-1]),
    )


def test_assign_voter_voting_open(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(committee_member.address),  # type: ignore
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
                        VOTER_BOX_KEY_PREFIX.encode()  # type: ignore
                        + decode_address(proposer.address),  # type: ignore
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_VOTING,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
        voters_count=len(committee_members),
        assigned_votes=10 * len(committee_members),
    )
