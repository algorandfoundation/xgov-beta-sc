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
    algorand_client: AlgorandClient,
    xgov_subscriber: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
    sp: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    before_global_state = xgov_registry_client.get_global_state()

    request_id = before_global_state.request_id - 1

    xgov_registry_client.approve_subscribe_xgov(
        request_id=request_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_subscriber.address,
            signer=xgov_subscriber.signer,
            suggested_params=sp,
            boxes=[
                (0, request_box_name(request_id)),
                (0, xgov_box_name(app_xgov_subscribe_requested.app_address)),
            ],
            foreign_apps=[app_xgov_subscribe_requested.app_id],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.ALREADY_XGOV):
        xgov_registry_client.request_subscribe_xgov(
            xgov_address=app_xgov_subscribe_requested.app_address,
            owner_address=xgov_subscriber.address,
            relation_type=0,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=xgov_subscriber.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.xgov_fee,
                    ),
                ),
                signer=xgov_subscriber.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=xgov_subscriber.address,
                signer=xgov_subscriber.signer,
                suggested_params=sp,
                boxes=[
                    (0, xgov_box_name(app_xgov_subscribe_requested.app_address)),
                    (0, request_box_name(global_state.request_id)),
                ],
                foreign_apps=[app_xgov_subscribe_requested.app_id],
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


def test_request_subscribe_xgov_paused_registry_error(
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    algorand_client: AlgorandClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
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

    xgov_registry_client.resume_registry()

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
