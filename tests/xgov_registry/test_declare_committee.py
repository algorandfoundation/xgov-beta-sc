import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    COMMITTEE_ID,
    COMMITTEE_SIZE,
    COMMITTEE_VOTES,
    LogicErrorType,
    assert_committee,
)


def test_declare_committee_success(
    xgov_registry_client: XGovRegistryClient, committee_manager: AddressAndSigner
) -> None:
    xgov_registry_client.declare_committee(
        committee_id=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=committee_manager.address,
            signer=committee_manager.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    assert_committee(
        global_state=global_state,
        committee_id=COMMITTEE_ID,
        committee_size=COMMITTEE_SIZE,
        committee_votes=COMMITTEE_VOTES,
    )


def test_declare_committee_not_manager(
    xgov_registry_client: XGovRegistryClient, random_account: AddressAndSigner
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.declare_committee(
            committee_id=COMMITTEE_ID,
            size=COMMITTEE_SIZE,
            votes=COMMITTEE_VOTES,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
            ),
        )


def test_declare_committee_too_large(
    xgov_registry_client: XGovRegistryClient, committee_manager: AddressAndSigner
) -> None:
    max_committee_size = xgov_registry_client.get_global_state().max_committee_size
    with pytest.raises(LogicErrorType, match=err.COMMITTEE_SIZE_TOO_LARGE):
        xgov_registry_client.declare_committee(
            committee_id=COMMITTEE_ID,
            size=max_committee_size + 1,
            votes=COMMITTEE_VOTES,
            transaction_parameters=TransactionParameters(
                sender=committee_manager.address,
                signer=committee_manager.signer,
            ),
        )
