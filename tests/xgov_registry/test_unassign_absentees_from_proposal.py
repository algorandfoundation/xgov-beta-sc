import pytest
from algokit_utils import CommonAppCallParams, LogicError

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import CommitteeMember
from tests.proposal.common import presence_counts, unassign_absentees


@pytest.mark.parametrize(
    "proposal_fixture", ["rejected_proposal_client", "approved_proposal_client"]
)
def test_unassign(
    xgov_registry_client: XGovRegistryClient,
    proposal_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    proposal_client: ProposalClient = request.getfixturevalue(proposal_fixture)

    absentees = proposal_client.state.box.voters.get_map()

    before = presence_counts(xgov_registry_client, absentees)

    composer = xgov_registry_client.new_group()
    unassign_absentees(composer, proposal_client.app_id, absentees, op_up_count=3)
    composer.send()

    after = presence_counts(xgov_registry_client, absentees)

    assert after == {a: before[a] - 1 for a in absentees}


def test_unassign_with_unsubscribed_xgov(
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    absentees = rejected_proposal_client.state.box.voters.get_map()

    unsub_addr = next(iter(absentees))  # pick one absentee key
    kept_addrs = [a for a in absentees if a != unsub_addr]

    before = presence_counts(xgov_registry_client, absentees)

    unsub_member = next(m for m in committee if m.account.address == unsub_addr)
    xgov_registry_client.send.unsubscribe_xgov(
        params=CommonAppCallParams(sender=unsub_member.account.address)
    )

    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer, rejected_proposal_client.app_id, absentees, op_up_count=3
    )
    composer.send()

    after = presence_counts(xgov_registry_client, kept_addrs)

    assert after == {a: before[a] - 1 for a in kept_addrs}


def test_paused_registry(
    xgov_registry_client: XGovRegistryClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    xgov_registry_client.send.pause_registry()
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        rejected_proposal_client.app_id,
        [],
    )
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        composer.send()


def test_invalid_proposal(
    xgov_registry_client: XGovRegistryClient,
) -> None:
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        xgov_registry_client.app_id,
        [],
    )
    with pytest.raises(LogicError, match=err.INVALID_PROPOSAL):
        composer.send()


def test_wrong_proposal_status(
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> None:
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        voting_proposal_client.app_id,
        [],
    )
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        composer.send()


def test_unassign_twice(
    xgov_registry_client: XGovRegistryClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    absentees = list(rejected_proposal_client.state.box.voters.get_map().keys())
    absentees.append(absentees[1])  # duplicate absentee to trigger error
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer, rejected_proposal_client.app_id, absentees, op_up_count=3
    )
    with pytest.raises(LogicError, match=err.VOTER_NOT_FOUND):
        composer.send()
