import pytest

from algokit_utils.models import Account
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
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_voting_account(
        xgov_address=xgov.address,
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
            xgov_address=random_account.address,
            voting_address=xgov.address,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(random_account.address))]
            ),
        )

def test_set_voting_account_not_voting_account_or_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    random_account: AddressAndSigner,
    xgov: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_voting_account(
        xgov_address=xgov.address,
        voting_address=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp,
            boxes=[(0, b"x" + decode_address(xgov.address))]
        ),
    )

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.set_voting_account(
            xgov_address=xgov.address,
            voting_address=random_account.address,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(random_account.address))]
            ),
        )