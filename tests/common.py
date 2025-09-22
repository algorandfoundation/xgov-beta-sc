import dataclasses
from typing import Final

from algokit_utils import AlgoAmount, SigningAccount, LogicError

from smart_contracts.proposal.constants import (
    BPS,
    COMMITTEE_ID_LENGTH,
)

logic_error_type: type[LogicError] = LogicError


def relative_to_absolute_amount(amount: int, fraction_in_bps: int) -> int:
    return amount * fraction_in_bps // BPS


DEFAULT_COMMITTEE_ID = b"\x01" * COMMITTEE_ID_LENGTH
DEFAULT_COMMITTEE_MEMBERS = 20
DEFAULT_MEMBER_VOTES = 10
DEFAULT_COMMITTEE_VOTES = DEFAULT_COMMITTEE_MEMBERS * DEFAULT_MEMBER_VOTES

INITIAL_FUNDS: Final[AlgoAmount] = AlgoAmount(algo=1_000)


@dataclasses.dataclass
class CommitteeMember:
    account: SigningAccount
    votes: int
