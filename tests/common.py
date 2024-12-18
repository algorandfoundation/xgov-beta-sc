from smart_contracts.proposal.constants import (
    BPS,
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