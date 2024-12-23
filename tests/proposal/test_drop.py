import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    logic_error_type,
    submit_proposal,
)

# TODO add tests for drop on other statuses


def test_drop_success(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    proposal_client.drop(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client, proposal_client.app_address, PROPOSAL_PARTIAL_FEE
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before_drop + LOCKED_AMOUNT - sp.min_fee,  # type: ignore
    )


def test_drop_twice(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    proposal_client.drop(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.drop(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                note="a",
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client, proposal_client.app_address, PROPOSAL_PARTIAL_FEE
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before_drop + LOCKED_AMOUNT - sp.min_fee,  # type: ignore
    )


def test_drop_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.drop(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                note="a",
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client, proposal_client.app_address, PROPOSAL_PARTIAL_FEE
    )

    assert_account_balance(
        algorand_client, proposer.address, proposer_balance_before_drop  # type: ignore
    )


def test_drop_not_proposer(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    not_proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        proposal_client.drop(
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
                suggested_params=sp,
                note="a",
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )
