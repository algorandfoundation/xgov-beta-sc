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

def test_set_voting_account_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
    xgov: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=xgov.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_min_balance
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

    xgov_registry_client.set_voting_account(
        voting_address=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp,
            boxes=[(0, b"x" + decode_address(xgov.address))]
        ),
    )

def test_set_voting_account_not_an_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
    xgov: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.set_voting_account(
            voting_address=random_account.address,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(xgov.address))]
            ),
        )

def test_set_voting_account_same_address(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=xgov.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_min_balance
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

    with pytest.raises(logic_error_type, match=err.VOTING_ADDRESS_MUST_BE_DIFFERENT):
        xgov_registry_client.set_voting_account(
            voting_address=xgov.address,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(xgov.address))]
            ),
        )