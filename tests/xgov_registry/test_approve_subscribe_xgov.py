import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    PaymentParams,
    SigningAccount,
)
from algosdk.error import AlgodHTTPError

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


def test_approve_subscribe_xgov_success(
    no_role_account: SigningAccount,
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    request_id = xgov_registry_client.state.global_state.request_id - 1
    xgov_registry_client.send.approve_subscribe_xgov(
        args=ApproveSubscribeXgovArgs(request_id=request_id),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs
    assert final_xgovs == initial_xgovs + 1

    xgov_box = xgov_registry_client.state.box.xgov_box.get_value(
        app_xgov_subscribe_requested.app_address
    )

    assert no_role_account.address == xgov_box.voting_address  # type: ignore

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.request_box.get_value(request_id)


def test_approve_subscribe_xgov_not_subscriber(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.approve_subscribe_xgov(
            args=ApproveSubscribeXgovArgs(
                request_id=xgov_registry_client.state.global_state.request_id - 1
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_approve_subscribe_already_xgov(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.ALREADY_XGOV):
        xgov_registry_client.send.request_subscribe_xgov(
            args=RequestSubscribeXgovArgs(
                xgov_address=app_xgov_managed_subscription.app_address,
                owner_address=no_role_account.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                ),
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
