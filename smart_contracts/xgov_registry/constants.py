# Constants

from typing import Final

BPS: Final[int] = 10_000

# Reference: https://developer.algorand.org/docs/get-details/parameter_tables/

ACCOUNT_MBR: Final[int] = 100_000  # 0.1 ALGO in microAlgos

MAX_PAGES_PER_APP: Final[int] = 4
MAX_GLOBAL_STATE_ENTRIES: Final[int] = 64
MAX_BOX_SIZE: Final[int] = 32_768  # 32 KiB in bytes
MAX_BOX_KEY_SIZE: Final[int] = 64  # 64 bytes

PER_PAGE_MBR: Final[int] = 100_000  # 0.1 ALGO in microAlgos
PER_BYTE_SLICE_ENTRY_MBR: Final[int] = 50_000  # 0.05 ALGO in microAlgos
PER_BOX_MBR: Final[int] = 2_500  # 0.0025 ALGO in microAlgos
PER_BYTE_IN_BOX_MBR: Final[int] = 400  # 0.0004 ALGO in microAlgos

MAX_MBR_PER_APP: Final[int] = (
    MAX_PAGES_PER_APP * PER_PAGE_MBR
    + MAX_GLOBAL_STATE_ENTRIES * PER_BYTE_SLICE_ENTRY_MBR
)  # 3.6 ALGO in microAlgos

MAX_MBR_PER_BOX: Final[int] = (
    MAX_BOX_SIZE + MAX_BOX_KEY_SIZE
) * PER_BYTE_IN_BOX_MBR + PER_BOX_MBR  # 13.14 ALGO in microAlgos

BYTES_PER_APP_PAGE: Final[int] = 2048  # 2 KiB in bytes

PROPOSAL_APPROVAL_PAGES: Final[int] = 1
MAX_APP_TOTAL_ARG_LEN: Final[int] = 2048
METHOD_SELECTOR_LENGTH: Final[int] = 4
UINT64_LENGTH: Final[int] = 8
DYNAMIC_BYTE_ARRAY_LENGTH_OVERHEAD: Final[int] = 2

GOVERNANCE_PERIOD: Final[int] = 1_000_000  # blocks
COMMITTEE_GRACE_PERIOD: Final[int] = 10_000  # blocks
