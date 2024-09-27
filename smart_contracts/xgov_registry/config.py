from typing import Final
from ..proposal.config import (
    GLOBAL_BYTES as PROPOSAL_GLOBAL_BYTES,
    GLOBAL_UINTS as PROPOSAL_GLOBAL_UINTS
)

# State Schema
GLOBAL_BYTES: Final[int] = 6
GLOBAL_UINTS: Final[int] = 30
LOCAL_BYTES: Final[int] = 0
LOCAL_UINTS: Final[int] = 0

# TODO: get the actual required pages for the proposal contract, 1 extra page is just a guess
PROPOSAL_MBR: Final[int] = 200_000 + (28_500 * PROPOSAL_GLOBAL_UINTS) + (50_000 * PROPOSAL_GLOBAL_BYTES)

# Global state keys
GS_KEY_XGOV_MANAGER: Final[bytes] = b"xgov_manager"
GS_KEY_XGOV_PAYOR: Final[bytes] = b"xgov_payor"
GS_KEY_KYC_PROVIDER: Final[bytes] = b"kyc_provider"
GS_KEY_COMMITTEE_MANAGER: Final[bytes] = b"committee_manager"
GS_KEY_COMMITTEE_PUBLISHER: Final[bytes] = b"committee_publisher"
GS_KEY_XGOV_MIN_BALANCE: Final[bytes] = b"xgov_min_balance"
GS_KEY_PROPOSER_FEE: Final[bytes] = b"proposer_fee"
GS_KEY_PROPOSAL_FEE: Final[bytes] = b"proposal_fee"
GS_KEY_PROPOSAL_PUBLISHING_BPS: Final[bytes] = b"proposal_publishing_bps"
GS_KEY_PROPOSAL_COMMITMENT_BPS: Final[bytes] = b"proposal_commitment_bps"
GS_KEY_MIN_REQUESTED_AMOUNT: Final[bytes] = b"min_requested_amount"
GS_KEY_MAX_REQUESTED_AMOUNT_SMALL: Final[bytes] = b"max_requested_amount_small"
GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM: Final[bytes] = b"max_requested_amount_medium"
GS_KEY_MAX_REQUESTED_AMOUNT_LARGE: Final[bytes] = b"max_requested_amount_large"
GS_KEY_DISCUSSION_DURATION_SMALL: Final[bytes] = b"discussion_duration_small"
GS_KEY_DISCUSSION_DURATION_MEDIUM: Final[bytes] = b"discussion_duration_medium"
GS_KEY_DISCUSSION_DURATION_LARGE: Final[bytes] = b"discussion_duration_large"
GS_KEY_DISCUSSION_DURATION_XLARGE: Final[bytes] = b"discussion_duration_xlarge"
GS_KEY_VOTING_DURATION_SMALL: Final[bytes] = b"voting_duration_small"
GS_KEY_VOTING_DURATION_MEDIUM: Final[bytes] = b"voting_duration_medium"
GS_KEY_VOTING_DURATION_LARGE: Final[bytes] = b"voting_duration_large"
GS_KEY_VOTING_DURATION_XLARGE: Final[bytes] = b"voting_duration_xlarge"
GS_KEY_COOL_DOWN_DURATION: Final[bytes] = b"cool_down_duration"
GS_KEY_QUORUM_SMALL: Final[bytes] = b"quorum_small"
GS_KEY_QUORUM_MEDIUM: Final[bytes] = b"quorum_medium"
GS_KEY_QUORUM_LARGE: Final[bytes] = b"quorum_large"
GS_KEY_WEIGHTED_QUORUM_SMALL: Final[bytes] = b"weighted_quorum_small"
GS_KEY_WEIGHTED_QUORUM_MEDIUM: Final[bytes] = b"weighted_quorum_medium"
GS_KEY_WEIGHTED_QUORUM_LARGE: Final[bytes] = b"weighted_quorum_large"
GS_KEY_OUTSTANDING_FUNDS: Final[bytes] = b"outstanding_funds"
GS_KEY_PENDING_PROPOSALS: Final[bytes] = b"pending_proposals"
GS_KEY_COMMITTEE_ID: Final[bytes] = b"committee_id"
GS_KEY_COMMITTEE_MEMBERS: Final[bytes] = b"committee_members"
GS_KEY_COMMITTEE_VOTES: Final[bytes] = b"committee_votes"