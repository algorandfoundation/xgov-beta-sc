import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    LogicError,
    PaymentParams,
    SigningAccount,
)
from algosdk.abi import Method
from algosdk.transaction import ApplicationNoOpTxn, PaymentTxn

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    DepositFundsArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err

ADDED_AMOUNT = AlgoAmount(algo=10)
DEPOSIT_FUNDS_SELECTOR = Method.from_signature("deposit_funds(pay)void").get_selector()


def _deposit_call(
    algorand_client: AlgorandClient,
    *,
    sender: str,
    app_id: int,
    note: bytes,
) -> ApplicationNoOpTxn:
    return ApplicationNoOpTxn(
        sender=sender,
        sp=algorand_client.client.algod.suggested_params(),
        index=app_id,
        app_args=[DEPOSIT_FUNDS_SELECTOR],
        note=note,
    )


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
    assert (
        xgov_registry_client.state.global_state.outstanding_funds
        == initial_funds + ADDED_AMOUNT.amount_in_micro_algo
    )


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


def test_deposit_funds_cannot_reuse_one_payment_for_multiple_calls(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:

    malicious = algorand_client.new_group()
    malicious.add_transaction(
        PaymentTxn(
            sender=deployer.address,
            sp=algorand_client.client.algod.suggested_params(),
            receiver=xgov_registry_client.app_address,
            amt=ADDED_AMOUNT.amount_in_micro_algo,
        )
    )
    malicious.add_transaction(
        _deposit_call(
            algorand_client,
            sender=deployer.address,
            app_id=xgov_registry_client.app_id,
            note=b"deposit-call",
        )
    )
    malicious.add_transaction(
        _deposit_call(
            algorand_client,
            sender=deployer.address,
            app_id=xgov_registry_client.app_id,
            note=b"malicious-deposit-call",
        )
    )

    # The second app call cannot reference the first payment: ARC4 binds the pay
    # argument to the transaction immediately before the app call, which is the
    # first app call here, so the group is rejected atomically.
    with pytest.raises(LogicError, match="transaction type is pay"):
        malicious.send()
