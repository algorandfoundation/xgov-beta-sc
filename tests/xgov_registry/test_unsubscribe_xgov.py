import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk import error
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from smart_contracts.artifacts.xgov_subscriber_app_mock.client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, xgov_box_name


def test_unsubscribe_xgov_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_min_balance,
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(random_account.address))],
        ),
    )

    sp.min_fee *= 2  # type: ignore

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.unsubscribe_xgov(
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(random_account.address))],
        ),
    )

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] - global_state.xgov_min_balance) == after_info["amount"]  # type: ignore

    with pytest.raises(error.AlgodHTTPError):  # type: ignore
        xgov_registry_client.algod_client.application_box_by_name(
            application_id=xgov_registry_client.app_id,
            box_name=xgov_box_name(random_account.address),
        )


def test_app_subscribe_xgov_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    xgov_subscriber_app.subscribe_xgov(
        app_id=xgov_registry_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            foreign_apps=[xgov_registry_client.app_id],
            boxes=[
                (
                    xgov_registry_client.app_id,
                    xgov_box_name(xgov_subscriber_app.app_address),
                )
            ],
        ),
    )

    xgov_subscriber_app.unsubscribe_xgov(
        app_id=xgov_registry_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            foreign_apps=[xgov_registry_client.app_id],
            boxes=[
                (
                    xgov_registry_client.app_id,
                    xgov_box_name(xgov_subscriber_app.app_address),
                )
            ],
        ),
    )


def test_unsubscribe_xgov_wrong_fee(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_min_balance,
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(random_account.address))],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FEE):
        xgov_registry_client.unsubscribe_xgov(
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )


def test_unsubscribe_xgov_not_an_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.unsubscribe_xgov(
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )
