import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.error import AlgodHTTPError

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_decommissioned_proposal_global_state,
    assert_empty_proposal_global_state,
    logic_error_type,
    submit_proposal,
)
from tests.utils import ERROR_TO_REGEX

# TODO add tests for drop on other statuses

NO_COMMITTEE = {
    "committee_id": b"",
    "committee_members": 0,
    "committee_votes": 0,
    "assigned_votes": 0,
    "voters_count": 0,
}


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
    sp.min_fee *= 3  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    xgov_registry_mock_client.drop_proposal(
        proposal_app=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(proposal_client.app_id, METADATA_BOX_KEY)],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_decommissioned_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client, proposal_client.app_address, PROPOSAL_PARTIAL_FEE
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before_drop + LOCKED_AMOUNT - sp.min_fee,  # type: ignore
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):  # type: ignore
        algorand_client.client.algod.application_box_by_name(
            proposal_client.app_id, METADATA_BOX_KEY.encode()
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
    sp.min_fee *= 3  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    xgov_registry_mock_client.drop_proposal(
        proposal_app=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(proposal_client.app_id, METADATA_BOX_KEY)],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.drop_proposal(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(proposal_client.app_id, METADATA_BOX_KEY)],
                note="a",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_decommissioned_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
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

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.drop_proposal(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(proposal_client.app_id, METADATA_BOX_KEY)],
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
