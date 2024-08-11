from typing import Type

import pytest
from algokit_utils import LogicError, TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.constants import (
    BPS,
    MAX_REQUESTED_AMOUNT_LARGE,  # TODO placeholder, the actual value will be set by the registry SC
    MAX_REQUESTED_AMOUNT_MEDIUM,  # TODO placeholder, the actual value will be set by the registry SC
    MAX_REQUESTED_AMOUNT_SMALL,  # TODO placeholder, the actual value will be set by the registry SC
    MIN_REQUESTED_AMOUNT,  # TODO placeholder, the actual value will be set by the registry SC
    PROPOSAL_COMMITMENT_BPS,  # TODO placeholder, the actual value will be set by the registry SC
    TITLE_MAX_BYTES,
)
from smart_contracts.proposal.enums import (
    CATEGORY_LARGE,
    CATEGORY_MEDIUM,
    CATEGORY_SMALL,
    FUNDING_NULL,
    FUNDING_PROACTIVE,
    STATUS_DRAFT,
)


def get_locked_amount(requested_amount: int) -> int:
    return PROPOSAL_COMMITMENT_BPS * requested_amount // BPS


REQUESTED_AMOUNT = MIN_REQUESTED_AMOUNT
LOCKED_AMOUNT = get_locked_amount(REQUESTED_AMOUNT)

logic_error_type: Type[LogicError] = LogicError


def test_submit_success(
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
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert global_state.title.as_str == "Test Proposal"
    assert global_state.cid.as_bytes == b"\x00" * 59
    assert global_state.submission_ts > 0
    assert global_state.finalization_ts == 0
    assert global_state.status == STATUS_DRAFT
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


def test_submit_not_proposer(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    not_proposer: AddressAndSigner,
) -> None:
    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        proposal_client.submit_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=not_proposer.address,
                        receiver=proposal_client.app_address,
                        amount=LOCKED_AMOUNT,
                    )
                ),
                signer=not_proposer.signer,
            ),
            title="Test Proposal",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
            ),
        )


def test_submit_twice(
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
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )
    with pytest.raises(logic_error_type, match=err.WRONG_PROPOSAL_STATUS):
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
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_title_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    with pytest.raises(logic_error_type, match=err.WRONG_TITLE_LENGTH):
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
            title="",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_title_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    with pytest.raises(logic_error_type, match=err.WRONG_TITLE_LENGTH):
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
            title="a" * (TITLE_MAX_BYTES + 1),
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_funding_type_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    with pytest.raises(logic_error_type, match=err.WRONG_FUNDING_TYPE):
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
            cid=b"\x00" * 59,
            funding_type=FUNDING_NULL,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_funding_type_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    with pytest.raises(logic_error_type, match=err.WRONG_FUNDING_TYPE):
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
            cid=b"\x00" * 59,
            funding_type=FUNDING_NULL + 1,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_requested_amount_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = REQUESTED_AMOUNT - 1
    locked_amount = get_locked_amount(requested_amount)
    with pytest.raises(logic_error_type, match=err.WRONG_MIN_REQUESTED_AMOUNT):
        proposal_client.submit_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=proposal_client.app_address,
                        amount=locked_amount,
                    )
                ),
                signer=proposer.signer,
            ),
            title="Test Proposal",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=requested_amount,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_requested_amount_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_LARGE + 1
    locked_amount = get_locked_amount(requested_amount)
    with pytest.raises(logic_error_type, match=err.WRONG_MAX_REQUESTED_AMOUNT):
        proposal_client.submit_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=proposal_client.app_address,
                        amount=locked_amount,
                    )
                ),
                signer=proposer.signer,
            ),
            title="Test Proposal",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=requested_amount,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_payment_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    locked_amount = LOCKED_AMOUNT - 1
    with pytest.raises(logic_error_type, match=err.WRONG_LOCKED_AMOUNT):
        proposal_client.submit_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=proposal_client.app_address,
                        amount=locked_amount,
                    )
                ),
                signer=proposer.signer,
            ),
            title="Test Proposal",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_payment_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    locked_amount = LOCKED_AMOUNT + 1
    with pytest.raises(logic_error_type, match=err.WRONG_LOCKED_AMOUNT):
        proposal_client.submit_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=proposal_client.app_address,
                        amount=locked_amount,
                    )
                ),
                signer=proposer.signer,
            ),
            title="Test Proposal",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_payment_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    not_proposer: AddressAndSigner,
) -> None:
    with pytest.raises(logic_error_type, match=err.WRONG_SENDER):
        proposal_client.submit_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=not_proposer.address,
                        receiver=proposal_client.app_address,
                        amount=LOCKED_AMOUNT,
                    )
                ),
                signer=not_proposer.signer,
            ),
            title="Test Proposal",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_wrong_payment_4(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    with pytest.raises(logic_error_type, match=err.WRONG_RECEIVER):
        proposal_client.submit_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=proposer.address,
                        amount=LOCKED_AMOUNT,
                    )
                ),
                signer=proposer.signer,
            ),
            title="Test Proposal",
            cid=b"\x00" * 59,
            funding_type=FUNDING_PROACTIVE,
            requested_amount=REQUESTED_AMOUNT,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
            ),
        )


def test_submit_category_small_1(
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
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_SMALL


def test_submit_category_small_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MIN_REQUESTED_AMOUNT + 1
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_SMALL


def test_submit_category_small_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_SMALL - 1
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_SMALL


def test_submit_category_small_4(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_SMALL
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_SMALL


def test_submit_category_medium_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_SMALL + 1
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_MEDIUM


def test_submit_category_medium_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_MEDIUM - 1
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_MEDIUM


def test_submit_category_medium_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_MEDIUM
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_MEDIUM


def test_submit_category_large_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_MEDIUM + 1
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_LARGE


def test_submit_category_large_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_LARGE - 1
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_LARGE


def test_submit_category_large_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_LARGE
    locked_amount = get_locked_amount(requested_amount)
    proposal_client.submit_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            signer=proposer.signer,
        ),
        title="Test Proposal",
        cid=b"\x00" * 59,
        funding_type=FUNDING_PROACTIVE,
        requested_amount=requested_amount,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
        ),
    )

    global_state = proposal_client.get_global_state()
    assert global_state.category == CATEGORY_LARGE
