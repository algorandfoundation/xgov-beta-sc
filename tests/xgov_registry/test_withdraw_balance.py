import pytest
from algokit_utils import SigningAccount, AlgorandClient, PaymentParams, AlgoAmount, CommonAppCallParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, DepositFundsArgs,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType


def test_withdraw_balance_success(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    deployer: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that the xGov Manager can successfully withdraw the balance
    (excluding MBR and outstanding funds).
    """
    # Add extra funds to the registry above the minimum balance
    extra_funds = AlgoAmount(algo=10)

    # First add some extra funds
    funded_xgov_registry_client.send.deposit_funds(
        args=DepositFundsArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=deployer.address,
                    receiver=funded_xgov_registry_client.app_address,
                    amount=extra_funds,
                )
            )
        )
    )

    # Get account info before withdrawal
    before_account_info = algorand_client.client.algod.account_info(
        funded_xgov_registry_client.app_address
    )
    before_balance = int(before_account_info["amount"])  # type: ignore
    initial_outstanding_funds = funded_xgov_registry_client.state.global_state.outstanding_funds
    min_balance = int(before_account_info["min-balance"])  # type: ignore

    # Calculate expected amount to be withdrawn
    expected_withdraw_amount = (
        before_balance - min_balance - initial_outstanding_funds
    )

    # Get deployer balance before withdrawal
    deployer_before = int(
        algorand_client.client.algod.account_info(deployer.address)["amount"]  # type: ignore
    )

    # Execute withdraw_balance
    funded_xgov_registry_client.send.withdraw_balance(
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    # Get account info after withdrawal
    after_account_info = algorand_client.client.algod.account_info(
        funded_xgov_registry_client.app_address
    )
    after_balance = int(after_account_info["amount"])  # type: ignore

    # Get deployer balance after withdrawal
    deployer_after = int(
        algorand_client.client.algod.account_info(deployer.address)["amount"]  # type: ignore
    )

    # Verify results
    # Balance of registry should be reduced to just enough to cover MBR and outstanding funds
    assert after_balance == min_balance + initial_outstanding_funds

    # Deployer should have received the withdrawn funds minus fees
    assert deployer_after >= deployer_before + expected_withdraw_amount - min_fee_times_2.amount_in_micro_algo


def test_withdraw_balance_not_manager(
    no_role_account: SigningAccount,
    min_fee_times_2: AlgoAmount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that only the xGov Manager can withdraw the balance.
    """
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.send.withdraw_balance(
            params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
        )


def test_withdraw_balance_insufficient_fee(
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that transaction fails if fee is insufficient.
    """
    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FEE):
        funded_xgov_registry_client.send.withdraw_balance()


def test_withdraw_balance_no_funds_available(
    min_fee_times_2: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that transaction fails if no withdrawable funds are available.
    """
    # Get the registry state to determine if there are funds above MBR and outstanding funds
    registry_info = xgov_registry_client.algorand.client.algod.account_info(
        xgov_registry_client.app_address
    )
    outstanding_funds = xgov_registry_client.state.global_state.outstanding_funds

    # Ensure no excess funds by withdrawing any that exist
    available = (
        int(registry_info["amount"])  # type: ignore
        - int(registry_info["min-balance"])  # type: ignore
        - outstanding_funds
    )

    # If there are available funds, withdraw them first
    if available > 0:
        xgov_registry_client.send.withdraw_balance(
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )

    # Now try to withdraw again, which should fail
    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.send.withdraw_balance(
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )
