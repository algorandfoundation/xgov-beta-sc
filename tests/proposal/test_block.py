import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.proposal.common import (
    assert_account_balance,
    assert_blocked_proposal_global_state,
    logic_error_type,
)
from tests.utils import ERROR_TO_REGEX

# TODO add tests for block on other statuses


def test_block_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_block_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        draft_proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_block_final_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        submitted_proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_block_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        voting_proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_block_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        rejected_proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_block_reviewed_proposal(
    reviewed_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        reviewed_proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_block_success(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:

    xgov_treasury_balance_before = algorand_client.account.get_information(  # type: ignore
        xgov_registry_mock_client.app_address
    )[
        "amount"
    ]

    locked_amount = blocked_proposal_client.get_global_state().locked_amount

    global_state = blocked_proposal_client.get_global_state()

    assert_blocked_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(
        algorand_client,
        xgov_registry_mock_client.app_address,
        xgov_treasury_balance_before + locked_amount,  # type: ignore
    )


def test_block_twice(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    xgov_treasury_balance_before = algorand_client.account.get_information(  # type: ignore
        xgov_registry_mock_client.app_address
    )[
        "amount"
    ]

    locked_amount = blocked_proposal_client.get_global_state().locked_amount

    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        blocked_proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                note="Second block",
            ),
        )

    global_state = blocked_proposal_client.get_global_state()

    assert_blocked_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(
        algorand_client,
        xgov_registry_mock_client.app_address,
        xgov_treasury_balance_before + locked_amount,  # type: ignore
    )


def test_block_not_council(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    no_role_account: AddressAndSigner,
) -> None:

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        approved_proposal_client.review(
            block=True,
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )
