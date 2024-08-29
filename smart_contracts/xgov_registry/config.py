from typing import Final

# State Schema
GLOBAL_BYTES: Final[int] = 0
GLOBAL_UINTS: Final[int] = 0
LOCAL_BYTES: Final[int] = 0
LOCAL_UINTS: Final[int] = 0

# Global state keys
GS_KEY_PROPOSAL_COMMITMENT_BPS: Final[bytes] = b"proposal_commitment"
GS_KEY_MIN_REQUESTED_AMOUNT: Final[bytes] = b"minimum_requested_amount"
GS_KEY_MAX_REQUESTED_AMOUNT_SMALL: Final[bytes] = b"maximum_requested_amount_small"
GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM: Final[bytes] = b"maximum_requested_amount_medium"
GS_KEY_MAX_REQUESTED_AMOUNT_LARGE: Final[bytes] = b"maximum_requested_amount_large"
GS_KEY_PUBLISHING_FEE_BPS: Final[bytes] = b"publishing_fee"
GS_KEY_DISCUSSION_DURATION_SMALL: Final[bytes] = b"discussion_duration_small"
GS_KEY_DISCUSSION_DURATION_MEDIUM: Final[bytes] = b"discussion_duration_medium"
GS_KEY_DISCUSSION_DURATION_LARGE: Final[bytes] = b"discussion_duration_large"
GS_KEY_COMMITTEE_PUBLISHER: Final[bytes] = b"committee_publisher"
GS_KEY_PROPOSAL_FEE: Final[bytes] = b"proposal_fee"
