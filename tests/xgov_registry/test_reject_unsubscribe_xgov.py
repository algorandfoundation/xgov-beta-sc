import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetRequestUnsubscribeBoxArgs,
    GetXgovBoxArgs,
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
    request_unsubscribe_id = (
        xgov_registry_client.state.global_state.request_unsubscribe_id - 1
    )
    xgov_registry_client.send.reject_unsubscribe_xgov(
        args=RejectUnsubscribeXgovArgs(request_unsubscribe_id=request_unsubscribe_id),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    assert xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(xgov_address=app_xgov_unsubscribe_requested.app_address)
    )

    with pytest.raises(LogicError, match="exists"):
        xgov_registry_client.send.get_request_unsubscribe_box(
            args=GetRequestUnsubscribeBoxArgs(
                request_unsubscribe_id=request_unsubscribe_id
            )
        )


def test_reject_unsubscribe_xgov_not_subscriber(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.reject_unsubscribe_xgov(
            args=RejectUnsubscribeXgovArgs(
                request_unsubscribe_id=xgov_registry_client.state.global_state.request_unsubscribe_id
                - 1
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
