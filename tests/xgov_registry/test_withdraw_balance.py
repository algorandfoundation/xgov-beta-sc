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
    before_account_info = algorand_client.account.get_information(funded_xgov_registry_client.app_address)
    before_balance = before_account_info.amount.micro_algo
    initial_outstanding_funds = funded_xgov_registry_client.state.global_state.outstanding_funds
    min_balance = before_account_info.min_balance.micro_algo

    # Calculate expected amount to be withdrawn
    expected_withdraw_amount = (
        before_balance - min_balance - initial_outstanding_funds
    )

    # Get deployer balance before withdrawal
    deployer_balance_before = algorand_client.account.get_information(deployer.address).amount.micro_algo

    # Execute withdraw_balance
    funded_xgov_registry_client.send.withdraw_balance(
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    # Get account info after withdrawal
    after_account_info = algorand_client.account.get_information(funded_xgov_registry_client.app_address)
    after_balance = after_account_info.amount.micro_algo

    # Get deployer balance after withdrawal
    deployer_balance_after = algorand_client.account.get_information(deployer.address).amount.micro_algo

    # Verify results
    # Balance of registry should be reduced to just enough to cover MBR and outstanding funds
    assert after_balance == min_balance + initial_outstanding_funds

    # Deployer should have received the withdrawn funds minus fees
    assert deployer_balance_after >= deployer_balance_before + expected_withdraw_amount - min_fee_times_2.amount_in_micro_algo


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
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that transaction fails if no withdrawable funds are available.
    """
    # Get the registry state to determine if there are funds above MBR and outstanding funds
    registry_info = algorand_client.account.get_information(xgov_registry_client.app_address)
    outstanding_funds = xgov_registry_client.state.global_state.outstanding_funds

    # Ensure no excess funds by withdrawing any that exist
    available = registry_info.amount.micro_algo - registry_info.min_balance.micro_algo - outstanding_funds

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
