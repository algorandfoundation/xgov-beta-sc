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
from tests.xgov_registry.common import LogicErrorType


def test_withdraw_funds_success(
    funded_xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    before_global_state = funded_xgov_registry_client.get_global_state()
    added_amount = 10_000_000
    sp = sp_min_fee_times_2

    funded_xgov_registry_client.withdraw_funds(
        amount=added_amount,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    after_global_state = funded_xgov_registry_client.get_global_state()

    assert (
        before_global_state.outstanding_funds - added_amount
    ) == after_global_state.outstanding_funds


def test_withdraw_funds_not_manager(
    funded_xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    added_amount = 10_000_000
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.withdraw_funds(
            amount=added_amount,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
            ),
        )


def test_withdraw_funds_insufficient_funds(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.withdraw_funds(
            amount=11_000_000,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
            ),
        )
