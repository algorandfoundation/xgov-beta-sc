import pytest

from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from smart_contracts.artifacts.proposal_mock.client import ProposalMockClient

from algosdk.encoding import decode_address
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.errors import std_errors as err
from smart_contracts.xgov_registry import enums as enm
from tests.xgov_registry.common import logic_error_type

def test_withdraw_funds_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    added_amount = 10_000_000
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=added_amount
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    xgov_registry_client.withdraw_funds(
        amount=added_amount,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert before_global_state.outstanding_funds == after_global_state.outstanding_funds


def test_withdraw_funds_not_manager(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    random_account: AddressAndSigner,
) -> None:
    added_amount = 10_000_000
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=added_amount
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.withdraw_funds(
            amount=added_amount,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
            ),
        )

def test_withdraw_funds_insufficient_funds(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
) -> None:
    added_amount = 10_000_000
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=added_amount
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=err.INSUFFICIENT_FUNDS):
        xgov_registry_client.withdraw_funds(
            amount=11_000_000,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
            ),
        )