from typing import Final

from algokit_utils import AlgoAmount

from smart_contracts.proposal.constants import (
    BPS,
    COMMITTEE_ID_LENGTH,
)


def relative_to_absolute_amount(amount: int, fraction_in_bps: int) -> int:
    return amount * fraction_in_bps // BPS


DEFAULT_COMMITTEE_ID = b"\x01" * COMMITTEE_ID_LENGTH
DEFAULT_COMMITTEE_MEMBERS = 20
DEFAULT_COMMITTEE_VOTES = 200

INITIAL_FUNDS: Final[AlgoAmount] = AlgoAmount(algo=1_000)
