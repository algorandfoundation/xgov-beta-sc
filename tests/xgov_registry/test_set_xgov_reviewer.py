import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.models import Account
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, decode_address, xgov_box_name


def test_set_xgov_council_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    random_account: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    xgov_registry_client.set_xgov_council(
        council=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(deployer.address))],
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    assert global_state.xgov_council.as_bytes == decode_address(random_account.address)  # type: ignore


def test_set_xgov_council_not_manager(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_xgov_council(
            council=random_account.address,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )
