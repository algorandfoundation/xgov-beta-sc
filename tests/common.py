from algokit_utils import LogicError
from algosdk.encoding import decode_address

from smart_contracts.proposal.config import VOTER_BOX_KEY_PREFIX
from smart_contracts.proposal.constants import (
    BPS,
    COMMITTEE_ID_LENGTH,
)
from smart_contracts.xgov_registry_mock.config import (
    MIN_REQUESTED_AMOUNT,
    PROPOSAL_COMMITMENT_BPS,
)

logic_error_type: type[LogicError] = LogicError


def relative_to_absolute_amount(amount: int, fraction_in_bps: int) -> int:
    return amount * fraction_in_bps // BPS


def get_locked_amount(requested_amount: int) -> int:
    return relative_to_absolute_amount(requested_amount, PROPOSAL_COMMITMENT_BPS)


def get_voter_box_key(voter_address: str) -> bytes:
    return VOTER_BOX_KEY_PREFIX.encode() + decode_address(voter_address)  # type: ignore


METADATA_B64 = "TUVUQURBVEE="

DEFAULT_COMMITTEE_ID = b"\x01" * COMMITTEE_ID_LENGTH
DEFAULT_COMMITTEE_MEMBERS = 20
DEFAULT_COMMITTEE_VOTES = 200

REQUESTED_AMOUNT = MIN_REQUESTED_AMOUNT
LOCKED_AMOUNT = get_locked_amount(REQUESTED_AMOUNT)
PROPOSAL_TITLE = "Test Proposal"
DEFAULT_FOCUS = 42
