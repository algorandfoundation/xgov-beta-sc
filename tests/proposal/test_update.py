import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.constants import (
    TITLE_MAX_BYTES,
)
from smart_contracts.proposal.enums import (
    CATEGORY_NULL,
    CATEGORY_SMALL,
    FUNDING_NULL,
    FUNDING_PROACTIVE,
    STATUS_DRAFT,
    STATUS_EMPTY,
)
from tests.proposal.common import LOCKED_AMOUNT, REQUESTED_AMOUNT, logic_error_type

# TODO add tests for update on other statuses


def test_update_success(
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

    proposal_client.update_proposal(
        title="Updated Test Proposal",
        cid=b"\x02" * 59,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert global_state.title.as_str == "Updated Test Proposal"
    assert global_state.cid.as_bytes == b"\x02" * 59
    assert global_state.status == STATUS_DRAFT

    assert global_state.submission_ts > 0
    assert global_state.finalization_ts == 0
    assert global_state.category == CATEGORY_SMALL
    assert global_state.funding_type == FUNDING_PROACTIVE
    assert global_state.requested_amount == REQUESTED_AMOUNT
    assert global_state.locked_amount == LOCKED_AMOUNT
    assert global_state.committee_id.as_bytes == b""
    assert global_state.committee_members == 0
    assert global_state.committee_votes == 0
    assert global_state.voted_members == 0
    assert global_state.approvals == 0
    assert global_state.rejections == 0

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == LOCKED_AMOUNT
    )


def test_update_twice(
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

    proposal_client.update_proposal(
        title="Updated Test Proposal",
        cid=b"\x02" * 59,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    proposal_client.update_proposal(
        title="Updated Test Proposal 2",
        cid=b"\x03" * 59,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert global_state.title.as_str == "Updated Test Proposal 2"
    assert global_state.cid.as_bytes == b"\x03" * 59
    assert global_state.status == STATUS_DRAFT

    assert global_state.submission_ts > 0
    assert global_state.finalization_ts == 0
    assert global_state.category == CATEGORY_SMALL
    assert global_state.funding_type == FUNDING_PROACTIVE
    assert global_state.requested_amount == REQUESTED_AMOUNT
    assert global_state.locked_amount == LOCKED_AMOUNT
    assert global_state.committee_id.as_bytes == b""
    assert global_state.committee_members == 0
    assert global_state.committee_votes == 0
    assert global_state.voted_members == 0
    assert global_state.approvals == 0
    assert global_state.rejections == 0

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == LOCKED_AMOUNT
    )


def test_update_not_proposer(
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

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        proposal_client.update_proposal(
            title="Updated Test Proposal",
            cid=b"\x02" * 59,
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert global_state.title.as_str == "Test Proposal"
    assert global_state.cid.as_bytes == b"\x01" * 59
    assert global_state.status == STATUS_DRAFT

    assert global_state.submission_ts > 0
    assert global_state.finalization_ts == 0
    assert global_state.category == CATEGORY_SMALL
    assert global_state.funding_type == FUNDING_PROACTIVE
    assert global_state.requested_amount == REQUESTED_AMOUNT
    assert global_state.locked_amount == LOCKED_AMOUNT
    assert global_state.committee_id.as_bytes == b""
    assert global_state.committee_members == 0
    assert global_state.committee_votes == 0
    assert global_state.voted_members == 0
    assert global_state.approvals == 0
    assert global_state.rejections == 0

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == LOCKED_AMOUNT
    )


def test_update_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    algorand_client: AlgorandClient,
) -> None:

    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
        proposal_client.update_proposal(
            title="Updated Test Proposal",
            cid=b"\x01" * 59,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert global_state.title.as_str == ""
    assert global_state.cid.as_bytes == b""
    assert global_state.status == STATUS_EMPTY

    assert global_state.submission_ts == 0
    assert global_state.finalization_ts == 0
    assert global_state.category == CATEGORY_NULL
    assert global_state.funding_type == FUNDING_NULL
    assert global_state.requested_amount == 0
    assert global_state.locked_amount == 0
    assert global_state.committee_id.as_bytes == b""
    assert global_state.committee_members == 0
    assert global_state.committee_votes == 0
    assert global_state.voted_members == 0
    assert global_state.approvals == 0
    assert global_state.rejections == 0

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == 0
    )


def test_update_wrong_title_1(
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

    with pytest.raises(logic_error_type, match=err.WRONG_TITLE_LENGTH):
        proposal_client.update_proposal(
            title="",
            cid=b"\x02" * 59,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert global_state.title.as_str == "Test Proposal"
    assert global_state.cid.as_bytes == b"\x01" * 59
    assert global_state.status == STATUS_DRAFT

    assert global_state.submission_ts > 0
    assert global_state.finalization_ts == 0
    assert global_state.category == CATEGORY_SMALL
    assert global_state.funding_type == FUNDING_PROACTIVE
    assert global_state.requested_amount == REQUESTED_AMOUNT
    assert global_state.locked_amount == LOCKED_AMOUNT
    assert global_state.committee_id.as_bytes == b""
    assert global_state.committee_members == 0
    assert global_state.committee_votes == 0
    assert global_state.voted_members == 0
    assert global_state.approvals == 0
    assert global_state.rejections == 0

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == LOCKED_AMOUNT
    )


def test_update_wrong_title_2(
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

    with pytest.raises(logic_error_type, match=err.WRONG_TITLE_LENGTH):
        proposal_client.update_proposal(
            title="a" * (TITLE_MAX_BYTES + 1),
            cid=b"\x02" * 59,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )

    global_state = proposal_client.get_global_state()

    assert global_state.title.as_str == "Test Proposal"
    assert global_state.cid.as_bytes == b"\x01" * 59
    assert global_state.status == STATUS_DRAFT

    assert global_state.submission_ts > 0
    assert global_state.finalization_ts == 0
    assert global_state.category == CATEGORY_SMALL
    assert global_state.funding_type == FUNDING_PROACTIVE
    assert global_state.requested_amount == REQUESTED_AMOUNT
    assert global_state.locked_amount == LOCKED_AMOUNT
    assert global_state.committee_id.as_bytes == b""
    assert global_state.committee_members == 0
    assert global_state.committee_votes == 0
    assert global_state.voted_members == 0
    assert global_state.approvals == 0
    assert global_state.rejections == 0

    assert (
        algorand_client.account.get_information(proposal_client.app_address)["amount"]  # type: ignore
        == LOCKED_AMOUNT
    )
