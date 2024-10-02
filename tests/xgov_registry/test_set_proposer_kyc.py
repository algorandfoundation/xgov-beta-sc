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

def test_set_proposer_kyc_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_kyc_provider(
        provider=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            boxes=[(0, b"p" + decode_address(proposer.address))]
        ),
    )

def test_set_proposer_kyc_not_kyc_provider(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_kyc_provider(
        provider=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    sp.min_fee *= 3  # type: ignore

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.set_proposer_kyc(
            proposer=proposer.address,
            kyc_status=True,
            kyc_expiring=18446744073709551615,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                boxes=[(0, b"p" + decode_address(proposer.address))]
            ),
        )

def test_set_proposer_kyc_not_a_proposer(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(logic_error_type, match=err.PROPOSER_DOES_NOT_EXIST):
        xgov_registry_client.set_proposer_kyc(
            proposer=random_account.address,
            kyc_status=True,
            kyc_expiring=18446744073709551615,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(random_account.address))]
            ),
        )