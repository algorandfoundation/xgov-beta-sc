import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.client import XgovRegistryMockClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.constants import (
    TITLE_MAX_BYTES,
)
from smart_contracts.proposal.enums import (
    CATEGORY_SMALL,
    FUNDING_PROACTIVE,
    STATUS_DRAFT,
)
from tests.proposal.common import (
    LOCKED_AMOUNT,
    REQUESTED_AMOUNT,
    assert_account_balance,
    assert_proposal_global_state,
    logic_error_type,
)

# TODO add tests for update on other statuses


def test_update_success(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    proposal_client.update(
        title="Updated Test Proposal",
        cid=b"\x02" * 59,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        title="Updated Test Proposal",
        cid=b"\x02" * 59,
        status=STATUS_DRAFT,
        category=CATEGORY_SMALL,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT,
    )


def test_update_twice(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    proposal_client.update(
        title="Updated Test Proposal",
        cid=b"\x02" * 59,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    proposal_client.update(
        title="Updated Test Proposal 2",
        cid=b"\x03" * 59,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        title="Updated Test Proposal 2",
        cid=b"\x03" * 59,
        status=STATUS_DRAFT,
        category=CATEGORY_SMALL,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT,
    )


def test_update_not_proposer(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    not_proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        proposal_client.update(
            title="Updated Test Proposal",
            cid=b"\x02" * 59,
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        title="Test Proposal",
        cid=b"\x01" * 59,
        status=STATUS_DRAFT,
        category=CATEGORY_SMALL,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT,
    )


def test_update_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.update(
            title="Updated Test Proposal",
            cid=b"\x01" * 59,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        0,
    )


def test_update_wrong_title_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(logic_error_type, match=err.WRONG_TITLE_LENGTH):
        proposal_client.update(
            title="",
            cid=b"\x02" * 59,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        title="Test Proposal",
        cid=b"\x01" * 59,
        status=STATUS_DRAFT,
        category=CATEGORY_SMALL,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT,
    )


def test_update_wrong_title_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=LOCKED_AMOUNT,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(logic_error_type, match=err.WRONG_TITLE_LENGTH):
        proposal_client.update(
            title="a" * (TITLE_MAX_BYTES + 1),
            cid=b"\x02" * 59,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        title="Test Proposal",
        cid=b"\x01" * 59,
        status=STATUS_DRAFT,
        category=CATEGORY_SMALL,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT,
    )
