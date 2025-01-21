from typing import Final

# TODO: Remove this `config.py` and point directly to the main xGov Registry configuration file

# Default values
PROPOSAL_COMMITMENT_BPS: Final[int] = 100
MIN_REQUESTED_AMOUNT: Final[int] = 10_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_SMALL: Final[int] = 50_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_MEDIUM: Final[int] = 250_000_000_000  # amount in microAlgos
MAX_REQUESTED_AMOUNT_LARGE: Final[int] = 500_000_000_000  # amount in microAlgos
PUBLISHING_FEE_BPS: Final[int] = 500
DISCUSSION_DURATION_SMALL: Final[int] = 604_800  # 1 week in seconds
DISCUSSION_DURATION_MEDIUM: Final[int] = 1_209_600  # 2 weeks in seconds
DISCUSSION_DURATION_LARGE: Final[int] = 1_814_400  # 3 weeks in seconds
COMMITTEE_PUBLISHER: Final[str] = (
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"  # zero address
)
PROPOSAL_FEE: Final[int] = 100_000_000  # amount in microAlgos
COMMITTEE_ID: Final[bytes] = b""
COMMITTEE_MEMBERS: Final[int] = 0
COMMITTEE_VOTES: Final[int] = 0
VOTING_DURATION_SMALL: Final[int] = 604_800  # 1 week in seconds
VOTING_DURATION_MEDIUM: Final[int] = 1_209_600  # 2 weeks in seconds
VOTING_DURATION_LARGE: Final[int] = 1_814_400  # 3 weeks in seconds
QUORUM_SMALL_BPS: Final[int] = 1_000  # 10%
QUORUM_MEDIUM_BPS: Final[int] = 1_500  # 15%
QUORUM_LARGE_BPS: Final[int] = 2_000  # 20%
WEIGHTED_QUORUM_SMALL_BPS: Final[int] = 2_000  # 20%
WEIGHTED_QUORUM_MEDIUM_BPS: Final[int] = 3_000  # 30%
WEIGHTED_QUORUM_LARGE_BPS: Final[int] = 4_000  # 40%
XGOV_REVIEWER: Final[str] = (
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"  # zero address
)
COOL_DOWN_DURATION: Final[int] = 1_209_600  # 2 weeks in seconds
