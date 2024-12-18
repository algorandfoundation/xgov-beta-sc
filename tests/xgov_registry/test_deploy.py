import algokit_utils

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from tests.xgov_registry.common import assert_registry_global_state


def test_deploy_registry(
    xgov_registry_client: XGovRegistryClient,
    deployer: algokit_utils.Account,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    assert_registry_global_state(
        global_state=global_state,
        manager_address=deployer.address,
    )
