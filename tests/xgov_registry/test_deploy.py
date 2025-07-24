from algokit_utils import SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)


def test_deploy_registry(
    xgov_registry_client: XGovRegistryClient, deployer: SigningAccount
) -> None:
    assert xgov_registry_client.state.global_state.xgov_manager == deployer.address
