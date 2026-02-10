import pytest
from algokit_utils import AlgoAmount, CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
    UnassignAbsenteesArgs,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.enums import STATUS_APPROVED
from tests.common import DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import (
    assert_approved_proposal_global_state,
    assert_rejected_proposal_global_state,
    unassign_absentees,
)


def _run_unassign_and_assert(
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
    absentees_to_unassign: list[CommitteeMember],
) -> None:
    absentees = proposal_client.state.global_state.assigned_members
    status = proposal_client.state.global_state.status

    approvals = proposal_client.state.global_state.approvals
    rejections = proposal_client.state.global_state.rejections
    nulls = proposal_client.state.global_state.nulls

    composer = xgov_registry_mock_client.new_group()
    unassign_absentees(
        composer,
        proposal_client.app_id,
        absentees_to_unassign,
    )
    composer.send()

    unassigned_absentees = (
        absentees - proposal_client.state.global_state.assigned_members
    )
    voted_members = proposal_client.state.global_state.voted_members

    common_kwargs = {
        "proposer_address": proposer.address,
        "registry_app_id": xgov_registry_mock_client.app_id,
        "assigned_votes": DEFAULT_MEMBER_VOTES
        * (len(committee) - voted_members - unassigned_absentees),
        "assigned_members": len(committee) - voted_members - unassigned_absentees,
        "voted_members": voted_members,
        "approvals": approvals,
        "rejections": rejections,
        "nulls": nulls,
    }

    if status == STATUS_APPROVED:
        assert_approved_proposal_global_state(proposal_client, **common_kwargs)
    else:
        assert_rejected_proposal_global_state(proposal_client, **common_kwargs)


def test_unassign_rejected_no_absentee(
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    _run_unassign_and_assert(
        committee,
        proposer,
        xgov_registry_mock_client,
        rejected_proposal_client,
        absentees_to_unassign=[],
    )


@pytest.mark.parametrize(
    "proposal_fixture", ["rejected_proposal_client", "approved_proposal_client"]
)
def test_unassign_absentees(
    min_fee_times_3: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    proposal_client: ProposalClient = request.getfixturevalue(proposal_fixture)
    absentee_addresses = list(proposal_client.state.box.voters.get_map().keys())
    absentees_to_unassign = [
        cm for cm in committee if cm.account.address in absentee_addresses
    ][:1]
    _run_unassign_and_assert(
        committee,
        proposer,
        xgov_registry_mock_client,
        proposal_client,
        absentees_to_unassign=absentees_to_unassign,
    )


def test_unauthorized(
    no_role_account: SigningAccount,
    rejected_proposal_client: ProposalClient,
) -> None:
    absentees = list(rejected_proposal_client.state.box.voters.get_map().keys())
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        rejected_proposal_client.send.unassign_absentees(
            UnassignAbsenteesArgs(absentees=absentees),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


@pytest.mark.parametrize(
    "proposal_fixture",
    ["draft_proposal_client", "submitted_proposal_client", "voting_proposal_client"],
)
def test_wrong_status(
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    proposal_client: ProposalClient = request.getfixturevalue(proposal_fixture)
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        composer = xgov_registry_mock_client.new_group()
        unassign_absentees(
            composer,
            proposal_client.app_id,
            [],
        )
        composer.send()


def test_unassign_twice(
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    absentees = list(rejected_proposal_client.state.box.voters.get_map().keys())
    absentees.append(absentees[1])  # duplicate absentee to trigger error
    composer = xgov_registry_mock_client.new_group()
    unassign_absentees(composer, rejected_proposal_client.app_id, absentees)
    with pytest.raises(LogicError, match=err.VOTER_NOT_FOUND):
        composer.send()
