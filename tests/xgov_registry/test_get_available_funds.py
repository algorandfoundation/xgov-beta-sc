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


def test_get_available_funds_success(
    algorand_client: AlgorandClient,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    registry_info = algorand_client.account.get_information(
        funded_xgov_registry_client.app_address
    )
    balance = registry_info.amount.micro_algo
    min_balance = registry_info.min_balance.micro_algo
    outstanding_funds = funded_xgov_registry_client.state.global_state.outstanding_funds

    expected_available = balance - min_balance - outstanding_funds
    assert expected_available > 0

    available_funds = funded_xgov_registry_client.send.get_available_funds().abi_return
    assert available_funds is not None

    assert available_funds == expected_available


def test_get_available_funds_no_funds_available(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    xgov_payor: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    registry_info = algorand_client.account.get_information(
        xgov_registry_client.app_address
    )
    balance = registry_info.amount.micro_algo
    min_balance = registry_info.min_balance.micro_algo
    outstanding_funds = xgov_registry_client.state.global_state.outstanding_funds

    available = balance - min_balance - outstanding_funds

    # If there are available funds, withdraw them first to ensure no funds are available
    if available > 0:
        xgov_registry_client.send.withdraw_available_funds(
            args=WithdrawAvailableFundsArgs(amount=available),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_2
            ),
        )

    # Now call get_available_funds should fail
    with pytest.raises(LogicError, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.send.get_available_funds()
