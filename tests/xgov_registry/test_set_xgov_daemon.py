import pytest
from algokit_utils import CommonAppCallParams, SigningAccount, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, SetXgovDaemonArgs,
)
from smart_contracts.errors import std_errors as err


def test_set_xgov_daemon_success(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.set_xgov_daemon(
        args=SetXgovDaemonArgs(xgov_daemon=no_role_account.address),
    )
    assert xgov_registry_client.state.global_state.xgov_daemon == no_role_account.address


def test_set_xgov_daemon_not_manager(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.set_xgov_daemon(
            args=SetXgovDaemonArgs(xgov_daemon=no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address)
        )
