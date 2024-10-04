import pytest

from algokit_utils.models import Account
from algokit_utils import TransactionParameters
from algosdk.v2client.algod import AlgodClient
from algokit_utils.beta.account_manager import AddressAndSigner
from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    assert_registry_payor,
    logicErrorType
)

def test_set_payor_success(
    xgov_registry_client: XGovRegistryClient,
    deployer: Account,
    random_account: AddressAndSigner,
) -> None:
    xgov_registry_client.set_payor(
        payor=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        )
    )

    global_state = xgov_registry_client.get_global_state()

    assert_registry_payor(
        global_state=global_state,
        payor_address=random_account.address,
    )

def test_set_payor_not_manager(
    xgov_registry_client: XGovRegistryClient,
    random_account: AddressAndSigner,
) -> None:
    with pytest.raises(logicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_payor(
            payor=random_account.address,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
            )
        )