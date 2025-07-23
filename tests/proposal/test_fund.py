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
from tests.common import logic_error_type
from tests.proposal.common import (
    assert_account_balance,
    assert_funded_proposal_global_state,
)
from tests.utils import ERROR_TO_REGEX

# TODO add tests for fund on other statuses


def test_fund_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_draft_proposal(
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=draft_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[draft_proposal_client.app_id],
            ),
        )


def test_fund_final_proposal(
    submitted_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=submitted_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[submitted_proposal_client.app_id],
            ),
        )


def test_fund_voting_proposal(
    voting_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=voting_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[voting_proposal_client.app_id],
            ),
        )


def test_fund_approved_proposal(
    approved_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=approved_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[approved_proposal_client.app_id],
            ),
        )


def test_fund_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=rejected_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[rejected_proposal_client.app_id],
            ),
        )


def test_fund_blocked_proposal(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=blocked_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[blocked_proposal_client.app_id],
            ),
        )


def test_fund_success(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    proposer_balance_before = algorand_client.account.get_information(proposer.address)[  # type: ignore
        "amount"
    ]
    locked_amount = reviewed_proposal_client.get_global_state().locked_amount

    xgov_registry_mock_client.fund(
        proposal_app=reviewed_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[reviewed_proposal_client.app_id],
        ),
    )

    global_state = reviewed_proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before + locked_amount - sp.min_fee,  # type: ignore
    )


def test_fund_twice(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    proposer_balance_before = algorand_client.account.get_information(proposer.address)[  # type: ignore
        "amount"
    ]
    locked_amount = reviewed_proposal_client.get_global_state().locked_amount

    xgov_registry_mock_client.fund(
        proposal_app=reviewed_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[reviewed_proposal_client.app_id],
        ),
    )

    global_state = reviewed_proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before + locked_amount - sp.min_fee,  # type: ignore
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=reviewed_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[reviewed_proposal_client.app_id],
                note="Second funding",
            ),
        )


def test_fund_not_registry(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        reviewed_proposal_client.fund(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[reviewed_proposal_client.app_id],
            )
        )
