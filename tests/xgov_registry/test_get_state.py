from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient

from algokit_utils.beta.account_manager import AddressAndSigner
from tests.xgov_registry.common import assert_get_state
from algokit_utils import TransactionParameters

from tests.xgov_registry.common import (
    committee_id,
    committee_votes,
    committee_size
)

def test_get_state_success(
        xgov_registry_client: XGovRegistryClient,
        committee_manager: AddressAndSigner,
) -> None:

    xgov_registry_client.declare_committee(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=committee_manager.address,
            signer=committee_manager.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()
    get_state = xgov_registry_client.get_state()

    assert_get_state(
        global_state=global_state,
        get_state=get_state.return_value
    )
