import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.models import Account
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType


def test_deposit_funds_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    added_amount = 10_000_000

    sp = algorand_client.get_suggested_params()

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=added_amount,
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert (
        before_global_state.outstanding_funds + added_amount
        == after_global_state.outstanding_funds
    )


def test_deposit_funds_wrong_recipient(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.WRONG_RECEIVER):
        xgov_registry_client.deposit_funds(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=deployer.address,
                        receiver=deployer.address,
                        amount=10_000_000,
                    ),
                ),
                signer=deployer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
            ),
        )
