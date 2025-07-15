import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
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
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
    committee_manager: AddressAndSigner,
) -> None:
    xgov_registry_client_committee_not_declared.declare_committee(
        committee_id=DEFAULT_COMMITTEE_ID,
        size=DEFAULT_COMMITTEE_MEMBERS,
        votes=DEFAULT_COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=committee_manager.address,
            signer=committee_manager.signer,
        ),
    )

    global_state = xgov_registry_client_committee_not_declared.get_global_state()

    assert_committee(
        global_state=global_state,
        committee_id=DEFAULT_COMMITTEE_ID,
        committee_size=DEFAULT_COMMITTEE_MEMBERS,
        committee_votes=DEFAULT_COMMITTEE_VOTES,
    )


def test_declare_committee_not_manager(
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
    no_role_account: AddressAndSigner,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client_committee_not_declared.declare_committee(
            committee_id=DEFAULT_COMMITTEE_ID,
            size=DEFAULT_COMMITTEE_MEMBERS,
            votes=DEFAULT_COMMITTEE_VOTES,
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
            ),
        )


def test_declare_committee_too_large(
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
    committee_manager: AddressAndSigner,
) -> None:
    max_committee_size = (
        xgov_registry_client_committee_not_declared.get_global_state().max_committee_size
    )
    with pytest.raises(LogicErrorType, match=err.COMMITTEE_SIZE_TOO_LARGE):
        xgov_registry_client_committee_not_declared.declare_committee(
            committee_id=DEFAULT_COMMITTEE_ID,
            size=max_committee_size + 1,
            votes=DEFAULT_COMMITTEE_VOTES,
            transaction_parameters=TransactionParameters(
                sender=committee_manager.address,
                signer=committee_manager.signer,
            ),
        )
