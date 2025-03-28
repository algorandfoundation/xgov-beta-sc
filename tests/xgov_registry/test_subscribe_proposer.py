import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.models import Account
from algosdk import abi
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, proposer_box_name


def test_subscribe_proposer_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposer_fee,
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(random_account.address))],
        ),
    )

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + global_state.proposer_fee) == after_info["amount"]  # type: ignore

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=proposer_box_name(random_account.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(bool,bool,uint64)")
    active_proposal, kyc_status, kyc_expiring = box_abi.decode(box_value)  # type: ignore

    assert not active_proposal  # type: ignore
    assert not kyc_status  # type: ignore
    assert kyc_expiring == 0  # type: ignore


def test_subscribe_proposer_already_proposer(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposer_fee,
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(random_account.address))],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.ALREADY_PROPOSER):
        xgov_registry_client.subscribe_proposer(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=random_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(random_account.address))],
            ),
        )


def test_subscribe_proposer_wrong_recipient(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.WRONG_RECEIVER):
        xgov_registry_client.subscribe_proposer(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=random_account.address,
                        receiver=random_account.address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(random_account.address))],
            ),
        )


def test_subscribe_proposer_wrong_amount(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.WRONG_PAYMENT_AMOUNT):
        xgov_registry_client.subscribe_proposer(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=random_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=100,
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(random_account.address))],
            ),
        )


def test_subscribe_proposer_paused_registry_error(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
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
                        sender=random_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(random_account.address))],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposer_fee,
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(random_account.address))],
        ),
    )

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + global_state.proposer_fee) == after_info["amount"]  # type: ignore

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=proposer_box_name(random_account.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(bool,bool,uint64)")
    active_proposal, kyc_status, kyc_expiring = box_abi.decode(box_value)  # type: ignore

    assert not active_proposal  # type: ignore
    assert not kyc_status  # type: ignore
    assert kyc_expiring == 0  # type: ignore
