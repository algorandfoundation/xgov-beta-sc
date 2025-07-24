import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    SetPayorArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err


def test_set_payor_success(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.set_payor(
        args=SetPayorArgs(payor=no_role_account.address)
    )
    assert xgov_registry_client.state.global_state.xgov_payor == no_role_account.address


def test_set_payor_not_manager(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.set_payor(
            args=SetPayorArgs(payor=no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
