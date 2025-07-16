import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.models import Account
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, proposer_box_name


def test_subscribe_proposer_success(
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp: SuggestedParams,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposer_fee,
                ),
            ),
            signer=no_role_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(no_role_account.address))],
        ),
    )

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + global_state.proposer_fee) == after_info["amount"]  # type: ignore

    proposer_box = xgov_registry_client.get_proposer_box(
        proposer_address=no_role_account.address,
        transaction_parameters=TransactionParameters(
            boxes=[(0, proposer_box_name(no_role_account.address))]
        ),
    )

    assert not proposer_box.return_value.active_proposal
    assert not proposer_box.return_value.kyc_status
    assert proposer_box.return_value.kyc_expiring == 0


def test_subscribe_proposer_already_proposer(
    algorand_client: AlgorandClient,
    deployer: Account,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposer_fee,
                ),
            ),
            signer=no_role_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(no_role_account.address))],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.ALREADY_PROPOSER):
        xgov_registry_client.subscribe_proposer(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(no_role_account.address))],
            ),
        )


def test_subscribe_proposer_wrong_recipient(
    algorand_client: AlgorandClient,
    deployer: Account,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.WRONG_RECEIVER):
        xgov_registry_client.subscribe_proposer(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=no_role_account.address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(no_role_account.address))],
            ),
        )


def test_subscribe_proposer_wrong_amount(
    algorand_client: AlgorandClient,
    deployer: Account,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.WRONG_PAYMENT_AMOUNT):
        xgov_registry_client.subscribe_proposer(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=100,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(no_role_account.address))],
            ),
        )


def test_subscribe_proposer_paused_registry_error(
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.subscribe_proposer(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(no_role_account.address))],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposer_fee,
                ),
            ),
            signer=no_role_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(no_role_account.address))],
        ),
    )

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + global_state.proposer_fee) == after_info["amount"]  # type: ignore

    proposer_box = xgov_registry_client.get_proposer_box(
        proposer_address=no_role_account.address,
        transaction_parameters=TransactionParameters(
            boxes=[(0, proposer_box_name(no_role_account.address))]
        ),
    )

    assert not proposer_box.return_value.active_proposal
    assert not proposer_box.return_value.kyc_status
    assert proposer_box.return_value.kyc_expiring == 0
