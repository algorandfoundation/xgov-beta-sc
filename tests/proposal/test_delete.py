import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.proposal.common import (
    assert_account_balance,
    finalize_proposal,
    unassign_voters,
)


def test_delete_empty_proposal(
    proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        draft_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_final_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        submitted_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        voting_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_approved_proposal(
    approved_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        approved_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_reviewed_proposal(
    reviewed_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        reviewed_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        rejected_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_blocked_proposal(
    blocked_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        blocked_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )


def test_delete_funded_proposal(
    funded_proposal_client: ProposalClient,
    xgov_daemon: SigningAccount,
    min_fee_times_3: AlgoAmount,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        funded_proposal_client.send.delete.delete(
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_3
            )
        )


def test_delete_success(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    min_fee_times_2: AlgoAmount,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
    )
    composer.send()

    finalize_proposal(
        xgov_registry_mock_client,
        rejected_proposal_client.app_id,
        xgov_daemon,
    )

    rejected_proposal_client.send.delete.delete(
        params=CommonAppCallParams(
            sender=xgov_daemon.address, static_fee=min_fee_times_2
        )
    )

    assert_account_balance(algorand_client, rejected_proposal_client.app_address, 0)

    with pytest.raises(Exception, match="application does not exist"):
        algorand_client.client.algod.application_info(rejected_proposal_client.app_id)


def test_delete_not_xgov_daemon(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    no_role_account: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
    )
    composer.send()

    finalize_proposal(
        xgov_registry_mock_client,
        rejected_proposal_client.app_id,
        xgov_daemon,
    )

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rejected_proposal_client.send.delete.delete(
            params=CommonAppCallParams(sender=no_role_account.address)
        )
