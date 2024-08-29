import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.client import XgovRegistryMockClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.enums import (
    CATEGORY_SMALL,
    FUNDING_PROACTIVE,
    STATUS_DRAFT,
    STATUS_FINAL,
)
from tests.proposal.common import (
    LOCKED_AMOUNT,
    REQUESTED_AMOUNT,
    assert_account_balance,
    assert_proposal_global_state,
    logic_error_type,
    relative_to_absolute_amount,
)

# TODO add tests for drop on other statuses


def test_finalize_success(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: str,
) -> None:
    proposal_client.submit_proposal(
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

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    publishing_fee = relative_to_absolute_amount(
        reg_gs.proposal_fee, reg_gs.publishing_fee_bps
    )
    committee_publisher_balance_before_finalize = algorand_client.account.get_information(  # type: ignore
        committee_publisher
    )[
        "amount"
    ]

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher],
            suggested_params=sp,
        ),
    )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    assert_account_balance(
        algorand_client=algorand_client,
        address=committee_publisher,
        expected_balance=committee_publisher_balance_before_finalize + publishing_fee,  # type: ignore
    )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_FINAL,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
    )


def test_finalize_not_proposer(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    not_proposer: AddressAndSigner,
    committee_publisher: str,
) -> None:
    proposal_client.submit_proposal(
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

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        proposal_client.finalize_proposal(
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[committee_publisher],
            ),
        )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_DRAFT,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
    )

    assert_account_balance(algorand_client, proposal_client.app_address, LOCKED_AMOUNT)


def test_finalize_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: str,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.finalize_proposal(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[committee_publisher],
            ),
        )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )


def test_finalize_twice(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: str,
) -> None:
    proposal_client.submit_proposal(
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

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=0
    )  # so we could actually finalize
    proposal_client.finalize_proposal(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
            accounts=[committee_publisher],
        ),
    )

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.finalize_proposal(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[committee_publisher],
                note="Second finalize",
            ),
        )
    xgov_registry_mock_client.set_discussion_duration_small(
        discussion_duration=discussion_duration
    )  # restore

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_FINAL,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
    )


def test_finalize_too_early(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: str,
) -> None:
    proposal_client.submit_proposal(
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

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.TOO_EARLY):
        proposal_client.finalize_proposal(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                suggested_params=sp,
                accounts=[committee_publisher],
            ),
        )

    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        status=STATUS_DRAFT,
        title="Test Proposal",
        cid=b"\x01" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        locked_amount=LOCKED_AMOUNT,
        category=CATEGORY_SMALL,
    )

    assert_account_balance(algorand_client, proposal_client.app_address, LOCKED_AMOUNT)
