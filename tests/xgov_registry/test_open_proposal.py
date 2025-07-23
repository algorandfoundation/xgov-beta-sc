import pytest
from algokit_utils import SigningAccount, AlgorandClient, PaymentParams, CommonAppCallParams, AlgoAmount, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, OpenProposalArgs,
)
from smart_contracts.errors import std_errors as err

from tests.utils import ERROR_TO_REGEX
from tests.xgov_registry.common import get_open_proposal_fee


def test_open_proposal_success(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient
) -> None:
    initial_pending_proposals = xgov_registry_client.state.global_state.pending_proposals
    xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=get_open_proposal_fee(xgov_registry_client),
                )
            )
        ),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
    )

    final_pending_proposals = xgov_registry_client.state.global_state.pending_proposals
    assert final_pending_proposals == initial_pending_proposals + 1


def test_open_proposal_not_a_proposer(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_open_proposal_fee(xgov_registry_client),
                    )
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address, static_fee=min_fee_times_3)
        )


def test_open_proposal_active_proposal(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    open_proposal_fee = get_open_proposal_fee(xgov_registry_client)
    xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=open_proposal_fee,
                )
            )
        ),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.ALREADY_ACTIVE_PROPOSAL]):
        xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=open_proposal_fee,
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
        )


def test_open_proposal_wrong_fee(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.INSUFFICIENT_FEE]):
        xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_open_proposal_fee(xgov_registry_client),
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address)
        )


def test_open_proposal_wrong_amount(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_PAYMENT_AMOUNT]):
        xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=AlgoAmount(micro_algo=get_open_proposal_fee(xgov_registry_client).micro_algo - 1),
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
        )


def test_open_proposal_wrong_recipient(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_RECEIVER]):
        xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=proposer.address,
                        amount=get_open_proposal_fee(xgov_registry_client),
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
        )


def test_open_proposal_paused_registry_error(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    open_proposal_fee = get_open_proposal_fee(xgov_registry_client)
    xgov_registry_client.send.pause_registry()
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.PAUSED_REGISTRY]):
        xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=open_proposal_fee,
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
        )

    xgov_registry_client.send.resume_registry()
    xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=open_proposal_fee,
                )
            )
        ),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
    )


def test_open_proposal_paused_proposal_error(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    open_proposal_fee = get_open_proposal_fee(xgov_registry_client)
    xgov_registry_client.send.pause_proposals()
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.PAUSED_PROPOSALS]):
        xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=open_proposal_fee,
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
        )

    xgov_registry_client.send.resume_proposals()
    xgov_registry_client.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=open_proposal_fee,
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
    )

def test_open_proposal_no_committee_declared(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError):  #TODO: match=ERROR_TO_REGEX[err.EMPTY_COMMITTEE_ID] on the Registry handles errors
        xgov_registry_client_committee_not_declared.send.open_proposal(
            args=OpenProposalArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client_committee_not_declared.app_address,
                        amount=get_open_proposal_fee(xgov_registry_client_committee_not_declared),
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3)
        )
