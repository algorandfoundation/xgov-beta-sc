import pytest
from algokit_utils import LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    UnsubscribeAbsenteeArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import CommitteeMember


@pytest.mark.skip(reason="Not reachable on LocalNet, just used on public deployments")
def test_unsubscribe_absentee(
    xgov_registry_client: XGovRegistryClient,
    absentee_committee: list[CommitteeMember],
) -> None:
    # The initial state of this test is not easily reachable on LocalNet, since it
    # needs an xGov with 0 tolerated absence that has not been already removed by
    # the `unassign_absentees_from_proposal` method. This state was a consequence
    # of the xGov Registry update on public deployments, which needed a first removal
    # at the inception of the absenteeism penalty mechanism.
    xgov_registry_client.send.unsubscribe_absentee(
        args=UnsubscribeAbsenteeArgs(xgov_address=absentee_committee[0].account.address)
    )


def test_paused_registry(
    xgov_registry_client: XGovRegistryClient,
    absentee_committee: list[CommitteeMember],
) -> None:
    xgov_registry_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.unsubscribe_absentee(
            args=UnsubscribeAbsenteeArgs(
                xgov_address=absentee_committee[0].account.address
            )
        )


def test_not_xgov(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.NOT_XGOV):
        xgov_registry_client.send.unsubscribe_absentee(
            args=UnsubscribeAbsenteeArgs(xgov_address=no_role_account.address)
        )


def test_unauthorized(
    xgov_registry_client: XGovRegistryClient,
    subscribed_committee: list[CommitteeMember],
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.unsubscribe_absentee(
            args=UnsubscribeAbsenteeArgs(
                xgov_address=subscribed_committee[0].account.address
            )
        )
