import pytest
from algokit_utils import AlgorandClient, SigningAccount, LogicError

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient, UnassignVotersArgs
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import (
    assert_blocked_proposal_global_state,
    assert_final_proposal_global_state,
    assert_funded_proposal_global_state,
    assert_rejected_proposal_global_state,
    assign_voters,
    unassign_voters,
)
from tests.utils import ERROR_TO_REGEX, time_warp

# TODO add tests for unassign on other statuses


def test_unassign_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    with pytest.raises(
        LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = proposal_client.new_group()
        unassign_voters(
            composer,
            committee_members,
            xgov_daemon,
        )
        composer.send()


def test_unassign_unauthorized(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer = submitted_proposal_client.new_group()
        unassign_voters(
            composer,
            [],
            proposer,
        )
        composer.send()


def test_unassign_no_voters(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        [],
        xgov_daemon,
    )
    composer.send()

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign_one_voter(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:1],
        xgov_daemon,
    )
    composer.send()

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_rejected_not_daemon(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    no_role_account: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:1],
        no_role_account,
    )
    composer.send()

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_funded_not_daemon(
    funded_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    no_role_account: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = funded_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:1],
        no_role_account,
    )
    composer.send()

    assert_funded_proposal_global_state(
        funded_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_blocked_not_daemon(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    no_role_account: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = blocked_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:1],
        no_role_account,
    )
    composer.send()

    assert_blocked_proposal_global_state(
        blocked_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_all_voters(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
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

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=0,
        voters_count=0,
    )


def test_unassign_metadata_ref(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    with pytest.raises(LogicError, match="invalid Box reference"):
        rejected_proposal_client.send.unassign_voters(
            args=UnassignVotersArgs(voters=[committee_members[0].address]),
        )

    assert_rejected_proposal_global_state(
        rejected_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign_not_same_app(
    submitted_proposal_client: ProposalClient,
    alternative_submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    no_role_account: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )
    composer.send()

    composer = alternative_submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )
    composer.send()

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = max(
        submitted_proposal_client.state.global_state.vote_open_ts,
        alternative_submitted_proposal_client.state.global_state.vote_open_ts,
    )
    time_warp(vote_open_ts + voting_duration + 1)

    submitted_proposal_client.send.scrutiny()
    alternative_submitted_proposal_client.send.scrutiny(
    )

    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
    )

    alternative_composer = alternative_submitted_proposal_client.new_group()
    unassign_voters(
        alternative_composer,
        committee_members,
        xgov_daemon,
    )

    alternative_composer.composer()._atc.txn_list[0] = composer.composer()._atc.txn_list[0]
    alternative_composer.composer()._atc.method_dict[0] = composer.composer()._atc.method_dict[0]

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_APP_ID]):
        alternative_composer.send()


def test_unassign_not_same_method(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    composer.get_state()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.send()


def test_unassign_not_same_method_2(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = rejected_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
    )
    composer.get_state()

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.send()


def test_unassign_one_call_not_xgov_daemon(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:-1],
        xgov_daemon,
    )
    unassign_voters(
        composer,
        committee_members[-1:],
        proposer,
    )
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer.send()


def test_unassign_final_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members[:1],
    )
    composer.send()

    composer = submitted_proposal_client.new_group()
    unassign_voters(
        composer,
        committee_members[:1],
        xgov_daemon,
    )
    composer.send()

    assert_final_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
