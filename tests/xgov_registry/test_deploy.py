from algosdk.v2client.algod import AlgodClient

import algokit_utils
from algokit_utils.beta.account_manager import AddressAndSigner
from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient

from tests.xgov_registry.common import assert_registry_global_state

def test_deploy_registry(
    xgov_registry_client: XGovRegistryClient,
    deployer: algokit_utils.Account
) -> None:
    global_state = xgov_registry_client.get_global_state()

    assert_registry_global_state(
        global_state=global_state,
        manager_address=deployer.address,
        payor_address=deployer.address,
        committee_manager_address=deployer.address
    )
