import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.models import Account
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, request_box_name, xgov_box_name


def test_request_subscribe_xgov_success(
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    algorand_client: AlgorandClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.request_subscribe_xgov(
        xgov_address=xgov_subscriber_app.app_address,
        owner_address=deployer.address,
        relation_type=0,
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
            boxes=[
                (0, xgov_box_name(xgov_subscriber_app.app_address)),
                (0, request_box_name(global_state.request_id)),
            ],
            foreign_apps=[xgov_subscriber_app.app_id],
        ),
    )


def test_request_subscribe_xgov_already_xgov(
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    app_xgov: XGovSubscriberAppMockClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.ALREADY_XGOV):
        xgov_registry_client.request_subscribe_xgov(
            xgov_address=app_xgov.app_address,
            owner_address=deployer.address,
            relation_type=0,
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
                boxes=[
                    (0, xgov_box_name(app_xgov.app_address)),
                    (0, request_box_name(global_state.request_id)),
                ],
                foreign_apps=[app_xgov.app_id],
            ),
        )


def test_request_subscribe_xgov_wrong_recipient(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.request_subscribe_xgov(
            xgov_address=xgov_subscriber_app.app_address,
            owner_address=deployer.address,
            relation_type=0,
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
                boxes=[
                    (0, xgov_box_name(xgov_subscriber_app.app_address)),
                    (0, request_box_name(global_state.request_id)),
                ],
                foreign_apps=[xgov_subscriber_app.app_id],
            ),
        )


def test_request_subscribe_xgov_wrong_amount(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.request_subscribe_xgov(
            xgov_address=xgov_subscriber_app.app_address,
            owner_address=deployer.address,
            relation_type=0,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=10,
                    ),
                ),
                signer=deployer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[
                    (0, xgov_box_name(xgov_subscriber_app.app_address)),
                    (0, request_box_name(global_state.request_id)),
                ],
                foreign_apps=[xgov_subscriber_app.app_id],
            ),
        )
