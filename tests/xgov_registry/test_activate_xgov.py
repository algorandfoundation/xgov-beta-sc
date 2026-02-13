import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ActivateXgovArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err


def test_activate_xgov_success(
    xgov_subscriber: SigningAccount,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.unsubscribe_xgov(
        params=CommonAppCallParams(sender=xgov.address),
    )

    xgov_box = xgov_registry_client.state.box.xgov_box.get_value(xgov.address)
    assert xgov_box.unsubscribed_round > 0

    xgov_registry_client.send.activate_xgov(
        args=ActivateXgovArgs(xgov_address=xgov.address),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    xgov_box = xgov_registry_client.state.box.xgov_box.get_value(xgov.address)
    assert xgov_box.unsubscribed_round == 0


def test_activate_xgov_unauthorized(
    no_role_account: SigningAccount,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.unsubscribe_xgov(
        params=CommonAppCallParams(sender=xgov.address),
    )

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.activate_xgov(
            args=ActivateXgovArgs(xgov_address=xgov.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_activate_xgov_not_xgov(
    xgov_subscriber: SigningAccount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.NOT_XGOV):
        xgov_registry_client.send.activate_xgov(
            args=ActivateXgovArgs(xgov_address=no_role_account.address),
            params=CommonAppCallParams(sender=xgov_subscriber.address),
        )


def test_activate_xgov_already_active(
    xgov_subscriber: SigningAccount,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.ALREADY_XGOV):
        xgov_registry_client.send.activate_xgov(
            args=ActivateXgovArgs(xgov_address=xgov.address),
            params=CommonAppCallParams(sender=xgov_subscriber.address),
        )
