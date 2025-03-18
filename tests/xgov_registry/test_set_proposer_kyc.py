import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.models import Account
from algosdk import abi

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    KYC_EXPIRATION,
    LogicErrorType,
    proposer_box_name,
)


def test_set_proposer_kyc_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=proposer_box_name(proposer.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(bool,bool,uint64)")
    active_proposal, kyc_status, kyc_expiring = box_abi.decode(box_value)  # type: ignore

    assert kyc_status  # type: ignore
    assert kyc_expiring == KYC_EXPIRATION  # type: ignore


def test_set_proposer_kyc_not_kyc_provider(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_proposer_kyc(
            proposer=proposer.address,
            kyc_status=True,
            kyc_expiring=18446744073709551615,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_set_proposer_kyc_not_a_proposer(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(LogicErrorType, match=err.PROPOSER_DOES_NOT_EXIST):
        xgov_registry_client.set_proposer_kyc(
            proposer=random_account.address,
            kyc_status=True,
            kyc_expiring=18446744073709551615,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(random_account.address))],
            ),
        )


def test_set_proposer_kyc_paused_non_admin_error(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.pause_non_admin()

    with pytest.raises(LogicErrorType, match=err.PAUSED_NON_ADMIN):
        xgov_registry_client.set_proposer_kyc(
            proposer=proposer.address,
            kyc_status=True,
            kyc_expiring=18446744073709551615,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )

    xgov_registry_client.resume_non_admin()

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=proposer_box_name(proposer.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(bool,bool,uint64)")
    active_proposal, kyc_status, kyc_expiring = box_abi.decode(box_value)  # type: ignore

    assert kyc_status  # type: ignore
    assert kyc_expiring == KYC_EXPIRATION  # type: ignore
