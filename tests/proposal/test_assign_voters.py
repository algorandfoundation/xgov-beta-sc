import pytest
from algokit_utils import TransactionParameters, SigningAccount, LogicError, AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY

from tests.proposal.common import (
    LOCKED_AMOUNT,
    METADATA_B64,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_boxes,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_final_proposal_global_state,
    assert_voting_proposal_global_state,
    assign_voters,
    get_voter_box_key
)
from tests.utils import ERROR_TO_REGEX

# TODO add tests for assign_voter on other statuses


def test_assign_voters_success(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )
    composer.send()

    assert_voting_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=submitted_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)]
        + [
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members
        ],
    )


def test_assign_voters_not_xgov_daemon(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_member: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer = submitted_proposal_client.new_group()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=proposer,
            committee_members=[committee_member],
        )
        composer.send()

    assert_final_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=submitted_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)],  # no voter boxes
    )


def test_assign_voters_empty_proposal(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_member: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]):
        composer = proposal_client.new_group()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=xgov_daemon,
            committee_members=[committee_member],
        )
        composer.send()

    assert_empty_proposal_global_state(
        proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[],  # no voter box
    )


def test_assign_voters_draft_proposal(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_member: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]):
        composer = draft_proposal_client.new_group()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=xgov_daemon,
            committee_members=[committee_member],
        )
        composer.send()

    assert_draft_proposal_global_state(
        draft_proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        draft_proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)],  # no voter box
    )


def test_assign_voters_voting_open(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )
    composer.send()

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]):
        composer = submitted_proposal_client.new_group()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=xgov_daemon,
            committee_members=committee_members[:1],
        )
        composer.send()

    assert_voting_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=submitted_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)]
        + [
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members
        ],
    )


def test_assign_voters_not_same_app(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    alternative_submitted_proposal_client: ProposalClient,
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )

    alternative_composer = alternative_submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=alternative_composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )

    alternative_composer.composer()._atc.txn_list[0] = composer.composer()._atc.txn_list[0]
    alternative_composer.composer()._atc.method_dict[0] = composer.composer()._atc.method_dict[0]

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_APP_ID]):
        alternative_composer.send()


def test_assign_voters_not_same_method(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    composer.get_state()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.send()


def test_assign_voters_not_same_method_2(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
    )
    composer.get_state()

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.send()


def test_assign_voters_one_call_not_xgov_daemon(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members[:-1],
    )
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=proposer,
        committee_members=[committee_members[-1]],
    )
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer.send()


def test_assign_voters_more_than_allowed(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee_members: list[SigningAccount],
    xgov_registry_mock_client: XgovRegistryMockClient,
    submitted_proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    composer = submitted_proposal_client.new_group()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=[*committee_members, proposer],
    )
    composer.send()

    assert_final_proposal_global_state(
        submitted_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=10 * (len(committee_members) + 1),  # proposer is also assigned
        voters_count=len(committee_members) + 1,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=submitted_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)]
        + [
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in [*committee_members, proposer]
        ],
    )
