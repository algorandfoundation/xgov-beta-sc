from typing import Final

# State Schema
GLOBAL_BYTES: Final[int] = 1
GLOBAL_UINTS: Final[int] = 2
LOCAL_BYTES: Final[int] = 0
LOCAL_UINTS: Final[int] = 0

# Global state keys
GS_KEY_ADMIN: Final[bytes] = b"admin"
GS_KEY_REGISTRY_APP_ID: Final[bytes] = b"registry_app_id"
GS_KEY_MEMBER_COUNT: Final[bytes] = b"member_count"

# Boxes
MEMBERS_KEY_PREFIX: Final[str] = "M"
VOTES_KEY_PREFIX: Final[str] = "V"

MEMBER_BOX_KEY_SIZE: Final[int] = 33  # 1 byte for prefix + 32 bytes for address
MEMBER_BOX_VALUE_SIZE: Final[int] = 0

VOTES_BOX_KEY_SIZE: Final[int] = 9  # 1 byte for prefix + 8 bytes for proposal ID