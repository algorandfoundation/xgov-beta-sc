from smart_contracts.xgov_registry.constants import (
    DYNAMIC_BYTE_ARRAY_LENGTH_OVERHEAD,
    MAX_APP_TOTAL_ARG_LEN,
    METHOD_SELECTOR_LENGTH,
    UINT64_LENGTH,
)


def load_proposal_contract_data_size_per_transaction() -> int:
    return (
        MAX_APP_TOTAL_ARG_LEN
        - METHOD_SELECTOR_LENGTH
        - UINT64_LENGTH
        - DYNAMIC_BYTE_ARRAY_LENGTH_OVERHEAD
    )
