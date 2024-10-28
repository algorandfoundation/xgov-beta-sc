from typing import List, Tuple, Type

from algokit_utils import LogicError, TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.encoding import decode_address, encode_address

from smart_contracts.artifacts.proposal.client import GlobalState, ProposalClient
from smart_contracts.proposal.config import VOTER_BOX_KEY_PREFIX
from smart_contracts.proposal.constants import (
    BPS,
)
from smart_contracts.proposal.enums import (
    CATEGORY_NULL,
    CATEGORY_SMALL,
    FUNDING_NULL,
    FUNDING_PROACTIVE,
    STATUS_DRAFT,
    STATUS_EMPTY,
    STATUS_FINAL,
    STATUS_VOTING,
)
from smart_contracts.xgov_registry_mock.config import (
    MIN_REQUESTED_AMOUNT,
    PROPOSAL_COMMITMENT_BPS,
)


def relative_to_absolute_amount(amount: int, fraction_in_bps: int) -> int:
    return amount * fraction_in_bps // BPS


def get_locked_amount(requested_amount: int) -> int:
    return relative_to_absolute_amount(requested_amount, PROPOSAL_COMMITMENT_BPS)


REQUESTED_AMOUNT = MIN_REQUESTED_AMOUNT
LOCKED_AMOUNT = get_locked_amount(REQUESTED_AMOUNT)
PROPOSAL_TITLE = "Test Proposal"
PROPOSAL_CID = b"\x01" * 59

logic_error_type: Type[LogicError] = LogicError

INITIAL_FUNDS = 10_000_000_000

DEFAULT_COMMITTEE_ID = b"\x01" * 32
DEFAULT_COMMITTEE_MEMBERS = 10
DEFAULT_COMMITTEE_VOTES = 100


def assert_proposal_global_state(
    global_state: GlobalState,
    *,
    proposer_address: str,
    registry_app_id: int,
    title: str = "",
    cid: bytes = b"",
    status: int = STATUS_EMPTY,
    category: int = CATEGORY_NULL,
    funding_type: int = FUNDING_NULL,
    requested_amount: int = 0,
    locked_amount: int = 0,
    committee_id: bytes = b"",
    committee_members: int = 0,
    committee_votes: int = 0,
    voted_members: int = 0,
    approvals: int = 0,
    rejections: int = 0,
    nulls: int = 0,
    assigned_votes: int = 0,
    voters_count: int = 0,
    milestone_approved: bool = False,
    # approvers: int = 0,
    # rejectors: int = 0,
) -> None:
    assert encode_address(global_state.proposer.as_bytes) == proposer_address  # type: ignore
    assert global_state.title.as_str == title
    assert global_state.cid.as_bytes == cid
    assert global_state.status == status
    assert global_state.category == category
    assert global_state.funding_type == funding_type
    assert global_state.requested_amount == requested_amount
    assert global_state.locked_amount == locked_amount
    assert global_state.committee_id.as_bytes == committee_id
    assert global_state.committee_members == committee_members
    assert global_state.committee_votes == committee_votes
    assert global_state.voted_members == voted_members
    assert global_state.approvals == approvals
    assert global_state.rejections == rejections
    assert global_state.nulls == nulls
    assert global_state.registry_app_id == registry_app_id
    assert global_state.assigned_votes == assigned_votes
    assert global_state.voters_count == voters_count
    assert global_state.milestone_approved == milestone_approved
    # assert global_state.approvers == approvers
    # assert global_state.rejectors == rejectors

    if status == STATUS_EMPTY:
        assert global_state.submission_ts == 0
    else:
        assert global_state.submission_ts > 0

    if status >= STATUS_FINAL:
        assert global_state.finalization_ts > 0
    else:
        assert global_state.finalization_ts == 0

    if status >= STATUS_VOTING:
        assert global_state.vote_open_ts > 0
    else:
        assert global_state.vote_open_ts == 0


def assert_empty_proposal_global_state(
    global_state: GlobalState, proposer_address: str, registry_app_id: int
) -> None:
    assert_proposal_global_state(
        global_state, proposer_address=proposer_address, registry_app_id=registry_app_id
    )


def assert_draft_proposal_global_state(
    global_state: GlobalState,
    *,
    proposer_address: str,
    registry_app_id: int,
    title: str = PROPOSAL_TITLE,
    cid: bytes = PROPOSAL_CID,
    funding_type: int = FUNDING_PROACTIVE,
    requested_amount: int = REQUESTED_AMOUNT,
    locked_amount: int = LOCKED_AMOUNT,
    category: int = CATEGORY_SMALL,
) -> None:
    assert_proposal_global_state(
        global_state,
        proposer_address=proposer_address,
        registry_app_id=registry_app_id,
        status=STATUS_DRAFT,
        title=title,
        cid=cid,
        funding_type=funding_type,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        category=category,
    )


def assert_final_proposal_global_state(
    global_state: GlobalState,
    *,
    proposer_address: str,
    registry_app_id: int,
    title: str = PROPOSAL_TITLE,
    cid: bytes = PROPOSAL_CID,
    funding_type: int = FUNDING_PROACTIVE,
    requested_amount: int = REQUESTED_AMOUNT,
    locked_amount: int = LOCKED_AMOUNT,
    category: int = CATEGORY_SMALL,
    committee_id: bytes = DEFAULT_COMMITTEE_ID,
    committee_members: int = DEFAULT_COMMITTEE_MEMBERS,
    committee_votes: int = DEFAULT_COMMITTEE_VOTES,
    voters_count: int = 0,
    assigned_votes: int = 0,
) -> None:
    assert_proposal_global_state(
        global_state,
        proposer_address=proposer_address,
        registry_app_id=registry_app_id,
        status=STATUS_FINAL,
        title=title,
        cid=cid,
        funding_type=funding_type,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        category=category,
        committee_id=committee_id,
        committee_members=committee_members,
        committee_votes=committee_votes,
        voters_count=voters_count,
        assigned_votes=assigned_votes,
    )


def assert_voting_proposal_global_state(
    global_state: GlobalState,
    *,
    proposer_address: str,
    registry_app_id: int,
    title: str = PROPOSAL_TITLE,
    cid: bytes = PROPOSAL_CID,
    funding_type: int = FUNDING_PROACTIVE,
    requested_amount: int = REQUESTED_AMOUNT,
    locked_amount: int = LOCKED_AMOUNT,
    category: int = CATEGORY_SMALL,
    committee_id: bytes = DEFAULT_COMMITTEE_ID,
    committee_members: int = DEFAULT_COMMITTEE_MEMBERS,
    committee_votes: int = DEFAULT_COMMITTEE_VOTES,
    voters_count: int = DEFAULT_COMMITTEE_MEMBERS,
    assigned_votes: int = 10 * DEFAULT_COMMITTEE_MEMBERS,
    approvals: int = 0,
    rejections: int = 0,
    nulls: int = 0,
    voted_members: int = 0,
    # approvers: int = 0,
    # rejectors: int = 0,
) -> None:
    assert_proposal_global_state(
        global_state,
        proposer_address=proposer_address,
        registry_app_id=registry_app_id,
        status=STATUS_VOTING,
        title=title,
        cid=cid,
        funding_type=funding_type,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        category=category,
        committee_id=committee_id,
        committee_members=committee_members,
        committee_votes=committee_votes,
        voters_count=voters_count,
        assigned_votes=assigned_votes,
        approvals=approvals,
        rejections=rejections,
        nulls=nulls,
        voted_members=voted_members,
        # approvers=approvers,
        # rejectors=rejectors,
    )


def assert_account_balance(
    algorand_client: AlgorandClient, address: str, expected_balance: int
) -> None:
    assert (
        algorand_client.account.get_information(address)["amount"] == expected_balance  # type: ignore
    )


def assert_boxes(
    algorand_client: AlgorandClient,
    app_id: int,
    expected_boxes: List[Tuple[bytes, str]],
) -> None:
    if len(expected_boxes) == 0:
        assert algorand_client.client.algod.application_boxes(app_id) == {"boxes": []}
    else:
        for box in expected_boxes:
            box_name, expected_value = box
            assert (
                algorand_client.client.algod.application_box_by_name(app_id, box_name)[  # type: ignore
                    "value"
                ]
                == expected_value
            )


def get_voter_box_key(voter_address: str) -> bytes:
    return VOTER_BOX_KEY_PREFIX.encode() + decode_address(voter_address)  # type: ignore


def submit_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    registry_app_id: int,
    *,
    payment_sender: AddressAndSigner = None,  # type: ignore
    payment_receiver: str = "",
    title: str = PROPOSAL_TITLE,
    cid: bytes = PROPOSAL_CID,
    funding_type: int = FUNDING_PROACTIVE,
    requested_amount: int = REQUESTED_AMOUNT,
    locked_amount: int = LOCKED_AMOUNT,
) -> None:
    if payment_sender is None:
        payment_sender = proposer

    if payment_receiver == "":
        payment_receiver = proposal_client.app_address

    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=payment_sender.address,
                    receiver=payment_receiver,
                    amount=locked_amount,
                )
            ),
            signer=payment_sender.signer,
        ),
        title=title,
        cid=cid,
        funding_type=funding_type,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[registry_app_id],
        ),
    )
