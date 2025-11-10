import pytest
from algokit_utils import AlgoAmount, CommonAppCallParams, LogicError, SigningAccount
from algosdk.error import AlgodHTTPError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    SetVotingAccountArgs,
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
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs

    xgov_registry_client.send.unsubscribe_xgov(
        params=CommonAppCallParams(sender=xgov.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs

    assert final_xgovs == initial_xgovs - 1

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.xgov_box.get_value(xgov.address)


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
        ),
    )

    xgov_subscriber_app.send.unsubscribe_xgov(
        args=AppUnsubscribeXgovArgs(app_id=xgov_registry_client.app_id),
    )


def test_unsubscribe_xgov_not_an_xgov(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.unsubscribe_xgov(
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_unsubscribe_xgov_voting_address(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov: SigningAccount,
) -> None:
    xgov_registry_client.send.set_voting_account(
        args=SetVotingAccountArgs(
            xgov_address=xgov.address,
            voting_address=no_role_account.address,
        ),
        params=CommonAppCallParams(sender=xgov.address),
    )

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.unsubscribe_xgov(
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_unsubscribe_xgov_paused_registry_error(
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    xgov_registry_client.send.pause_registry()

    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.unsubscribe_xgov(
            params=CommonAppCallParams(sender=xgov.address),
        )

    xgov_registry_client.send.resume_registry()

    xgov_registry_client.send.unsubscribe_xgov(
        params=CommonAppCallParams(sender=xgov.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs

    assert final_xgovs == initial_xgovs - 1

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.xgov_box.get_value(xgov.address)
