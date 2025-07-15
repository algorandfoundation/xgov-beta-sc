from algokit_utils import LogicError
from algosdk.util import algos_to_microalgos

from smart_contracts.proposal.constants import (
    BPS,
    COMMITTEE_ID_LENGTH,
)

logic_error_type: type[LogicError] = LogicError


def relative_to_absolute_amount(amount: int, fraction_in_bps: int) -> int:
    return amount * fraction_in_bps // BPS


DEFAULT_COMMITTEE_ID = b"\x01" * COMMITTEE_ID_LENGTH
DEFAULT_COMMITTEE_MEMBERS = 20
DEFAULT_COMMITTEE_VOTES = 200

INITIAL_FUNDS: int = algos_to_microalgos(10_000)  # type: ignore[no-untyped-call]
