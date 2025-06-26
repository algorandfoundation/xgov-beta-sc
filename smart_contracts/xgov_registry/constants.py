# Constants

from typing import Final

# Reference: https://developer.algorand.org/docs/get-details/parameter_tables/

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
