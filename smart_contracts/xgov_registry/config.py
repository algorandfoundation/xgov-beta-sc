from typing import Final

# State Schema
#  Total of 64 (max out global state) to allow updates of the contract without breaking
GLOBAL_BYTES: Final[int] = 28
GLOBAL_UINTS: Final[int] = 36
LOCAL_BYTES: Final[int] = 0
LOCAL_UINTS: Final[int] = 0

# Global state keys
GS_KEY_XGOV_MANAGER: Final[bytes] = b"xgov_manager"
GS_KEY_XGOV_SUBSCRIBER: Final[bytes] = b"xgov_subscriber"
GS_KEY_XGOV_PAYOR: Final[bytes] = b"xgov_payor"
GS_KEY_XGOV_COUNCIL: Final[bytes] = b"xgov_council"
GS_KEY_KYC_PROVIDER: Final[bytes] = b"kyc_provider"
GS_KEY_COMMITTEE_MANAGER: Final[bytes] = b"committee_manager"
GS_KEY_XGOV_BACKEND: Final[bytes] = b"xgov_backend"
GS_KEY_XGOV_FEE: Final[bytes] = b"xgov_fee"
GS_KEY_XGOVS: Final[bytes] = b"xgovs"
GS_KEY_PAUSED_REGISTRY: Final[bytes] = b"paused_registry"
GS_KEY_PAUSED_PROPOSALS: Final[bytes] = b"paused_proposals"
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
GS_KEY_QUORUM_SMALL: Final[bytes] = b"quorum_small"
GS_KEY_QUORUM_MEDIUM: Final[bytes] = b"quorum_medium"
GS_KEY_QUORUM_LARGE: Final[bytes] = b"quorum_large"
GS_KEY_WEIGHTED_QUORUM_SMALL: Final[bytes] = b"weighted_quorum_small"
GS_KEY_WEIGHTED_QUORUM_MEDIUM: Final[bytes] = b"weighted_quorum_medium"
GS_KEY_WEIGHTED_QUORUM_LARGE: Final[bytes] = b"weighted_quorum_large"
GS_KEY_OUTSTANDING_FUNDS: Final[bytes] = b"outstanding_funds"
GS_KEY_PENDING_PROPOSALS: Final[bytes] = b"pending_proposals"
GS_KEY_REQUEST_ID: Final[bytes] = b"request_id"
GS_KEY_COMMITTEE_ID: Final[bytes] = b"committee_id"
GS_KEY_COMMITTEE_MEMBERS: Final[bytes] = b"committee_members"
GS_KEY_COMMITTEE_VOTES: Final[bytes] = b"committee_votes"

XGOV_BOX_MAP_PREFIX: Final[bytes] = b"x"
REQUEST_BOX_MAP_PREFIX: Final[bytes] = b"r"
PROPOSER_BOX_MAP_PREFIX: Final[bytes] = b"p"
