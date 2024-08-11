# Constants

from typing import Final

CID_LENGTH: Final[int] = 59
COMMITTEE_ID_LENGTH: Final[int] = 32
TITLE_MAX_BYTES: Final[int] = 123

BPS: Final[int] = 10000

# These are placeholders, the actual values will be set by the registry SC
# TODO delete after we have the registry SC
PROPOSAL_COMMITMENT_BPS: Final[int] = 100
MIN_REQUESTED_AMOUNT: Final[int] = 10_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_SMALL: Final[int] = 50_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_MEDIUM: Final[int] = 250_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_LARGE: Final[int] = 500_000_000_000  # amount in microAlgos
