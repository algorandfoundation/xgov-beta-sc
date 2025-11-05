import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)
from algosdk.error import AlgodHTTPError

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    DropProposalArgs,
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
)

# TODO add tests for drop on other statuses

NO_COMMITTEE = {
    "committee_id": b"",
    "committee_members": 0,
    "committee_votes": 0,
    "assigned_votes": 0,
    "voters_count": 0,
}


def test_drop_success(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient
) -> None:
    proposer_balance_before_drop = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    xgov_registry_mock_client.send.drop_proposal(
        args=DropProposalArgs(proposal_app=draft_proposal_client.app_id),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3),
    )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )

    assert_account_balance(
        algorand_client, draft_proposal_client.app_address, PROPOSAL_PARTIAL_FEE
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before_drop
        + LOCKED_AMOUNT.micro_algo
        - min_fee_times_3.micro_algo,
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):  # type: ignore
        algorand_client.client.algod.application_box_by_name(
            draft_proposal_client.app_id, METADATA_BOX_KEY.encode()
        )


def test_drop_twice(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient
) -> None:
    proposer_balance_before_drop = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    xgov_registry_mock_client.send.drop_proposal(
        args=DropProposalArgs(proposal_app=draft_proposal_client.app_id),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3),
    )

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.drop_proposal(
            args=DropProposalArgs(proposal_app=draft_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_3
            ),
        )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        proposer.address,
        xgov_registry_mock_client.app_id,
        finalized=True,
    )

    assert_account_balance(
        algorand_client, draft_proposal_client.app_address, PROPOSAL_PARTIAL_FEE
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before_drop
        + LOCKED_AMOUNT.micro_algo
        - min_fee_times_3.micro_algo,
    )


def test_drop_empty_proposal(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient
) -> None:
    proposer_balance_before_drop = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_mock_client.send.drop_proposal(
            args=DropProposalArgs(proposal_app=proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_2
            ),
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client, proposal_client.app_address, PROPOSAL_PARTIAL_FEE
    )

    assert_account_balance(
        algorand_client, proposer.address, proposer_balance_before_drop
    )
