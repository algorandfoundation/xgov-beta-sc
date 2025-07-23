import pytest
from algokit_utils import SigningAccount, AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err

# TODO add tests for submit on other statuses
from tests.common import (
    relative_to_absolute_amount,
)
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_final_proposal_global_state,
    open_proposal,
    submit_proposal,
)


def test_submit_success(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
    proposer: SigningAccount,
) -> None:
    reg_gs = xgov_registry_mock_client.state.global_state

    daemon_ops_funding_bps = relative_to_absolute_amount(
        reg_gs.open_proposal_fee, reg_gs.daemon_ops_funding_bps
    )
    xgov_daemon_balance_before_submit = algorand_client.account.get_information(xgov_daemon.address).amount.micro_algo

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_mock_client,
        proposer=proposer,
    )

    assert_account_balance(
        algorand_client=algorand_client,
        address=xgov_daemon.address,
        expected_balance=xgov_daemon_balance_before_submit + daemon_ops_funding_bps,  # type: ignore
    )

    assert_final_proposal_global_state(
        draft_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_submit_not_proposer(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    no_role_account: SigningAccount,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_mock_client=xgov_registry_mock_client,
            proposer=no_role_account,
            xgov_daemon=xgov_daemon,
            sp_min_fee_times_2=sp,
        )

    global_state = draft_proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        draft_proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )


def test_submit_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        submit_proposal(
            proposal_client=proposal_client,
            xgov_registry_mock_client=xgov_registry_mock_client,
            proposer=proposer,
            xgov_daemon=xgov_daemon,
            sp_min_fee_times_2=sp,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )


def test_submit_twice(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_mock_client=xgov_registry_mock_client,
        proposer=proposer,
        xgov_daemon=xgov_daemon,
        sp_min_fee_times_2=sp,
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_mock_client=xgov_registry_mock_client,
            proposer=proposer,
            xgov_daemon=xgov_daemon,
            sp_min_fee_times_2=sp,
        )

    global_state = draft_proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_submit_too_early(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.TOO_EARLY]):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_mock_client=xgov_registry_mock_client,
            proposer=proposer,
            xgov_daemon=xgov_daemon,
            sp_min_fee_times_2=sp,
            should_time_warp=False,
        )

    global_state = draft_proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        draft_proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )


def test_submit_no_metadata(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        metadata=b"",
    )

    sp = sp_min_fee_times_2

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.MISSING_METADATA]):
        submit_proposal(
            proposal_client=proposal_client,
            xgov_registry_mock_client=xgov_registry_mock_client,
            proposer=proposer,
            xgov_daemon=xgov_daemon,
            sp_min_fee_times_2=sp,
        )


def test_submit_paused_registry_error(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    reg_gs = xgov_registry_mock_client.get_global_state()

    daemon_ops_funding_bps = relative_to_absolute_amount(
        reg_gs.open_proposal_fee, reg_gs.daemon_ops_funding_bps
    )
    xgov_daemon_balance_before_submit = algorand_client.account.get_information(  # type: ignore
        xgov_daemon.address
    )[
        "amount"
    ]

    xgov_registry_mock_client.pause_registry()
    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_mock_client=xgov_registry_mock_client,
            proposer=proposer,
            xgov_daemon=xgov_daemon,
            sp_min_fee_times_2=sp,
        )

    xgov_registry_mock_client.resume_registry()

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_mock_client=xgov_registry_mock_client,
        proposer=proposer,
        xgov_daemon=xgov_daemon,
        sp_min_fee_times_2=sp,
    )

    assert_account_balance(
        algorand_client=algorand_client,
        address=xgov_daemon.address,
        expected_balance=xgov_daemon_balance_before_submit + daemon_ops_funding_bps,  # type: ignore
    )

    global_state = draft_proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
