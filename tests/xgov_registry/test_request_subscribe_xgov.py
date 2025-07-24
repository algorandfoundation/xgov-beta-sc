import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    PaymentParams,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ApproveSubscribeXgovArgs,
    RequestSubscribeXgovArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import get_xgov_fee


def test_request_subscribe_xgov_success(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    initial_request_id = xgov_registry_client.state.global_state.request_id
    xgov_registry_client.send.request_subscribe_xgov(
        args=RequestSubscribeXgovArgs(
            xgov_address=xgov_subscriber_app.app_address,
            owner_address=deployer.address,
            relation_type=0,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=get_xgov_fee(xgov_registry_client),
                )
            ),
        )
    )
    final_request_id = xgov_registry_client.state.global_state.request_id
    assert final_request_id == initial_request_id + 1


def test_request_subscribe_xgov_already_xgov(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    xgov_registry_client.send.approve_subscribe_xgov(
        args=ApproveSubscribeXgovArgs(
            request_id=xgov_registry_client.state.global_state.request_id - 1
        ),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    with pytest.raises(LogicError, match=err.ALREADY_XGOV):
        xgov_registry_client.send.request_subscribe_xgov(
            args=RequestSubscribeXgovArgs(
                xgov_address=app_xgov_subscribe_requested.app_address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                ),
            ),
        )


def test_request_subscribe_xgov_wrong_recipient(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PAYMENT):
        xgov_registry_client.send.request_subscribe_xgov(
            args=RequestSubscribeXgovArgs(
                xgov_address=xgov_subscriber_app.app_address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=deployer.address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                ),
            ),
        )


def test_request_subscribe_xgov_wrong_amount(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PAYMENT):
        xgov_registry_client.send.request_subscribe_xgov(
            args=RequestSubscribeXgovArgs(
                xgov_address=xgov_subscriber_app.app_address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=AlgoAmount(
                            micro_algo=get_xgov_fee(xgov_registry_client).micro_algo - 1
                        ),
                    )
                ),
            ),
        )


def test_request_subscribe_xgov_paused_registry_error(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    xgov_fee = get_xgov_fee(xgov_registry_client)
    xgov_registry_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.request_subscribe_xgov(
            args=RequestSubscribeXgovArgs(
                xgov_address=xgov_subscriber_app.app_address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=xgov_fee,
                    )
                ),
            ),
        )

    xgov_registry_client.send.resume_registry()
    xgov_registry_client.send.request_subscribe_xgov(
        args=RequestSubscribeXgovArgs(
            xgov_address=xgov_subscriber_app.app_address,
            owner_address=deployer.address,
            relation_type=0,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=xgov_fee,
                )
            ),
        )
    )
