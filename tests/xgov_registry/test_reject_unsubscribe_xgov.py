import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount
from algosdk.error import AlgodHTTPError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    RejectUnsubscribeXgovArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err


def test_reject_unsubscribe_xgov_success(
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    request_id = xgov_registry_client.state.global_state.request_id - 1
    xgov_registry_client.send.reject_unsubscribe_xgov(
        args=RejectUnsubscribeXgovArgs(request_id=request_id),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    assert xgov_registry_client.state.box.xgov_box.get_value(
        app_xgov_unsubscribe_requested.app_address
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.request_unsubscribe_box.get_value(request_id)


def test_reject_unsubscribe_xgov_not_subscriber(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.reject_unsubscribe_xgov(
            args=RejectUnsubscribeXgovArgs(
                request_id=xgov_registry_client.state.global_state.request_id - 1
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
