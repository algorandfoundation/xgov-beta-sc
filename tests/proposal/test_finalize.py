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

# TODO add tests for finalize on other statuses
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    relative_to_absolute_amount,
)
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_final_proposal_global_state,
    logic_error_type,
    submit_proposal,
)

# TODO add tests for finalize on other statuses
from tests.utils import ERROR_TO_REGEX, get_latest_timestamp, time_warp
from tests.xgov_registry.common import LogicErrorType


def test_finalize_success(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    publishing_fee = relative_to_absolute_amount(
        reg_gs.proposal_fee, reg_gs.publishing_fee_bps
    )
    xgov_daemon_balance_before_finalize = algorand_client.account.get_information(  # type: ignore
        xgov_daemon.address
    )[
        "amount"
    ]

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY.encode())],
        ),
    )

    assert_account_balance(
        algorand_client=algorand_client,
        address=xgov_daemon.address,
        expected_balance=xgov_daemon_balance_before_finalize + publishing_fee,  # type: ignore
    )

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_finalize_not_proposer(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    not_proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[xgov_daemon.address],
                boxes=[(0, METADATA_BOX_KEY.encode())],
            ),
        )

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


def test_finalize_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    latest_ts = get_latest_timestamp(algorand_client.client.algod)
    time_warp(latest_ts + discussion_duration)  # so we could actually finalize
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[xgov_daemon.address],
                boxes=[(0, METADATA_BOX_KEY.encode())],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )


def test_finalize_twice(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
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
            suggested_params=sp,
            accounts=[xgov_daemon.address],
            boxes=[(0, METADATA_BOX_KEY.encode())],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[xgov_daemon.address],
                note="Second finalize",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_finalize_too_early(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.TOO_EARLY]):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[xgov_daemon.address],
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )

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


def test_finalize_no_metadata(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        metadata=b"",
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.MISSING_METADATA]):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                accounts=[xgov_daemon.address],
                boxes=[(0, METADATA_BOX_KEY.encode())],
                suggested_params=sp,
            ),
        )


def test_finalize_wrong_committee_id(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    xgov_registry_mock_client.clear_committee_id()  # invalid committee id
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.EMPTY_COMMITTEE_ID]):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                accounts=[xgov_daemon.address],
                boxes=[(0, METADATA_BOX_KEY.encode())],
                suggested_params=sp,
            ),
        )

    xgov_registry_mock_client.set_committee_id(
        committee_id=DEFAULT_COMMITTEE_ID
    )  # restore

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )


def test_finalize_wrong_committee_members(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    xgov_registry_mock_client.set_committee_members(
        committee_members=0
    )  # invalid committee members
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_COMMITTEE_MEMBERS]
    ):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                accounts=[xgov_daemon.address],
                boxes=[(0, METADATA_BOX_KEY.encode())],
                suggested_params=sp,
            ),
        )

    xgov_registry_mock_client.set_committee_members(
        committee_members=DEFAULT_COMMITTEE_MEMBERS
    )  # restore

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )


def test_finalize_wrong_committee_votes(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    xgov_registry_mock_client.set_committee_votes(
        committee_votes=0
    )  # invalid committee votes
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_COMMITTEE_VOTES]
    ):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                accounts=[xgov_daemon.address],
                boxes=[(0, METADATA_BOX_KEY.encode())],
                suggested_params=sp,
            ),
        )

    xgov_registry_mock_client.set_committee_votes(
        committee_votes=DEFAULT_COMMITTEE_VOTES
    )  # restore

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )


def test_finalize_paused_registry_error(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    publishing_fee = relative_to_absolute_amount(
        reg_gs.proposal_fee, reg_gs.publishing_fee_bps
    )
    xgov_daemon_balance_before_finalize = algorand_client.account.get_information(  # type: ignore
        xgov_daemon.address
    )[
        "amount"
    ]

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize

    xgov_registry_mock_client.pause_registry()
    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        proposal_client.finalize(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                accounts=[xgov_daemon.address],
                suggested_params=sp,
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )

    xgov_registry_mock_client.resume_registry()

    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    assert_account_balance(
        algorand_client=algorand_client,
        address=xgov_daemon.address,
        expected_balance=xgov_daemon_balance_before_finalize + publishing_fee,  # type: ignore
    )

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
