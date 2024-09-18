from algosdk.v2client.algod import AlgodClient
from algokit_utils.beta.account_manager import AddressAndSigner
from smart_contracts.artifacts.xgov_registry.client import XgovRegistryClient

# from tests.proposal.common import assert_proposal_global_state
from tests.xgov_registry.common import assert_registry_global_state


def test_deploy_registry(
    registry_client: XgovRegistryClient,
    deployer: AddressAndSigner
) -> None:
    global_state = registry_client.get_global_state()

    assert_registry_global_state(
        global_state=global_state,
        proposer_address=deployer.address,
    )
