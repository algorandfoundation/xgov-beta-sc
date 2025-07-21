import pytest
from algokit_utils import SigningAccount, CommonAppCallParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, DeclareCommitteeArgs,
)
from smart_contracts.errors import std_errors as err
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
)
from tests.xgov_registry.common import (
    LogicErrorType,
    assert_committee,
)


def test_declare_committee_success(
    committee_manager: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> None:
    xgov_registry_client_committee_not_declared.send.declare_committee(
        args=DeclareCommitteeArgs(
            committee_id=DEFAULT_COMMITTEE_ID,
            size=DEFAULT_COMMITTEE_MEMBERS,
            votes=DEFAULT_COMMITTEE_VOTES,
        ),
        params=CommonAppCallParams(sender=committee_manager.address)
    )

    assert_committee(
        xgov_registry_client=xgov_registry_client_committee_not_declared,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_size=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
    )


def test_declare_committee_not_manager(
    no_role_account: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client_committee_not_declared.send.declare_committee(
            args=DeclareCommitteeArgs(
                committee_id=DEFAULT_COMMITTEE_ID,
                size=DEFAULT_COMMITTEE_MEMBERS,
                votes=DEFAULT_COMMITTEE_VOTES,
            ),
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_declare_committee_too_large(
    committee_manager: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> None:
    max_committee_size = (
        xgov_registry_client_committee_not_declared.state.global_state.max_committee_size
    )
    with pytest.raises(LogicErrorType, match=err.COMMITTEE_SIZE_TOO_LARGE):
        xgov_registry_client_committee_not_declared.send.declare_committee(
            args=DeclareCommitteeArgs(
                committee_id=DEFAULT_COMMITTEE_ID,
                size=max_committee_size+1,
                votes=DEFAULT_COMMITTEE_VOTES,
            ),
            params=CommonAppCallParams(sender=committee_manager.address)
        )
