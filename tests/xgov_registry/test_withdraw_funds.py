import pytest

from algokit_utils.models import Account
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient

from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import logicErrorType

def test_withdraw_funds_success(
    funded_xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
) -> None:
    before_global_state = funded_xgov_registry_client.get_global_state()
    added_amount = 10_000_000
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2

    funded_xgov_registry_client.withdraw_funds(
        amount=added_amount,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    after_global_state = funded_xgov_registry_client.get_global_state()

    assert (before_global_state.outstanding_funds - added_amount) == after_global_state.outstanding_funds

def test_withdraw_funds_not_manager(
    funded_xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    added_amount = 10_000_000
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2

    with pytest.raises(logicErrorType, match=err.UNAUTHORIZED):
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
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2

    with pytest.raises(logicErrorType, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.withdraw_funds(
            amount=11_000_000,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
            ),
        )