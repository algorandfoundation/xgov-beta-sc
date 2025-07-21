from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from tests.xgov_registry.common import assert_get_state


def test_get_state_success(xgov_registry_client: XGovRegistryClient) -> None:
    get_state = xgov_registry_client.send.get_state()
    assert_get_state(xgov_registry_client=xgov_registry_client, get_state=get_state.abi_return)
