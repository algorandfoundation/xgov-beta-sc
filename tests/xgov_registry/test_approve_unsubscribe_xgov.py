import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ApproveUnsubscribeXgovArgs,
    GetRequestUnsubscribeBoxArgs,
    GetXgovBoxArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err


def test_approve_unsubscribe_xgov_success(
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    request_unsubscribe_id = (
        xgov_registry_client.state.global_state.request_unsubscribe_id - 1
    )
    xgov_registry_client.send.approve_unsubscribe_xgov(
        args=ApproveUnsubscribeXgovArgs(request_unsubscribe_id=request_unsubscribe_id),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs
    assert final_xgovs == initial_xgovs - 1

    with pytest.raises(LogicError, match="entry exists"):
        xgov_registry_client.send.get_xgov_box(
            args=GetXgovBoxArgs(xgov_address=app_xgov_unsubscribe_requested.app_address)
        )

    with pytest.raises(LogicError, match="exists"):
        xgov_registry_client.send.get_request_unsubscribe_box(
            args=GetRequestUnsubscribeBoxArgs(
                request_unsubscribe_id=request_unsubscribe_id
            )
        )


def test_approve_unsubscribe_xgov_not_subscriber(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.approve_unsubscribe_xgov(
            args=ApproveUnsubscribeXgovArgs(
                request_unsubscribe_id=xgov_registry_client.state.global_state.request_unsubscribe_id
                - 1
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
