# Constants

from typing import Final

CID_LENGTH: Final[int] = 59
COMMITTEE_ID_LENGTH: Final[int] = 32
TITLE_MAX_BYTES: Final[int] = 123

BPS: Final[int] = 10_000

# These are placeholders, the actual values will be set by the registry SC
# TODO delete after we have the registry SC
PROPOSAL_COMMITMENT_BPS: Final[int] = 100
MIN_REQUESTED_AMOUNT: Final[int] = 10_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_SMALL: Final[int] = 50_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_MEDIUM: Final[int] = 250_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_LARGE: Final[int] = 500_000_000_000  # amount in microAlgos
PUBLISHING_FEE: Final[int] = 5_000_000  # amount in microAlgos
DISCUSSION_DURATION_SMALL: Final[int] = 604_800  # 1 week in seconds
DISCUSSION_DURATION_MEDIUM: Final[int] = 1_209_600  # 2 weeks in seconds
DISCUSSION_DURATION_LARGE: Final[int] = 1_814_400  # 3 weeks in seconds
