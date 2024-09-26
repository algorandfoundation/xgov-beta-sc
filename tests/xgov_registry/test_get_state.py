from smart_contracts.artifacts.xgov_registry.client import (
    XGovRegistryClient,
    XGovRegistryConfig,
)
from tests.xgov_registry.common import assert_get_state
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner

def test_get_state_success(
    xgov_registry_client: XGovRegistryClient,
    deployer: AddressAndSigner,
    xgov_registry_config: XGovRegistryConfig
) -> None:

    xgov_registry_client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    xgov_registry_client.declare_committee(
        id=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        size=10,
        votes=100,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()
    get_state = xgov_registry_client.get_state()

    assert_get_state(
        global_state=global_state,
        get_state=get_state.return_value
    )
