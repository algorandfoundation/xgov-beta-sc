from algokit_utils import LogicError, AlgoAmount, SigningAccount, AlgorandClient, PaymentParams, CommonAppCallParams
from algosdk.constants import MIN_TXN_FEE

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient, OpenArgs, ProposalComposer, UploadMetadataArgs, UnassignVotersArgs, AssignVotersArgs,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, FinalizeProposalArgs
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.proposal.config import GLOBAL_BYTES, GLOBAL_UINTS
from smart_contracts.proposal.enums import (
    FUNDING_CATEGORY_NULL,
    FUNDING_CATEGORY_SMALL,
    FUNDING_NULL,
    FUNDING_PROACTIVE,
    STATUS_APPROVED,
    STATUS_BLOCKED,
    STATUS_DRAFT,
    STATUS_EMPTY,
    STATUS_FUNDED,
    STATUS_REJECTED,
    STATUS_REVIEWED,
    STATUS_SUBMITTED,
    STATUS_VOTING,
)
from smart_contracts.xgov_registry.config import (
    MIN_REQUESTED_AMOUNT,
    OPEN_PROPOSAL_FEE,
    PROPOSAL_COMMITMENT_BPS,
)
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    relative_to_absolute_amount,
)
from tests.utils import time_warp

logic_error_type: type[LogicError] = LogicError

MAX_UPLOAD_PAYLOAD_SIZE = 2041  # 2048 - 4 bytes (method selector) - 2 bytes (payload length) - 1 byte (boolean flag)

PROPOSAL_MBR = 200_000 + (28_500 * GLOBAL_UINTS) + (50_000 * GLOBAL_BYTES)
PROPOSAL_PARTIAL_FEE = OPEN_PROPOSAL_FEE - PROPOSAL_MBR

PROPOSAL_TITLE = "Test Proposal"
METADATA_B64 = "TUVUQURBVEE="
DEFAULT_FOCUS = 42


def get_locked_amount(requested_amount: AlgoAmount) -> AlgoAmount:
    return AlgoAmount(micro_algo=relative_to_absolute_amount(requested_amount.amount_in_micro_algo, PROPOSAL_COMMITMENT_BPS))


REQUESTED_AMOUNT = AlgoAmount(micro_algo=MIN_REQUESTED_AMOUNT)
LOCKED_AMOUNT = get_locked_amount(REQUESTED_AMOUNT)


def assert_proposal_global_state(
    proposal_client: ProposalClient,
    *,
    proposer_address: str,
    registry_app_id: int,
    status: int = STATUS_EMPTY,
    finalized: bool = False,
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
    global_state = proposal_client.state.global_state
    assert global_state.proposer == proposer_address
    assert global_state.title == title
    assert global_state.status == status
    assert global_state.finalized == finalized
    assert global_state.funding_category == funding_category
    assert global_state.focus == focus
    assert global_state.funding_type == funding_type
    assert global_state.requested_amount == requested_amount
    assert global_state.locked_amount == locked_amount
    assert bytes(global_state.committee_id) == committee_id
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
        assert global_state.open_ts == 0
    else:
        assert global_state.open_ts > 0

    if status >= STATUS_SUBMITTED:
        assert global_state.submission_ts > 0
    else:
        assert global_state.submission_ts == 0

    if status >= STATUS_VOTING:
        assert global_state.vote_open_ts > 0
    else:
        assert global_state.vote_open_ts == 0


def get_default_params_for_status(status: int, overrides: dict, *, finalized: bool) -> dict:  # type: ignore
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
        "voters_count": 0 if finalized else DEFAULT_COMMITTEE_MEMBERS,
        "assigned_votes": 0 if finalized else 10 * DEFAULT_COMMITTEE_MEMBERS,
    }

    # Specific status defaults, with shared defaults included where needed
    status_defaults = {
        STATUS_DRAFT: {
            "status": STATUS_DRAFT,
            **committee_defaults,
            "locked_amount": 0 if finalized else LOCKED_AMOUNT,
        },
        STATUS_SUBMITTED: {"status": STATUS_SUBMITTED, **committee_defaults},
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
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    status: int,
    *,
    finalized: bool = False,
    **overrides,  # noqa: ANN003
) -> None:
    params = get_default_params_for_status(status, overrides, finalized=finalized)  # type: ignore
    assert_proposal_global_state(
        proposal_client,
        proposer_address=proposer_address,
        registry_app_id=registry_app_id,
        finalized=finalized,
        **params,  # type: ignore
    )


def assert_empty_proposal_global_state(
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    *,
    finalized: bool = False,
) -> None:
    assert_proposal_global_state(
        proposal_client,
        proposer_address=proposer_address,
        registry_app_id=registry_app_id,
        finalized=finalized,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_members=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
    )


def assert_draft_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    *,
    finalized: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_DRAFT, finalized=finalized, **kwargs  # type: ignore
    )


def assert_voting_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_VOTING, **kwargs  # type: ignore
    )


def assert_approved_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_APPROVED, **kwargs  # type: ignore
    )


def assert_rejected_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    *,
    finalized: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_REJECTED, finalized=finalized, **kwargs  # type: ignore
    )


def assert_final_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_SUBMITTED, **kwargs  # type: ignore
    )


def assert_reviewed_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_REVIEWED, **kwargs  # type: ignore
    )


def assert_blocked_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    *,
    finalized: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_BLOCKED, finalized=finalized, **kwargs  # type: ignore
    )


def assert_funded_proposal_global_state(  # type: ignore
    proposal_client: ProposalClient,
    proposer_address: str,
    registry_app_id: int,
    *,
    finalized: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    assert_proposal_with_status(
        proposal_client, proposer_address, registry_app_id, STATUS_FUNDED, finalized=finalized, **kwargs  # type: ignore
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


def open_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    *,
    payment_sender: SigningAccount = None,  # type: ignore
    payment_receiver: str = "",
    title: str = PROPOSAL_TITLE,
    metadata: bytes = b"METADATA",
    funding_type: int = FUNDING_PROACTIVE,
    focus: int = DEFAULT_FOCUS,
    requested_amount: AlgoAmount = REQUESTED_AMOUNT,
    locked_amount: AlgoAmount = LOCKED_AMOUNT,
) -> None:
    if payment_sender is None:
        payment_sender = proposer

    if payment_receiver == "":
        payment_receiver = proposal_client.app_address

    composer = proposal_client.new_group().open(
        args=OpenArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=payment_sender.address,
                    receiver=payment_receiver,
                    amount=locked_amount,
                ),
            ),
            title=title,
            funding_type=funding_type,
            focus=focus,
            requested_amount=requested_amount.amount_in_micro_algo,
        ),
        params = CommonAppCallParams(signer=proposer.signer)
    )

    if metadata != b"":
        upload_metadata(
            composer,
            proposer,
            metadata,
        )

    composer.send()


def upload_metadata(
    proposal_client_composer: ProposalComposer,
    proposer: SigningAccount,
    metadata: bytes,
) -> None:

    for i in range((len(metadata) // MAX_UPLOAD_PAYLOAD_SIZE) + 1):
        proposal_client_composer.upload_metadata(
            args=UploadMetadataArgs(
                payload=metadata[
                        i * MAX_UPLOAD_PAYLOAD_SIZE: (i + 1) * MAX_UPLOAD_PAYLOAD_SIZE
                        ],
                is_first_in_group=i == 0,
            ),
            params = CommonAppCallParams(signer=proposer.signer)
        )


def unassign_voters(
    proposal_client_composer: ProposalComposer,
    committee_members: list[SigningAccount],
    xgov_daemon: SigningAccount,
    bulks: int = 8,
) -> None:
    proposal_client_composer.unassign_voters(
        args=UnassignVotersArgs(voters=[cm.address for cm in committee_members[: bulks - 1]],),
        params = CommonAppCallParams(signer=xgov_daemon.signer)
    )
    rest_of_committee_members = committee_members[bulks - 1 :]
    for i in range(1 + len(rest_of_committee_members) // bulks):
        proposal_client_composer.unassign_voters(
            args=UnassignVotersArgs(voters=[cm.address for cm in rest_of_committee_members[i * bulks: (i + 1) * bulks]]),
            params = CommonAppCallParams(signer=xgov_daemon.signer)
        )


def assign_voters(
    proposal_client_composer: ProposalComposer,
    committee_members: list[SigningAccount],
    xgov_daemon: SigningAccount,
    bulks: int = 8,
) -> None:
    proposal_client_composer.assign_voters(
        args=AssignVotersArgs(voters=[(cm.address, 10) for cm in committee_members[: bulks - 1]]),
        params = CommonAppCallParams(signer=xgov_daemon.signer)
    )
    rest_of_committee_members = committee_members[bulks - 1 :]
    for i in range(1 + len(rest_of_committee_members) // bulks):
        proposal_client_composer.assign_voters(
            args=AssignVotersArgs(voters=[(cm.address, 10) for cm in rest_of_committee_members[i * bulks: (i + 1) * bulks]]),
            params = CommonAppCallParams(signer=xgov_daemon.signer)
        )


def finalize_proposal(
    xgov_registry_client: XgovRegistryMockClient,
    proposal_app_id: int,
    xgov_daemon: SigningAccount,
) -> None:
    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(proposal_id=proposal_app_id,),
        params = CommonAppCallParams(signer=xgov_daemon.signer)
    )


def submit_proposal(
    proposal_client: ProposalClient,
    xgov_registry_client: XgovRegistryMockClient | XGovRegistryClient,
    proposer: SigningAccount,
    should_time_warp: bool = True,  # noqa: FBT001, FBT002
) -> None:
    if should_time_warp:
        reg_gs = xgov_registry_client.state.global_state
        discussion_duration = reg_gs.discussion_duration_large

        open_ts = proposal_client.state.global_state.open_ts
        if open_ts > 0:  # not empty proposal
            time_warp(open_ts + discussion_duration)  # so we could actually submit

    proposal_client.send.submit(
        params=CommonAppCallParams(sender=proposer.address, static_fee=AlgoAmount(micro_algo=MIN_TXN_FEE*2))
    )
