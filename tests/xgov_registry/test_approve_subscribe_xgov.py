import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ApproveSubscribeXgovArgs,
    GetXgovBoxArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err


def test_approve_subscribe_xgov_success(
    no_role_account: SigningAccount,
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    xgov_registry_client.send.approve_subscribe_xgov(
        args=ApproveSubscribeXgovArgs(
            request_id=xgov_registry_client.state.global_state.request_id - 1
        ),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs
    assert final_xgovs == initial_xgovs + 1

    xgov_box = xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(
            xgov_address=app_xgov_subscribe_requested.app_address,
        ),
    ).abi_return

    assert no_role_account.address == xgov_box.voting_address  # type: ignore


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
