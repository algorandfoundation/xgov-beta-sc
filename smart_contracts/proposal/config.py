from typing import Final

# State Schema
GLOBAL_BYTES: Final[int] = 3
GLOBAL_UINTS: Final[int] = 27
LOCAL_BYTES: Final[int] = 0
LOCAL_UINTS: Final[int] = 0

# Global Bytes Keys
GS_KEY_PROPOSER: Final[bytes] = b"proposer"
GS_KEY_TITLE: Final[bytes] = b"title"

# Global UInt Keys
GS_KEY_REGISTRY_APP_ID: Final[bytes] = b"registry_app_id"
GS_KEY_METADATA_UPLOADED: Final[bytes] = b"metadata_uploaded"
GS_KEY_OPEN_TS: Final[bytes] = b"open_timestamp"
GS_KEY_SUBMISSION_TS: Final[bytes] = b"submission_timestamp"
GS_KEY_VOTE_OPEN_TS: Final[bytes] = b"vote_opening_timestamp"
GS_KEY_STATUS: Final[bytes] = b"status"
GS_KEY_FINALIZED: Final[bytes] = b"finalized"
GS_KEY_FUNDING_CATEGORY: Final[bytes] = b"funding_category"
GS_KEY_FOCUS: Final[bytes] = b"focus"
GS_KEY_FUNDING_TYPE: Final[bytes] = b"funding_type"
GS_KEY_REQUESTED_AMOUNT: Final[bytes] = b"requested_amount"
GS_KEY_LOCKED_AMOUNT: Final[bytes] = b"locked_amount"
GS_KEY_QUORUM_THRESHOLD: Final[bytes] = b"quorum_threshold"
GS_KEY_WEIGHTED_QUORUM_THRESHOLD: Final[bytes] = b"weighted_quorum_threshold"
GS_KEY_DISCUSSION_DURATION: Final[bytes] = b"discussion_duration"
GS_KEY_VOTING_DURATION: Final[bytes] = b"voting_duration"
GS_KEY_ASSIGNED_MEMBERS: Final[bytes] = b"assigned_members"
GS_KEY_ASSIGNED_VOTES: Final[bytes] = b"assigned_votes"
GS_KEY_VOTED_MEMBERS: Final[bytes] = b"voted_members"
GS_KEY_BOYCOTTED_MEMBERS: Final[bytes] = b"boycotted_members"
GS_KEY_APPROVALS: Final[bytes] = b"approvals"
GS_KEY_REJECTIONS: Final[bytes] = b"rejections"
GS_KEY_NULLS: Final[bytes] = b"nulls"

# Boxes
VOTER_BOX_KEY_PREFIX: Final[str] = "V"
METADATA_BOX_KEY: Final[str] = "M"
