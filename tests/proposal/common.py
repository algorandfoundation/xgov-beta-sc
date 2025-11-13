import dataclasses

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    PaymentParams,
    SigningAccount,
)
from algosdk.constants import MIN_TXN_FEE
from algosdk.encoding import decode_address

import smart_contracts.proposal.enums
from smart_contracts.artifacts.proposal.proposal_client import (
    AssignVotersArgs,
    OpenArgs,
    ProposalClient,
    ProposalComposer,
    UnassignVotersArgs,
    UploadMetadataArgs,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    FinalizeProposalArgs,
    XgovRegistryMockClient,
)
from smart_contracts.proposal.config import (
    GLOBAL_BYTES,
    GLOBAL_UINTS,
    VOTER_BOX_KEY_PREFIX,
)
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
from smart_contracts.xgov_registry import config as reg_cfg
from smart_contracts.xgov_registry.constants import PROPOSAL_APPROVAL_PAGES
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    DEFAULT_MEMBER_VOTES,
    CommitteeMember,
    relative_to_absolute_amount,
)
from tests.utils import time_warp

MAX_UPLOAD_PAYLOAD_SIZE = 2041  # 2048 - 4 bytes (method selector) - 2 bytes (payload length) - 1 byte (boolean flag)

MBR_PER_APP_PAGE = 100_000
MBR_PER_SCHEMA_ENTRY = 25_000
MBR_PER_UINT_ENTRY = MBR_PER_SCHEMA_ENTRY + 3_500
MBR_PER_BYTES_ENTRY = MBR_PER_SCHEMA_ENTRY + 25_000

PROPOSAL_PAGES = PROPOSAL_APPROVAL_PAGES + 1
PROPOSAL_MBR = (
    PROPOSAL_PAGES * MBR_PER_APP_PAGE
    + (MBR_PER_UINT_ENTRY * GLOBAL_UINTS)
    + (MBR_PER_BYTES_ENTRY * GLOBAL_BYTES)
)
PROPOSAL_PARTIAL_FEE = reg_cfg.OPEN_PROPOSAL_FEE - PROPOSAL_MBR

PROPOSAL_TITLE = "Test Proposal"
METADATA_B64 = "TUVUQURBVEE="
DEFAULT_FOCUS = 42


@dataclasses.dataclass
class ProposalRegistryValues:
    discussion_duration: int = 0
    voting_duration: int = 0
    members_quorum: int = 0
    votes_quorum: int = 0


def get_voter_box_key(voter_address: str) -> bytes:
    return VOTER_BOX_KEY_PREFIX.encode() + decode_address(voter_address)  # type: ignore


def get_locked_amount(requested_amount: AlgoAmount) -> AlgoAmount:
    return AlgoAmount(
        micro_algo=relative_to_absolute_amount(
            requested_amount.amount_in_micro_algo, reg_cfg.PROPOSAL_COMMITMENT_BPS
        )
    )


REQUESTED_AMOUNT = AlgoAmount(micro_algo=reg_cfg.MIN_REQUESTED_AMOUNT)
LOCKED_AMOUNT = get_locked_amount(REQUESTED_AMOUNT)


def get_proposal_values_from_registry(
    proposal_client: ProposalClient,
) -> ProposalRegistryValues | None:
    global_state = proposal_client.state.global_state
    funding_category = global_state.funding_category
    committee_members = global_state.committee_members
    committee_votes = global_state.committee_votes
    match funding_category:
        case smart_contracts.proposal.enums.FUNDING_CATEGORY_SMALL:
            return ProposalRegistryValues(
                discussion_duration=reg_cfg.DISCUSSION_DURATION_SMALL,
                voting_duration=reg_cfg.VOTING_DURATION_SMALL,
                members_quorum=relative_to_absolute_amount(
                    committee_members, reg_cfg.QUORUM_SMALL
                ),
                votes_quorum=relative_to_absolute_amount(
                    committee_votes, reg_cfg.WEIGHTED_QUORUM_SMALL
                ),
            )
        case smart_contracts.proposal.enums.FUNDING_CATEGORY_MEDIUM:
            return ProposalRegistryValues(
                discussion_duration=reg_cfg.DISCUSSION_DURATION_MEDIUM,
                voting_duration=reg_cfg.VOTING_DURATION_MEDIUM,
                members_quorum=relative_to_absolute_amount(
                    committee_members, reg_cfg.QUORUM_MEDIUM
                ),
                votes_quorum=relative_to_absolute_amount(
                    committee_votes, reg_cfg.WEIGHTED_QUORUM_MEDIUM
                ),
            )
        case smart_contracts.proposal.enums.FUNDING_CATEGORY_LARGE:
            return ProposalRegistryValues(
                discussion_duration=reg_cfg.DISCUSSION_DURATION_LARGE,
                voting_duration=reg_cfg.VOTING_DURATION_LARGE,
                members_quorum=relative_to_absolute_amount(
                    committee_members, reg_cfg.QUORUM_LARGE
                ),
                votes_quorum=relative_to_absolute_amount(
                    committee_votes, reg_cfg.WEIGHTED_QUORUM_LARGE
                ),
            )
        case _:
            return None


def quorums_reached(
    proposal_client: ProposalClient,
    voted_members: int,
    total_votes: int,
    *,
    plebiscite: bool = False,
) -> bool:
    proposal_values = proposal_client.state.global_state
    proposal_registry_values = get_proposal_values_from_registry(proposal_client)
    if plebiscite:
        return (
            voted_members == proposal_values.committee_members
            and total_votes == proposal_values.committee_votes
        )
    else:
        return (
            voted_members >= proposal_registry_values.members_quorum  # type: ignore
            and total_votes >= proposal_registry_values.votes_quorum  # type: ignore
        )


def members_for_both_quorums(
    proposal_client: ProposalClient, committee: list[CommitteeMember]
) -> int:
    for cm in committee:
        assert (
            cm.votes == DEFAULT_MEMBER_VOTES
        )  # Required to compute the number of voting members to reach both quorums
    proposal_registry_values = get_proposal_values_from_registry(proposal_client)
    weighted_quorum_members = (
        proposal_registry_values.votes_quorum // DEFAULT_MEMBER_VOTES  # type: ignore
    )
    return max(proposal_registry_values.members_quorum, weighted_quorum_members)  # type: ignore


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
    assert global_state.assigned_members == voters_count

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

    if status > STATUS_REJECTED or global_state.finalized:
        assert not global_state.assigned_members
        assert not global_state.assigned_votes


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
            "voters_count": DEFAULT_COMMITTEE_MEMBERS,
            "assigned_votes": DEFAULT_COMMITTEE_MEMBERS,
        },
        STATUS_APPROVED: {
            "status": STATUS_APPROVED,
            **committee_defaults,
        },
        STATUS_REJECTED: {
            "status": STATUS_REJECTED,
            **committee_defaults,
            "locked_amount": 0,
        },
        STATUS_REVIEWED: {
            "status": STATUS_REVIEWED,
            **committee_defaults,
            "locked_amount": 0,
        },
        STATUS_BLOCKED: {
            "status": STATUS_BLOCKED,
            **committee_defaults,
            "locked_amount": 0,
        },
        STATUS_FUNDED: {
            "status": STATUS_FUNDED,
            **committee_defaults,
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
    print(algorand_client.account.get_information(address).amount, expected_balance)
    assert algorand_client.account.get_information(address).amount == AlgoAmount(
        micro_algo=expected_balance
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

    args = OpenArgs(
        payment=algorand_client.create_transaction.payment(
            PaymentParams(
                sender=payment_sender.address,
                signer=payment_sender.signer,
                receiver=payment_receiver,
                amount=locked_amount,
            ),
        ),
        title=title,
        funding_type=funding_type,
        focus=focus,
        requested_amount=requested_amount.amount_in_micro_algo,
    )

    params = CommonAppCallParams(sender=proposer.address, signer=proposer.signer)

    if metadata != b"":
        composer = proposal_client.new_group().open(
            args=args,
            params=params,
        )

        if metadata != b"":
            upload_metadata(
                composer,
                proposer,
                metadata,
            )

        composer.send()
    else:
        proposal_client.send.open(
            args=args,
            params=params,
        )


def upload_metadata(
    proposal_client_composer: ProposalComposer,
    proposer: SigningAccount,
    metadata: bytes,
) -> None:

    for i in range((len(metadata) // MAX_UPLOAD_PAYLOAD_SIZE) + 1):
        proposal_client_composer.upload_metadata(
            args=UploadMetadataArgs(
                payload=metadata[
                    i * MAX_UPLOAD_PAYLOAD_SIZE : (i + 1) * MAX_UPLOAD_PAYLOAD_SIZE
                ],
                is_first_in_group=i == 0,
            ),
            params=CommonAppCallParams(sender=proposer.address, signer=proposer.signer),
        )


def unassign_voters(
    proposal_client_composer: ProposalComposer,
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    bulks: int = 8,
) -> None:
    proposal_client_composer.unassign_voters(
        args=UnassignVotersArgs(
            voters=[cm.account.address for cm in committee[: bulks - 1]],
        ),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, signer=xgov_daemon.signer
        ),
    )
    rest_of_committee_members = committee[bulks - 1 :]
    for i in range(1 + len(rest_of_committee_members) // bulks):
        proposal_client_composer.unassign_voters(
            args=UnassignVotersArgs(
                voters=[
                    cm.account.address
                    for cm in rest_of_committee_members[i * bulks : (i + 1) * bulks]
                ]
            ),
            params=CommonAppCallParams(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                note=i.to_bytes(4, "big"),
            ),
        )


def assign_voters(
    proposal_client_composer: ProposalComposer,
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    bulks: int = 8,
) -> None:
    proposal_client_composer.assign_voters(
        args=AssignVotersArgs(
            voters=[(cm.account.address, cm.votes) for cm in committee[: bulks - 1]]
        ),
        params=CommonAppCallParams(sender=xgov_daemon.address),
    )
    rest_of_committee_members = committee[bulks - 1 :]
    for i in range(1 + len(rest_of_committee_members) // bulks):
        proposal_client_composer.assign_voters(
            args=AssignVotersArgs(
                voters=[
                    (cm.account.address, cm.votes)
                    for cm in rest_of_committee_members[i * bulks : (i + 1) * bulks]
                ]
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address),
        )


def finalize_proposal(
    xgov_registry_client: XgovRegistryMockClient,
    proposal_app_id: int,
    xgov_daemon: SigningAccount,
    static_fee: AlgoAmount = AlgoAmount(micro_algo=MIN_TXN_FEE * 3),  # noqa: B008
) -> None:
    xgov_registry_client.send.finalize_proposal(
        args=FinalizeProposalArgs(
            proposal_app=proposal_app_id,
        ),
        params=CommonAppCallParams(
            sender=xgov_daemon.address, signer=xgov_daemon.signer, static_fee=static_fee
        ),
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
        params=CommonAppCallParams(
            sender=proposer.address, static_fee=AlgoAmount(micro_algo=MIN_TXN_FEE * 2)
        )
    )


def end_voting_session_time(proposal_client: ProposalClient) -> None:
    voting_duration = get_proposal_values_from_registry(proposal_client).voting_duration
    vote_open_ts = proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)


def scrutinize_proposal(
    scrutinizer: SigningAccount,
    proposal_client: ProposalClient,
    scrutiny_fee: AlgoAmount,
) -> None:
    end_voting_session_time(proposal_client)
    proposal_client.send.scrutiny(
        params=CommonAppCallParams(sender=scrutinizer.address, static_fee=scrutiny_fee)
    )
