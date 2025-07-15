import uuid

from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.encoding import encode_address
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import (
    Composer,
    GlobalState,
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.proposal.config import GLOBAL_BYTES, GLOBAL_UINTS, METADATA_BOX_KEY
from smart_contracts.proposal.enums import (
    FUNDING_CATEGORY_NULL,
    FUNDING_CATEGORY_SMALL,
    FUNDING_NULL,
    FUNDING_PROACTIVE,
    STATUS_APPROVED,
    STATUS_BLOCKED,
    STATUS_DRAFT,
    STATUS_EMPTY,
    STATUS_FINAL,
    STATUS_FUNDED,
    STATUS_REJECTED,
    STATUS_REVIEWED,
    STATUS_VOTING,
)
from smart_contracts.xgov_registry_mock.config import OPEN_PROPOSAL_FEE
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    DEFAULT_FOCUS,
    LOCKED_AMOUNT,
    PROPOSAL_TITLE,
    REQUESTED_AMOUNT,
    get_voter_box_key,
)

MAX_UPLOAD_PAYLOAD_SIZE = 2041  # 2048 - 4 bytes (method selector) - 2 bytes (payload length) - 1 byte (boolean flag)


PROPOSAL_MBR = 200_000 + (28_500 * GLOBAL_UINTS) + (50_000 * GLOBAL_BYTES)
PROPOSAL_PARTIAL_FEE = OPEN_PROPOSAL_FEE - PROPOSAL_MBR

INITIAL_FUNDS = 10_000_000_000


def assert_proposal_global_state(
    global_state: GlobalState,
    *,
    proposer_address: str,
    registry_app_id: int,
    status: int = STATUS_EMPTY,
    decommissioned: bool = False,
    title: str = "",
    funding_category: int = FUNDING_CATEGORY_NULL,
    focus: int = 0,
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
) -> None:
    assert encode_address(global_state.proposer.as_bytes) == proposer_address  # type: ignore
    assert global_state.title.as_str == title
    assert global_state.status == status
    assert global_state.decommissioned == decommissioned
    assert global_state.funding_category == funding_category
    assert global_state.focus == focus
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


def get_default_params_for_status(status: int, overrides: dict, *, decommissioned: bool) -> dict:  # type: ignore
    # Define common parameters that are shared across statuses
    common_defaults = {
        "title": PROPOSAL_TITLE,
        "funding_type": FUNDING_PROACTIVE,
        "requested_amount": REQUESTED_AMOUNT,
        "locked_amount": LOCKED_AMOUNT,
        "funding_category": FUNDING_CATEGORY_SMALL,
        "focus": DEFAULT_FOCUS,
    }

    # Define common committee-related defaults used in multiple statuses
    committee_defaults = {
        "committee_id": DEFAULT_COMMITTEE_ID,
        "committee_members": DEFAULT_COMMITTEE_MEMBERS,
        "committee_votes": DEFAULT_COMMITTEE_VOTES,
    }

    # Define common voter-related defaults used in multiple statuses
    voter_defaults = {
        "voters_count": 0 if decommissioned else DEFAULT_COMMITTEE_MEMBERS,
        "assigned_votes": 0 if decommissioned else 10 * DEFAULT_COMMITTEE_MEMBERS,
    }

    # Specific status defaults, with shared defaults included where needed
    status_defaults = {
        STATUS_DRAFT: {
            "status": STATUS_DRAFT,
            **committee_defaults,
            "locked_amount": 0 if decommissioned else LOCKED_AMOUNT,
        },
        STATUS_FINAL: {"status": STATUS_FINAL, **committee_defaults},
        STATUS_VOTING: {
            "status": STATUS_VOTING,
            **committee_defaults,
            **voter_defaults,
        },
        STATUS_APPROVED: {
            "status": STATUS_APPROVED,
            **committee_defaults,
            **voter_defaults,
        },
        STATUS_REJECTED: {
            "status": STATUS_REJECTED,
            **committee_defaults,
            **voter_defaults,
            "locked_amount": 0,
        },
        STATUS_REVIEWED: {
            "status": STATUS_REVIEWED,
            **committee_defaults,
            **voter_defaults,
        },
        STATUS_BLOCKED: {
            "status": STATUS_BLOCKED,
            **committee_defaults,
            **voter_defaults,
            "locked_amount": 0,
        },
        STATUS_FUNDED: {
            "status": STATUS_FUNDED,
            **committee_defaults,
            **voter_defaults,
            "locked_amount": 0,
        },
    }.get(status, {})

    # Combine all defaults and apply overrides, with overrides taking precedence
    return {**common_defaults, **status_defaults, **overrides}  # type: ignore


def assert_proposal_with_status(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    status: int,
    *,
    decommissioned: bool = False,
    **overrides,  # noqa: ANN003
) -> None:
    params = get_default_params_for_status(status, overrides, decommissioned=decommissioned)  # type: ignore
    assert_proposal_global_state(
        global_state,
        proposer_address=proposer_address,
        registry_app_id=registry_app_id,
        decommissioned=decommissioned,
        **params,  # type: ignore
    )


def assert_empty_proposal_global_state(
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    *,
    decommissioned: bool = False,
) -> None:
    assert_proposal_global_state(
        global_state,
        proposer_address=proposer_address,
        registry_app_id=registry_app_id,
        decommissioned=decommissioned,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
    )


def assert_draft_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    *,
    decommissioned: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_DRAFT, decommissioned=decommissioned, **kwargs  # type: ignore
    )


def assert_voting_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_VOTING, **kwargs  # type: ignore
    )


def assert_approved_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_APPROVED, **kwargs  # type: ignore
    )


def assert_rejected_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    *,
    decommissioned: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_REJECTED, decommissioned=decommissioned, **kwargs  # type: ignore
    )


def assert_final_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_FINAL, **kwargs  # type: ignore
    )


def assert_reviewed_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_REVIEWED, **kwargs  # type: ignore
    )


def assert_blocked_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    *,
    decommissioned: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_BLOCKED, decommissioned=decommissioned, **kwargs  # type: ignore
    )


def assert_funded_proposal_global_state(  # type: ignore
    global_state: GlobalState,
    proposer_address: str,
    registry_app_id: int,
    *,
    decommissioned: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        global_state, proposer_address, registry_app_id, STATUS_FUNDED, decommissioned=decommissioned, **kwargs  # type: ignore
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
    expected_boxes: list[tuple[bytes, str]],
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


def submit_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    registry_app_id: int,
    *,
    payment_sender: AddressAndSigner = None,  # type: ignore
    payment_receiver: str = "",
    title: str = PROPOSAL_TITLE,
    metadata: bytes = b"METADATA",
    funding_type: int = FUNDING_PROACTIVE,
    focus: int = DEFAULT_FOCUS,
    requested_amount: int = REQUESTED_AMOUNT,
    locked_amount: int = LOCKED_AMOUNT,
) -> None:
    if payment_sender is None:
        payment_sender = proposer

    if payment_receiver == "":
        payment_receiver = proposal_client.app_address

    composer = proposal_client.compose()

    composer.submit(
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
        funding_type=funding_type,
        focus=focus,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[registry_app_id],
        ),
    )

    if metadata != b"":
        upload_metadata(
            composer,
            proposer,
            registry_app_id,
            metadata,
        )

    composer.execute()


def upload_metadata(
    proposal_client_composer: Composer,
    proposer: AddressAndSigner,
    registry_app_id: int,
    metadata: bytes,
) -> None:

    for i in range((len(metadata) // MAX_UPLOAD_PAYLOAD_SIZE) + 1):
        proposal_client_composer.upload_metadata(
            payload=metadata[
                i * MAX_UPLOAD_PAYLOAD_SIZE : (i + 1) * MAX_UPLOAD_PAYLOAD_SIZE
            ],
            is_first_in_group=i == 0,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[registry_app_id],
                boxes=[(0, METADATA_BOX_KEY), (0, METADATA_BOX_KEY)],
                note=uuid.uuid4().bytes,
            ),
        )


def unassign_voters(
    proposal_client_composer: Composer,
    committee_members: list[AddressAndSigner],
    xgov_daemon: AddressAndSigner,
    sp: SuggestedParams,
    xgov_registry_app_id: int,
    bulks: int = 8,
) -> None:
    proposal_client_composer.unassign_voters(
        voters=[cm.address for cm in committee_members[: bulks - 1]],
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
            foreign_apps=[xgov_registry_app_id],
            boxes=[
                (
                    0,
                    get_voter_box_key(cm.address),
                )
                for cm in committee_members[: bulks - 1]
            ],
            suggested_params=sp,
        ),
    )
    rest_of_committee_members = committee_members[bulks - 1 :]
    for i in range(1 + len(rest_of_committee_members) // bulks):
        proposal_client_composer.unassign_voters(
            voters=[
                cm.address
                for cm in rest_of_committee_members[i * bulks : (i + 1) * bulks]
            ],
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                boxes=[
                    (
                        0,
                        get_voter_box_key(cm.address),
                    )
                    for cm in rest_of_committee_members[i * bulks : (i + 1) * bulks]
                ],
                suggested_params=sp,
            ),
        )


def assign_voters(
    proposal_client_composer: Composer,
    committee_members: list[AddressAndSigner],
    xgov_daemon: AddressAndSigner,
    sp: SuggestedParams,
    xgov_registry_app_id: int,
    bulks: int = 8,
) -> None:
    proposal_client_composer.assign_voters(
        voters=[(cm.address, 10) for cm in committee_members[: bulks - 1]],
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
            foreign_apps=[xgov_registry_app_id],
            boxes=[
                (
                    0,
                    get_voter_box_key(cm.address),
                )
                for cm in committee_members[: bulks - 1]
            ],
            suggested_params=sp,
        ),
    )
    rest_of_committee_members = committee_members[bulks - 1 :]
    for i in range(1 + len(rest_of_committee_members) // bulks):
        proposal_client_composer.assign_voters(
            voters=[
                (cm.address, 10)
                for cm in rest_of_committee_members[i * bulks : (i + 1) * bulks]
            ],
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                boxes=[
                    (
                        0,
                        get_voter_box_key(cm.address),
                    )
                    for cm in rest_of_committee_members[i * bulks : (i + 1) * bulks]
                ],
                suggested_params=sp,
            ),
        )


def decommission_proposal(
    xgov_registry_client: XgovRegistryMockClient,
    proposal_app_id: int,
    xgov_daemon: AddressAndSigner,
    sp: SuggestedParams,
    note: str = "",
) -> None:
    xgov_registry_client.decommission_proposal(
        proposal_app=proposal_app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
            foreign_apps=[proposal_app_id],
            boxes=[
                (
                    proposal_app_id,
                    METADATA_BOX_KEY.encode(),
                )
            ],
            suggested_params=sp,
            note=note,
        ),
    )
