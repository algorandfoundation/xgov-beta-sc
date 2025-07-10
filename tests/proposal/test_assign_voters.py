import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY

# TODO add tests for assign_voter on other statuses
from tests.common import METADATA_B64, get_voter_box_key
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_boxes,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_final_proposal_global_state,
    assert_voting_proposal_global_state,
    assign_voters,
    logic_error_type,
)

# TODO add tests for assign_voter on other statuses
from tests.utils import ERROR_TO_REGEX


def test_assign_voters_success(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    composer = finalized_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    global_state = finalized_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=finalized_proposal_client.app_id,
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
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer = finalized_proposal_client.compose()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=proposer,
            committee_members=[committee_member],
            xgov_registry_app_id=xgov_registry_mock_client.app_id,
            sp=sp,
        )
        composer.execute()

    global_state = finalized_proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=finalized_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)],  # no voter boxes
    )


def test_assign_voters_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = proposal_client.compose()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=xgov_daemon,
            committee_members=[committee_member],
            xgov_registry_app_id=xgov_registry_mock_client.app_id,
            sp=sp,
        )
        composer.execute()

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[],  # no voter box
    )


def test_assign_voters_draft_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = submitted_proposal_client.compose()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=xgov_daemon,
            committee_members=[committee_member],
            xgov_registry_app_id=xgov_registry_mock_client.app_id,
            sp=sp,
        )
        composer.execute()

    global_state = submitted_proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        submitted_proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=submitted_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)],  # no voter box
    )


def test_assign_voters_voting_open(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    composer = finalized_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = finalized_proposal_client.compose()
        assign_voters(
            proposal_client_composer=composer,
            xgov_daemon=xgov_daemon,
            committee_members=committee_members[:1],
            xgov_registry_app_id=xgov_registry_mock_client.app_id,
            sp=sp,
        )
        composer.execute()

    global_state = finalized_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=finalized_proposal_client.app_id,
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
    finalized_proposal_client: ProposalClient,
    alternative_finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    composer = finalized_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )

    alternative_composer = alternative_finalized_proposal_client.compose()
    assign_voters(
        proposal_client_composer=alternative_composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )

    alternative_composer.atc.txn_list[0] = composer.atc.txn_list[0]
    alternative_composer.atc.method_dict[0] = composer.atc.method_dict[0]

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_APP_ID]):
        alternative_composer.execute()


def test_assign_voters_not_same_method(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    composer = finalized_proposal_client.compose()
    composer.get_state(
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
        ),
    )
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.execute()


def test_assign_voters_not_same_method_2(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    composer = finalized_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.get_state(
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.execute()


def test_assign_voters_one_call_not_xgov_daemon(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    composer = finalized_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members[:-1],
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=proposer,
        committee_members=[committee_members[-1]],
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer.execute()


def test_assign_voters_more_than_allowed(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    composer = finalized_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=[*committee_members, proposer],
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    global_state = finalized_proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=10 * (len(committee_members) + 1),  # proposer is also assigned
        voters_count=len(committee_members) + 1,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=finalized_proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)]
        + [
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in [*committee_members, proposer]
        ],
    )
