from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
)
from tests.xgov_registry.common import assert_get_state


def test_get_state_success(
    xgov_registry_client: XGovRegistryClient,
    committee_manager: AddressAndSigner,
) -> None:

    xgov_registry_client.declare_committee(
        committee_id=DEFAULT_COMMITTEE_ID,
        size=DEFAULT_COMMITTEE_MEMBERS,
        votes=DEFAULT_COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=committee_manager.address,
            signer=committee_manager.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()
    get_state = xgov_registry_client.get_state()

    assert_get_state(global_state=global_state, get_state=get_state.return_value)
