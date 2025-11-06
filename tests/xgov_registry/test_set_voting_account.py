import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    SetVotingAccountArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err


def test_set_voting_account_as_xgov(
    no_role_account: SigningAccount,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_box = xgov_registry_client.state.box.xgov_box.get_value(xgov.address)
    assert xgov_box.voting_address == xgov.address  # type: ignore

    xgov_registry_client.send.set_voting_account(
        args=SetVotingAccountArgs(
            xgov_address=xgov.address,
            voting_address=no_role_account.address,
        ),
        params=CommonAppCallParams(sender=xgov.address),
    )

    xgov_box = xgov_registry_client.state.box.xgov_box.get_value(xgov.address)
    assert xgov_box.voting_address == no_role_account.address  # type: ignore


def test_set_voting_account_not_an_xgov(
    no_role_account: SigningAccount,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.set_voting_account(
            args=SetVotingAccountArgs(
                xgov_address=xgov.address,
                voting_address=no_role_account.address,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_set_voting_account_as_voting_address(
    no_role_account: SigningAccount,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.set_voting_account(
        args=SetVotingAccountArgs(
            xgov_address=xgov.address,
            voting_address=no_role_account.address,
        ),
        params=CommonAppCallParams(sender=xgov.address),
    )

    xgov_registry_client.send.set_voting_account(
        args=SetVotingAccountArgs(
            xgov_address=xgov.address,
            voting_address=xgov.address,
        ),
        params=CommonAppCallParams(sender=no_role_account.address),
    )


def test_set_voting_account_paused_registry_error(
    no_role_account: SigningAccount,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.set_voting_account(
            args=SetVotingAccountArgs(
                xgov_address=xgov.address,
                voting_address=no_role_account.address,
            ),
            params=CommonAppCallParams(sender=xgov.address),
        )

    xgov_registry_client.send.resume_registry()

    xgov_registry_client.send.set_voting_account(
        args=SetVotingAccountArgs(
            xgov_address=xgov.address,
            voting_address=no_role_account.address,
        ),
        params=CommonAppCallParams(sender=xgov.address),
    )
