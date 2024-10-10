from typing import Type

from algokit_utils import LogicError
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.encoding import encode_address

from smart_contracts.artifacts.proposal.client import GlobalState
from smart_contracts.proposal.constants import (
    BPS,
)
from smart_contracts.proposal.enums import (
    CATEGORY_NULL,
    FUNDING_NULL,
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

logic_error_type: Type[LogicError] = LogicError

INITIAL_FUNDS = 10_000_000_000

DEFAULT_COMMITTEE_ID = b"\x01" * 32
DEFAULT_COMMITTEE_MEMBERS = 10
DEFAULT_COMMITTEE_VOTES = 100


def assert_proposal_global_state(
    global_state: GlobalState,
    *,
    proposer_address: str,
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
    registry_app_id: int = 0,
    assigned_votes: int = 0,
    voters_count: int = 0,
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


def assert_account_balance(
    algorand_client: AlgorandClient, address: str, expected_balance: int
) -> None:
    assert (
        algorand_client.account.get_information(address)["amount"] == expected_balance  # type: ignore
    )
