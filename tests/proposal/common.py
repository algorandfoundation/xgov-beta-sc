from typing import Type

from algokit_utils import LogicError

from smart_contracts.proposal.constants import (
    BPS,
    MIN_REQUESTED_AMOUNT,
    PROPOSAL_COMMITMENT_BPS,
)


def get_locked_amount(requested_amount: int) -> int:
    return PROPOSAL_COMMITMENT_BPS * requested_amount // BPS


REQUESTED_AMOUNT = MIN_REQUESTED_AMOUNT
LOCKED_AMOUNT = get_locked_amount(REQUESTED_AMOUNT)

logic_error_type: Type[LogicError] = LogicError

INITIAL_FUNDS = 10_000_000_000
