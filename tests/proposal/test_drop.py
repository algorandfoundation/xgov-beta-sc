import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.enums import (
    FUNDING_PROACTIVE,
    STATUS_DRAFT,
    STATUS_EMPTY,
)
from tests.proposal.common import LOCKED_AMOUNT, REQUESTED_AMOUNT, logic_error_type

# TODO add tests for drop on other statuses


def test_drop_success(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
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
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    proposal_client.drop_proposal(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert global_state.status == STATUS_EMPTY

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == 0
    )

    assert (
        algorand_client.account.get_information(proposer.address)["amount"]  # type: ignore
        == proposer_balance_before_drop + LOCKED_AMOUNT - sp.min_fee  # type: ignore
    )


def test_drop_twice(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
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
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    proposal_client.drop_proposal(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.drop_proposal(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                note="a",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert global_state.status == STATUS_EMPTY

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == 0
    )

    assert (
        algorand_client.account.get_information(proposer.address)["amount"]  # type: ignore
        == proposer_balance_before_drop + LOCKED_AMOUNT - sp.min_fee  # type: ignore
    )


def test_drop_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposer_balance_before_drop = algorand_client.account.get_information(  # type: ignore
        proposer.address
    )[
        "amount"
    ]

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.drop_proposal(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                note="a",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert global_state.status == STATUS_EMPTY

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == 0
    )

    assert (
        algorand_client.account.get_information(proposer.address)["amount"]  # type: ignore
        == proposer_balance_before_drop  # type: ignore
    )


def test_drop_not_proposer(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    not_proposer: AddressAndSigner,
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
        ),
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        proposal_client.drop_proposal(
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
                suggested_params=sp,
                note="a",
            ),
        )

    global_state = proposal_client.get_global_state()

    assert global_state.status == STATUS_DRAFT

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == LOCKED_AMOUNT
    )
