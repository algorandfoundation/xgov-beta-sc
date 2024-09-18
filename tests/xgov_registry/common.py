
from smart_contracts.artifacts.xgov_registry.client import GlobalState
from algosdk.encoding import encode_address

def assert_registry_global_state(
    global_state: GlobalState,
    *,
    manager_address: str,
    payor_address: str,
    committee_manager_address: str
) -> None:
    assert encode_address(global_state.proposer.as_bytes) == manager_address  # type: ignore
    assert encode_address(global_state.proposer.as_bytes) == payor_address  # type: ignore
    assert encode_address(global_state.proposer.as_bytes) == committee_manager_address  # type: ignore