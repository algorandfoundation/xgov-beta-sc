import pytest
from algokit_utils import SigningAccount, CommonAppCallParams, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, RejectSubscribeXgovArgs, GetXgovBoxArgs,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err


def test_reject_subscribe_xgov_success(
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    xgov_registry_client.send.reject_subscribe_xgov(
        args=RejectSubscribeXgovArgs(
            request_id=xgov_registry_client.state.global_state.request_id - 1
        ),
        params=CommonAppCallParams(sender=xgov_subscriber.address)
    )

    with pytest.raises(LogicError, match="exists"):  # type: ignore
        xgov_registry_client.send.get_xgov_box(
            args=GetXgovBoxArgs(xgov_address=app_xgov_subscribe_requested.app_address)
        )


def test_reject_subscribe_xgov_not_subscriber(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.reject_subscribe_xgov(
            args=RejectSubscribeXgovArgs(
                request_id=xgov_registry_client.state.global_state.request_id - 1
            ),
            params=CommonAppCallParams(sender=no_role_account.address)
        )
