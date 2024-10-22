from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from tests.xgov_registry.common import (
    COMMITTEE_ID,
    COMMITTEE_SIZE,
    COMMITTEE_VOTES,
    assert_get_state,
)


def test_get_state_success(
    xgov_registry_client: XGovRegistryClient,
    committee_manager: AddressAndSigner,
) -> None:

    xgov_registry_client.declare_committee(
        cid=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=committee_manager.address,
            signer=committee_manager.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()
    get_state = xgov_registry_client.get_state()

    assert_get_state(global_state=global_state, get_state=get_state.return_value)
