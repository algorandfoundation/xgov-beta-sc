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
from tests.common import CommitteeMember
from tests.proposal.common import (
    assert_account_balance,
    finalize_proposal,
    unassign_voters,
)


@pytest.mark.parametrize(
    "proposal_client_fixture",
    [
        "proposal_client",
        "draft_proposal_client",
        "submitted_proposal_client",
        "voting_proposal_client",
        "approved_proposal_client",
        "reviewed_proposal_client",
        "rejected_proposal_client",
        "blocked_proposal_client",
        "funded_proposal_client",
    ],
)
def test_delete_wrong_status(
    proposal_client_fixture: str,
    min_fee_times_3: AlgoAmount,
    xgov_daemon: SigningAccount,
    request: pytest.FixtureRequest,
) -> None:
    client: ProposalClient = request.getfixturevalue(proposal_client_fixture)
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        client.send.delete.delete(
            params=CommonAppCallParams(
                sender=xgov_daemon.address, static_fee=min_fee_times_3
            )
        )


def test_delete_success(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
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
    committee: list[CommitteeMember],
    no_role_account: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
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
