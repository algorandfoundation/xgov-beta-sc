import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    LogicErrorType,
    proposer_box_name,
)


def test_open_proposal_success(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp_min_fee_times_3,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()
    assert after_global_state.pending_proposals == (global_state.pending_proposals + 1)


def test_open_proposal_not_a_proposer(
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp_min_fee_times_3,
                boxes=[(0, proposer_box_name(no_role_account.address))],
            ),
        )


def test_open_proposal_active_proposal(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp_min_fee_times_3,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.ALREADY_ACTIVE_PROPOSAL):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp_min_fee_times_3,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_wrong_fee(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FEE):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp_min_fee_times_2,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_wrong_amount(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    with pytest.raises(LogicErrorType, match=err.WRONG_PAYMENT_AMOUNT):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=1_000,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp_min_fee_times_3,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_wrong_recipient(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    with pytest.raises(LogicErrorType, match=err.WRONG_RECEIVER):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=proposer.address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp_min_fee_times_3,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_paused_registry_error(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    xgov_registry_client.pause_registry()
    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp_min_fee_times_3,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp_min_fee_times_3,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert after_global_state.pending_proposals == (global_state.pending_proposals + 1)


def test_open_proposal_paused_proposal_error(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    xgov_registry_client.pause_proposals()
    with pytest.raises(LogicErrorType, match=err.PAUSED_PROPOSALS):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp_min_fee_times_3,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )

    xgov_registry_client.resume_proposals()

    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp_min_fee_times_3,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert after_global_state.pending_proposals == (global_state.pending_proposals + 1)


def test_open_proposal_no_committee_declared(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    global_state = xgov_registry_client_committee_not_declared.get_global_state()
    with pytest.raises(LogicErrorType):
        xgov_registry_client_committee_not_declared.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client_committee_not_declared.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp_min_fee_times_3,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )
