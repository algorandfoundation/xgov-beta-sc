import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.models import Account

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, assert_registry_payor


def test_set_payor_success(
    deployer: Account,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.set_payor(
        payor=no_role_account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    assert_registry_payor(
        global_state=global_state,
        payor_address=no_role_account.address,
    )


def test_set_payor_not_manager(
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_payor(
            payor=no_role_account.address,
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
            ),
        )
