import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.models import Account
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType


def test_withdraw_balance_success(
    funded_xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    sp: SuggestedParams,
) -> None:
    """
    Test that the xGov Manager can successfully withdraw the balance
    (excluding MBR and outstanding funds).
    """
    # Add extra funds to the registry above the minimum balance
    extra_funds = 10_000_000

    # First add some extra funds
    funded_xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=funded_xgov_registry_client.app_address,
                    amount=extra_funds,
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

    # Get account info before withdrawal
    before_account_info = funded_xgov_registry_client.algod_client.account_info(
        funded_xgov_registry_client.app_address
    )
    before_balance = int(before_account_info["amount"])  # type: ignore
    before_global_state = funded_xgov_registry_client.get_global_state()
    min_balance = int(before_account_info["min-balance"])  # type: ignore

    # Calculate expected amount to be withdrawn
    expected_withdraw_amount = (
        before_balance - min_balance - before_global_state.outstanding_funds
    )

    # Ensure transaction fee is sufficient
    sp.min_fee *= 2  # type: ignore

    # Get deployer balance before withdrawal
    deployer_before = int(
        funded_xgov_registry_client.algod_client.account_info(deployer.address)["amount"]  # type: ignore
    )

    # Execute withdraw_balance
    funded_xgov_registry_client.withdraw_balance(
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    # Get account info after withdrawal
    after_account_info = funded_xgov_registry_client.algod_client.account_info(
        funded_xgov_registry_client.app_address
    )
    after_balance = int(after_account_info["amount"])  # type: ignore

    # Get deployer balance after withdrawal
    deployer_after = int(
        funded_xgov_registry_client.algod_client.account_info(deployer.address)["amount"]  # type: ignore
    )

    # Verify results
    # Balance of registry should be reduced to just enough to cover MBR and outstanding funds
    assert after_balance == min_balance + before_global_state.outstanding_funds

    # Deployer should have received the withdrawn funds minus fees
    fee_paid = int(sp.min_fee)  # type: ignore
    assert deployer_after >= deployer_before + expected_withdraw_amount - fee_paid


def test_withdraw_balance_not_manager(
    funded_xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    """
    Test that only the xGov Manager can withdraw the balance.
    """
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.withdraw_balance(
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
            ),
        )


def test_withdraw_balance_insufficient_fee(
    funded_xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
) -> None:
    """
    Test that transaction fails if fee is insufficient.
    """
    # Use regular minimum fee (which is less than required)
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FEE):
        funded_xgov_registry_client.withdraw_balance(
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
            ),
        )


def test_withdraw_balance_no_funds_available(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    """
    Test that transaction fails if no withdrawable funds are available.
    """
    # Get the registry state to determine if there are funds above MBR and outstanding funds
    registry_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address
    )
    global_state = xgov_registry_client.get_global_state()

    # Ensure no excess funds by withdrawing any that exist
    available = (
        int(registry_info["amount"])  # type: ignore
        - int(registry_info["min-balance"])  # type: ignore
        - global_state.outstanding_funds
    )

    # If there are available funds, withdraw them first
    if available > 0:
        sp = sp_min_fee_times_2
        xgov_registry_client.withdraw_balance(
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
            ),
        )

    sp = sp_min_fee_times_2

    # Now try to withdraw again, which should fail
    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.withdraw_balance(
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                note=b"Withdraw again",
            ),
        )
