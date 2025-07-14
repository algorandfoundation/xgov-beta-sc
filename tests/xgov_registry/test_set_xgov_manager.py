import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.models import Account
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, decode_address, xgov_box_name


def test_set_xgov_manager_success(
    deployer: Account,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    xgov_registry_client.set_xgov_manager(
        manager=no_role_account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp_min_fee_times_2,
            boxes=[(0, xgov_box_name(deployer.address))],
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    assert global_state.xgov_manager.as_bytes == decode_address(no_role_account.address)  # type: ignore


def test_set_xgov_manager_not_manager(
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_xgov_manager(
            manager=no_role_account.address,
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp_min_fee_times_2,
                boxes=[(0, xgov_box_name(no_role_account.address))],
            ),
        )
