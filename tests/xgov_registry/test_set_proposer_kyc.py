import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk import abi
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    UNLIMITED_KYC_EXPIRATION,
    LogicErrorType,
    proposer_box_name,
)


def test_set_proposer_kyc_success(
    kyc_provider: AddressAndSigner,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=UNLIMITED_KYC_EXPIRATION,
        transaction_parameters=TransactionParameters(
            sender=kyc_provider.address,
            signer=kyc_provider.signer,
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
    assert kyc_expiring == UNLIMITED_KYC_EXPIRATION  # type: ignore


def test_set_proposer_kyc_not_kyc_provider(
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_proposer_kyc(
            proposer=proposer.address,
            kyc_status=True,
            kyc_expiring=UNLIMITED_KYC_EXPIRATION,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_set_proposer_kyc_not_a_proposer(
    kyc_provider: AddressAndSigner,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    with pytest.raises(LogicErrorType, match=err.PROPOSER_DOES_NOT_EXIST):
        xgov_registry_client.set_proposer_kyc(
            proposer=no_role_account.address,
            kyc_status=True,
            kyc_expiring=UNLIMITED_KYC_EXPIRATION,
            transaction_parameters=TransactionParameters(
                sender=kyc_provider.address,
                signer=kyc_provider.signer,
                suggested_params=sp_min_fee_times_2,
                boxes=[(0, proposer_box_name(no_role_account.address))],
            ),
        )
