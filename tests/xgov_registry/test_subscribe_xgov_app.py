import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.models import Account
from algosdk import abi
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from smart_contracts.artifacts.xgov_subscriber_app_mock.client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, xgov_box_name


def test_subscribe_xgov_app_success(
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    algorand_client: AlgorandClient,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.subscribe_xgov_app(
        app=xgov_subscriber_app.app_id,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=before_global_state.xgov_fee,
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(xgov_subscriber_app.app_address))],
            foreign_apps=[xgov_subscriber_app.app_id],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + before_global_state.xgov_fee) == after_info["amount"]  # type: ignore
    assert (before_global_state.xgovs + 1) == after_global_state.xgovs

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=xgov_box_name(xgov_subscriber_app.app_address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("address")
    voting_address = box_abi.decode(box_value)  # type: ignore

    assert deployer.address == voting_address  # type: ignore


def test_subscribe_xgov_app_already_xgov(
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    app_xgov: XGovSubscriberAppMockClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.ALREADY_XGOV):
        xgov_registry_client.subscribe_xgov_app(
            app=app_xgov.app_id,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.xgov_fee,
                    ),
                ),
                signer=deployer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(app_xgov.app_address))],
                foreign_apps=[app_xgov.app_id],
            ),
        )


def test_subscribe_xgov_app_wrong_recipient(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.subscribe_xgov_app(
            app=xgov_subscriber_app.app_id,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=deployer.address,
                        receiver=deployer.address,
                        amount=global_state.xgov_fee,
                    ),
                ),
                signer=deployer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(xgov_subscriber_app.app_address))],
                foreign_apps=[xgov_subscriber_app.app_id],
            ),
        )


def test_subscribe_xgov_app_wrong_amount(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.subscribe_xgov_app(
            app=xgov_subscriber_app.app_id,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=100,
                    ),
                ),
                signer=deployer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(xgov_subscriber_app.app_address))],
                foreign_apps=[xgov_subscriber_app.app_id],
            ),
        )
