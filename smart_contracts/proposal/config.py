from typing import Final

# State Schema
GLOBAL_BYTES: Final[int] = 5
GLOBAL_UINTS: Final[int] = 13
LOCAL_BYTES: Final[int] = 0
LOCAL_UINTS: Final[int] = 0

# TODO: get the actual required pages for the proposal contract, 1 extra page is just a guess
PROPOSAL_MBR: Final[int] = 200_000 + (28_500 * GLOBAL_UINTS) + (50_000 * GLOBAL_BYTES)

# Global state keys
GS_KEY_PROPOSER: Final[bytes] = b"proposer"
GS_KEY_REGISTRY_APP_ID: Final[bytes] = b"registry_app_id"
GS_KEY_TITLE: Final[bytes] = b"title"
GS_KEY_CID: Final[bytes] = b"cid"
GS_KEY_SUBMISSION_TS: Final[bytes] = b"submission_timestamp"
GS_KEY_FINALIZATION_TS: Final[bytes] = b"finalization_timestamp"
GS_KEY_STATUS: Final[bytes] = b"status"
GS_KEY_CATEGORY: Final[bytes] = b"category"
GS_KEY_FUNDING_TYPE: Final[bytes] = b"funding_type"
GS_KEY_REQUESTED_AMOUNT: Final[bytes] = b"requested_amount"
GS_KEY_LOCKED_AMOUNT: Final[bytes] = b"locked_amount"
GS_KEY_COMMITTEE_ID: Final[bytes] = b"committee_id"
GS_KEY_COMMITTEE_MEMBERS: Final[bytes] = b"committee_members"
GS_KEY_COMMITTEE_VOTES: Final[bytes] = b"committee_votes"
GS_KEY_VOTED_MEMBERS: Final[bytes] = b"voted_members"
GS_KEY_APPROVALS: Final[bytes] = b"approvals"
GS_KEY_REJECTIONS: Final[bytes] = b"rejections"