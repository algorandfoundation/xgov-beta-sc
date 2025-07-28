import pytest
from algokit_utils import AlgorandClient, LogicError, SigningAccount

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
    xgov_daemon_balance_before_submit = algorand_client.account.get_information(
        xgov_daemon.address
    ).amount.micro_algo

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_mock_client,
        proposer=proposer,
    )

    assert_account_balance(
        algorand_client=algorand_client,
        address=xgov_daemon.address,
        expected_balance=xgov_daemon_balance_before_submit + daemon_ops_funding_bps,
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
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_client=xgov_registry_mock_client,
            proposer=no_role_account,
        )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        draft_proposal_client.app_address,
        LOCKED_AMOUNT.micro_algo + PROPOSAL_PARTIAL_FEE,
    )


def test_submit_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        submit_proposal(
            proposal_client=proposal_client,
            xgov_registry_client=xgov_registry_mock_client,
            proposer=proposer,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )


def test_submit_twice(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
) -> None:
    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_mock_client,
        proposer=proposer,
    )

    with pytest.raises(
        LogicError,
        match=err.WRONG_PROPOSAL_STATUS,
    ):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_client=xgov_registry_mock_client,
            proposer=proposer,
        )

    assert_final_proposal_global_state(
        draft_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_submit_too_early(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
) -> None:
    with pytest.raises(LogicError, match=err.TOO_EARLY):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_client=xgov_registry_mock_client,
            proposer=proposer,
            should_time_warp=False,
        )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        draft_proposal_client.app_address,
        LOCKED_AMOUNT.micro_algo + PROPOSAL_PARTIAL_FEE,
    )


def test_submit_no_metadata(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
) -> None:

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        metadata=b"",
    )
    with pytest.raises(LogicError, match=err.MISSING_METADATA):
        submit_proposal(
            proposal_client=proposal_client,
            xgov_registry_client=xgov_registry_mock_client,
            proposer=proposer,
        )


def test_submit_paused_registry_error(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: SigningAccount,
) -> None:
    reg_gs = xgov_registry_mock_client.state.global_state

    daemon_ops_funding_bps = relative_to_absolute_amount(
        reg_gs.open_proposal_fee, reg_gs.daemon_ops_funding_bps
    )
    xgov_daemon_balance_before_submit = algorand_client.account.get_information(
        xgov_daemon.address
    ).amount.micro_algo

    xgov_registry_mock_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_client=xgov_registry_mock_client,
            proposer=proposer,
        )

    xgov_registry_mock_client.send.resume_registry()

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_mock_client,
        proposer=proposer,
    )

    assert_account_balance(
        algorand_client=algorand_client,
        address=xgov_daemon.address,
        expected_balance=xgov_daemon_balance_before_submit + daemon_ops_funding_bps,
    )

    assert_final_proposal_global_state(
        draft_proposal_client,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
