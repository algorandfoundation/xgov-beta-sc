import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.models import Account

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType


def test_update_xgov_registry_success(
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.update_update_xgov_registry(
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )


def test_update_xgov_registry_not_manager(
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.update_update_xgov_registry(
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
            ),
        )
