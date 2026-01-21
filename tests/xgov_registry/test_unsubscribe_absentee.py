import pytest
from algokit_utils import LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    UnsubscribeAbsenteeArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import CommitteeMember


def test_unsubscribe_absentee(
    xgov_registry_client: XGovRegistryClient,
    absentee_committee: list[CommitteeMember],
) -> None:
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
