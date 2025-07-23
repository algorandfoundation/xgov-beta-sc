import pytest
from algokit_utils import SigningAccount, CommonAppCallParams, AlgoAmount, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, WithdrawFundsArgs,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import TREASURY_AMOUNT


def test_withdraw_funds_success(
    min_fee_times_2: AlgoAmount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_funds = funded_xgov_registry_client.state.global_state.outstanding_funds
    withdraw_amount = TREASURY_AMOUNT.amount_in_micro_algo

    funded_xgov_registry_client.send.withdraw_funds(
        args=WithdrawFundsArgs(amount=withdraw_amount),
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    final_funds = funded_xgov_registry_client.state.global_state.outstanding_funds

    assert final_funds == initial_funds - withdraw_amount


def test_withdraw_funds_not_manager(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.send.withdraw_funds(
            args=WithdrawFundsArgs(amount=TREASURY_AMOUNT.amount_in_micro_algo),
            params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_2)
        )


def test_withdraw_funds_insufficient_funds(
    min_fee_times_2: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.send.withdraw_funds(
            args=WithdrawFundsArgs(amount=TREASURY_AMOUNT.micro_algo + 1,),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )
