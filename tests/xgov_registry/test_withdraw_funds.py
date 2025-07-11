import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.models import Account
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import TREASURY_AMOUNT, LogicErrorType


def test_withdraw_funds_success(
    deployer: Account,
    funded_xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    before_global_state = funded_xgov_registry_client.get_global_state()
    sp = sp_min_fee_times_2

    funded_xgov_registry_client.withdraw_funds(
        amount=TREASURY_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    after_global_state = funded_xgov_registry_client.get_global_state()

    assert (
        before_global_state.outstanding_funds - TREASURY_AMOUNT
    ) == after_global_state.outstanding_funds


def test_withdraw_funds_not_manager(
    random_account: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.withdraw_funds(
            amount=TREASURY_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
            ),
        )


def test_withdraw_funds_insufficient_funds(
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.withdraw_funds(
            amount=TREASURY_AMOUNT + 1,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
            ),
        )
