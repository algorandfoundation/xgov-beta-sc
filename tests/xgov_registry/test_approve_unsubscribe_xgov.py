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
    ApproveUnsubscribeXgovArgs,
    RequestUnsubscribeXgovArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import get_xgov_fee


def test_approve_unsubscribe_xgov_success(
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    request_id = xgov_registry_client.state.global_state.request_id - 1
    xgov_registry_client.send.approve_unsubscribe_xgov(
        args=ApproveUnsubscribeXgovArgs(request_id=request_id),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs
    assert final_xgovs == initial_xgovs - 1
    assert (
        xgov_registry_client.state.box.xgov_box.get_value(
            app_xgov_unsubscribe_requested.app_address
        ).unsubscribed_round
        > 0
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.request_unsubscribe_box.get_value(request_id)


def test_approve_unsubscribe_xgov_not_subscriber(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.approve_unsubscribe_xgov(
            args=ApproveUnsubscribeXgovArgs(
                request_id=xgov_registry_client.state.global_state.request_id - 1
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_approve_unsubscribe_xgov_not_xgov(
    algorand_client: AlgorandClient,
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov: SigningAccount,
) -> None:
    xgov_registry_client.send.request_unsubscribe_xgov(
        args=RequestUnsubscribeXgovArgs(
            xgov_address=xgov.address,
            owner_address=xgov.address,
            relation_type=0,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=xgov.address,
                    receiver=xgov_registry_client.app_address,
                    amount=get_xgov_fee(xgov_registry_client),
                )
            ),
        ),
        params=CommonAppCallParams(sender=xgov.address),
    )

    request_id = xgov_registry_client.state.global_state.request_id - 1

    # Unsubscribe the xGov directly (bypassing the request system, this is not possible in production)
    xgov_registry_client.send.unsubscribe_xgov(
        params=CommonAppCallParams(sender=xgov.address),
    )

    with pytest.raises(LogicError, match=err.NOT_XGOV):
        xgov_registry_client.send.approve_unsubscribe_xgov(
            args=ApproveUnsubscribeXgovArgs(request_id=request_id),
            params=CommonAppCallParams(sender=xgov_subscriber.address),
        )
