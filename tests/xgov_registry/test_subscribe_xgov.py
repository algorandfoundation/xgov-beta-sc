import pytest

from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient

from algosdk.encoding import decode_address
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import logic_error_type

def test_subscribe_xgov_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_min_balance
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, b"x" + decode_address(random_account.address))]
        ),
    )

def test_subscribe_xgov_already_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(logic_error_type, match=err.ALREADY_XGOV):
        xgov_registry_client.subscribe_xgov(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=xgov.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.proposer_fee
                    ),
                ),
                signer=xgov.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(xgov.address))]
            ),
        )

def test_subscribe_xgov_wrong_recipient(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(logic_error_type, match=err.WRONG_RECEIVER):
        xgov_registry_client.subscribe_xgov(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=random_account.address,
                        receiver=random_account.address,
                        amount=global_state.proposer_fee
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(random_account.address))]
            ),
        )

def test_subscribe_xgov_wrong_amount(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(logic_error_type, match=err.WRONG_PAYMENT_AMOUNT):
        xgov_registry_client.subscribe_xgov(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=random_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=100
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(random_account.address))]
            ),
        )