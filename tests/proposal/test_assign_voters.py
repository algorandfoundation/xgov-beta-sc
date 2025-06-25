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
    submit_proposal,
)

# TODO add tests for assign_voter on other statuses
from tests.utils import ERROR_TO_REGEX, time_warp


def test_assign_voters_success(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_backend=xgov_backend,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)]
        + [
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members
        ],
    )


def test_assign_voters_not_xgov_backend(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer = proposal_client.compose()
        assign_voters(
            proposal_client_composer=composer,
            xgov_backend=proposer,
            committee_members=[committee_member],
            xgov_registry_app_id=xgov_registry_mock_client.app_id,
            sp=sp,
        )
        composer.execute()

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)],  # no voter boxes
    )


def test_assign_voters_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
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
            xgov_backend=xgov_backend,
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
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_member: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = proposal_client.compose()
        assign_voters(
            proposal_client_composer=composer,
            xgov_backend=xgov_backend,
            committee_members=[committee_member],
            xgov_registry_app_id=xgov_registry_mock_client.app_id,
            sp=sp,
        )
        composer.execute()

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[(METADATA_BOX_KEY.encode(), METADATA_B64)],  # no voter box
    )


def test_assign_voters_voting_open(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_backend=xgov_backend,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = proposal_client.compose()
        assign_voters(
            proposal_client_composer=composer,
            xgov_backend=xgov_backend,
            committee_members=committee_members[:1],
            xgov_registry_app_id=xgov_registry_mock_client.app_id,
            sp=sp,
        )
        composer.execute()

    global_state = proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
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
    proposal_client: ProposalClient,
    alternative_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    not_proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    submit_proposal(
        alternative_proposal_client,
        algorand_client,
        not_proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = max(
        proposal_client.get_global_state().submission_ts,
        alternative_proposal_client.get_global_state().submission_ts,
    )
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize

    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    alternative_proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=not_proposer.address,
            signer=not_proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_backend=xgov_backend,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )

    alternative_composer = alternative_proposal_client.compose()
    assign_voters(
        proposal_client_composer=alternative_composer,
        xgov_backend=xgov_backend,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )

    alternative_composer.atc.txn_list[0] = composer.atc.txn_list[0]
    alternative_composer.atc.method_dict[0] = composer.atc.method_dict[0]

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_APP_ID]):
        alternative_composer.execute()


def test_assign_voters_not_same_method(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    composer.get_state(
        transaction_parameters=TransactionParameters(
            sender=xgov_backend.address,
            signer=xgov_backend.signer,
        ),
    )
    assign_voters(
        proposal_client_composer=composer,
        xgov_backend=xgov_backend,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.execute()


def test_assign_voters_not_same_method_2(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_backend=xgov_backend,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.get_state(
        transaction_parameters=TransactionParameters(
            sender=xgov_backend.address,
            signer=xgov_backend.signer,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.execute()


def test_assign_voters_one_call_not_xgov_backend(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_backend: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_backend.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_backend=xgov_backend,
        committee_members=committee_members[:-1],
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    assign_voters(
        proposal_client_composer=composer,
        xgov_backend=proposer,
        committee_members=[committee_members[-1]],
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer.execute()
