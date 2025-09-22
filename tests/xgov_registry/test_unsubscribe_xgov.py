import pytest
from algokit_utils import AlgoAmount, CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetXgovBoxArgs,
    UnsubscribeXgovArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    SubscribeXgovArgs,
    XGovSubscriberAppMockClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    UnsubscribeXgovArgs as AppUnsubscribeXgovArgs,
)
from smart_contracts.errors import std_errors as err


def test_unsubscribe_xgov_success(
    xgov_registry_client: XGovRegistryClient,
    xgov: SigningAccount,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs

    xgov_registry_client.send.unsubscribe_xgov(
        args=UnsubscribeXgovArgs(xgov_address=xgov.address),
        params=CommonAppCallParams(sender=xgov.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs

    assert final_xgovs == initial_xgovs - 1

    with pytest.raises(LogicError, match="entry exists"):
        xgov_registry_client.send.get_xgov_box(
            args=GetXgovBoxArgs(xgov_address=xgov.address)
        )


def test_app_unsubscribe_xgov_success(
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> None:
    xgov_subscriber_app.send.subscribe_xgov(
        args=SubscribeXgovArgs(
            app_id=xgov_registry_client.app_id,
            voting_address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            static_fee=min_fee_times_3,
            app_references=[
                xgov_registry_client.app_id
            ],  # FIXME: This should have been autopopulated
        ),
    )

    xgov_subscriber_app.send.unsubscribe_xgov(
        args=AppUnsubscribeXgovArgs(app_id=xgov_registry_client.app_id),
        params=CommonAppCallParams(
            app_references=[
                xgov_registry_client.app_id
            ]  # FIXME: This should have been autopopulated
        ),
    )


def test_unsubscribe_xgov_not_an_xgov(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.unsubscribe_xgov(
            args=UnsubscribeXgovArgs(xgov_address=no_role_account.address)
        )


def test_unsubscribe_xgov_paused_registry_error(
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    xgov_registry_client.send.pause_registry()

    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.unsubscribe_xgov(
            args=UnsubscribeXgovArgs(xgov_address=xgov.address),
        )

    xgov_registry_client.send.resume_registry()

    xgov_registry_client.send.unsubscribe_xgov(
        args=UnsubscribeXgovArgs(xgov_address=xgov.address),
        params=CommonAppCallParams(sender=xgov.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs

    assert final_xgovs == initial_xgovs - 1

    with pytest.raises(LogicError, match="entry exists"):
        xgov_registry_client.send.get_xgov_box(
            args=GetXgovBoxArgs(xgov_address=xgov.address)
        )
