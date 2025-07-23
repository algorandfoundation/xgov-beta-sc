import pytest
from algokit_utils import AlgorandClient, PaymentParams, SigningAccount, AlgoAmount, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, DepositFundsArgs,
)
from smart_contracts.errors import std_errors as err

ADDED_AMOUNT = AlgoAmount(algo=10)


def test_deposit_funds_success(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_funds = xgov_registry_client.state.global_state.outstanding_funds
    xgov_registry_client.send.deposit_funds(
        args=DepositFundsArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=ADDED_AMOUNT,
                )
            )
        ),
    )
    assert xgov_registry_client.state.global_state.outstanding_funds == initial_funds + ADDED_AMOUNT.amount_in_micro_algo


def test_deposit_funds_wrong_recipient(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_RECEIVER):
        xgov_registry_client.send.deposit_funds(
            args=DepositFundsArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=deployer.address,
                        amount=ADDED_AMOUNT,
                    )
                )
            ),
        )
