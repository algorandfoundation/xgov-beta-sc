import pytest
from algokit_utils import (
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_submitted_proposal_global_state,
    assign_voters,
    unassign_voters,
)


def test_unassign_unauthorized_submitted(
    no_role_account: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        composer = submitted_proposal_client.new_group()
        unassign_voters(
            composer,
            [],
            no_role_account,
        )
        composer.send()


def test_unassign_no_voters(
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        [],
        xgov_daemon,
    )
    composer.send()

    assert_submitted_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign_one_voter(
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        composer,
        committee[1:],
        xgov_daemon,
    )
    composer.send()
    old_assigned_members = submitted_proposal_client.state.global_state.assigned_members
    assert old_assigned_members == len(committee) - 1

    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[1:2],
        xgov_daemon,
    )
    composer.send()
    unassigned_voters = (
        old_assigned_members
        - submitted_proposal_client.state.global_state.assigned_members
    )
    assert unassigned_voters == 1

    assert_submitted_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=DEFAULT_MEMBER_VOTES * (len(committee) - 1 - unassigned_voters),
        assigned_members=len(committee) - 1 - unassigned_voters,
    )


@pytest.mark.parametrize(
    "proposal_client_fixture",
    [
        "proposal_client",
        "approved_proposal_client",
        "rejected_proposal_client",
        "funded_proposal_client",
        "blocked_proposal_client",
    ],
)
def test_unassign_wrong_proposal_status(
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    proposal_client_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    proposal_client: ProposalClient = request.getfixturevalue(proposal_client_fixture)
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        composer = proposal_client.new_group()
        unassign_voters(
            composer,
            committee,
            xgov_daemon,
        )
        composer.send()


def test_unassign_not_same_app(
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    submitted_proposal_client: ProposalClient,
    alternative_submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee=committee[1:],
    )
    composer.send()

    composer = alternative_submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee=committee[1:],
    )
    composer.send()

    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[1:],
        xgov_daemon,
    )
    composer.composer().build()

    alternative_composer = alternative_submitted_proposal_client.new_group()
    unassign_voters(
        alternative_composer,
        committee[1:],
        xgov_daemon,
    )
    alternative_composer.composer().build()

    alternative_composer.composer()._atc.txn_list[
        0
    ] = composer.composer()._atc.txn_list[0]
    alternative_composer.composer()._atc.method_dict[
        0
    ] = composer.composer()._atc.method_dict[0]

    with pytest.raises(LogicError, match=err.WRONG_APP_ID):
        alternative_composer.send()


def test_unassign_not_same_method(
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    composer.get_state(params=CommonAppCallParams(sender=xgov_daemon.address))
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )

    with pytest.raises(LogicError, match=err.WRONG_METHOD_CALL):
        composer.send()


def test_unassign_not_same_method_2(
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.get_state(params=CommonAppCallParams(sender=xgov_daemon.address))

    with pytest.raises(LogicError, match=err.WRONG_METHOD_CALL):
        composer.send()


def test_unassign_one_call_not_xgov_daemon(
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:-1],
        xgov_daemon,
    )
    unassign_voters(
        composer,
        committee[-1:],
        proposer,
    )
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        composer.send()


def test_unassign_final_proposal(
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee=committee[:1],
    )
    composer.send()

    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee[:1],
        xgov_daemon,
    )
    composer.send()

    assert_submitted_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
