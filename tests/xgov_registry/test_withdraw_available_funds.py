import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    WithdrawAvailableFundsArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err


def test_withdraw_balance_success(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    deployer: SigningAccount,
    xgov_payor: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that the xGov Payor can successfully withdraw the available balance
    (excluding MBR and outstanding funds).
    """

    # Get xGov Treasury info before withdrawal
    treasury_info = algorand_client.account.get_information(
        funded_xgov_registry_client.app_address
    )
    before_balance = treasury_info.amount.micro_algo
    outstanding_funds = funded_xgov_registry_client.state.global_state.outstanding_funds
    min_balance = treasury_info.min_balance.micro_algo

    # Calculate the available amount to be withdrawn
    available = before_balance - min_balance - outstanding_funds
    assert available > 0

    # Get xGov Payor balance before withdrawal
    payor_balance_before = algorand_client.account.get_information(
        xgov_payor.address
    ).amount.micro_algo

    # Execute withdraw_balance
    funded_xgov_registry_client.send.withdraw_available_funds(
        args=WithdrawAvailableFundsArgs(amount=available),
        params=CommonAppCallParams(
            sender=xgov_payor.address, static_fee=min_fee_times_2
        ),
    )

    # Get xGov Treasury balance after withdrawal
    after_balance = algorand_client.account.get_information(
        funded_xgov_registry_client.app_address
    ).amount.micro_algo

    # Get xGov Payor balance after withdrawal
    payor_balance_after = algorand_client.account.get_information(
        xgov_payor.address
    ).amount.micro_algo

    # Verify results
    # xGov Treasury balance should be reduced by the available funds
    assert after_balance == before_balance - available

    # xGov Payor should have received the withdrawn funds minus fees
    assert (
        payor_balance_after
        == payor_balance_before + available - min_fee_times_2.amount_in_micro_algo
    )

    # No funds should be available to withdraw
    final_balance = algorand_client.account.get_information(
        funded_xgov_registry_client.app_address
    ).amount.micro_algo
    available = final_balance - min_balance - outstanding_funds
    assert not available


def test_withdraw_balance_not_payor(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that only the xGov Payor can withdraw the balance.
    """
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.send.withdraw_available_funds(
            args=WithdrawAvailableFundsArgs(amount=0),
            params=CommonAppCallParams(
                sender=no_role_account.address, static_fee=min_fee_times_2
            ),
        )


def test_withdraw_balance_insufficient_fee(
    xgov_payor: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that transaction fails if fee is insufficient.
    """
    with pytest.raises(LogicError, match=err.INSUFFICIENT_FEE):
        funded_xgov_registry_client.send.withdraw_available_funds(
            args=WithdrawAvailableFundsArgs(amount=0),
            params=CommonAppCallParams(sender=xgov_payor.address),
        )


def test_withdraw_balance_no_funds_available(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    """
    Test that transaction fails if no withdrawable funds are available.
    """
    # Get the registry state to determine if there are funds above MBR and outstanding funds
    registry_info = algorand_client.account.get_information(
        xgov_registry_client.app_address
    )
    outstanding_funds = xgov_registry_client.state.global_state.outstanding_funds

    # Ensure no excess funds by withdrawing any that exist
    available = (
        registry_info.amount.micro_algo
        - registry_info.min_balance.micro_algo
        - outstanding_funds
    )

    # If there are available funds, withdraw them first
    if available > 0:
        xgov_registry_client.send.withdraw_available_funds(
            args=WithdrawAvailableFundsArgs(amount=available),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_2
            ),
        )

    # Now try to withdraw again, which should fail
    with pytest.raises(LogicError, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.send.withdraw_available_funds(
            args=WithdrawAvailableFundsArgs(amount=1),  # Attempt to withdraw any amount
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_2
            ),
        )
