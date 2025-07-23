import pytest
from algokit_utils import SigningAccount, CommonAppCallParams, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, SetCommitteeManagerArgs,
)
from smart_contracts.errors import std_errors as err


def test_set_committee_manager_success(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.set_committee_manager(
        args=SetCommitteeManagerArgs(manager=no_role_account.address),
    )
    assert xgov_registry_client.state.global_state.committee_manager == no_role_account.address


def test_set_committee_manager_not_manager(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.set_committee_manager(
            args=SetCommitteeManagerArgs(manager=no_role_account.address),
            params=CommonAppCallParams(sender=no_role_account.address)
        )
