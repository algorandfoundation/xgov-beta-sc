import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.models import Account
from algosdk import abi
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, xgov_box_name


def test_set_voting_account_success(
    random_account: AddressAndSigner,
    xgov: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    xgov_registry_client.set_voting_account(
        xgov_address=xgov.address,
        voting_address=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(xgov.address))],
        ),
    )

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=xgov_box_name(xgov.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(address,uint64,uint64)")
    voting_address, _, _ = box_abi.decode(box_value)  # type: ignore

    assert random_account.address == voting_address  # type: ignore


def test_set_voting_account_not_an_xgov(
    random_account: AddressAndSigner,
    xgov: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_voting_account(
            xgov_address=random_account.address,
            voting_address=xgov.address,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp_min_fee_times_2,
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )


def test_set_voting_account_not_voting_account_or_xgov(
    deployer: Account,
    random_account: AddressAndSigner,
    xgov: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.set_voting_account(
        xgov_address=xgov.address,
        voting_address=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp_min_fee_times_2,
            boxes=[(0, xgov_box_name(xgov.address))],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.set_voting_account(
            xgov_address=xgov.address,
            voting_address=random_account.address,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp_min_fee_times_2,
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )


def test_set_voting_account_paused_registry_error(
    random_account: AddressAndSigner,
    xgov: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    xgov_registry_client.pause_registry()
    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.set_voting_account(
            xgov_address=xgov.address,
            voting_address=random_account.address,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp_min_fee_times_2,
                boxes=[(0, xgov_box_name(xgov.address))],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.set_voting_account(
        xgov_address=xgov.address,
        voting_address=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp_min_fee_times_2,
            boxes=[(0, xgov_box_name(xgov.address))],
        ),
    )

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=xgov_box_name(xgov.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(address,uint64,uint64)")
    voting_address, _, _ = box_abi.decode(box_value)  # type: ignore

    assert random_account.address == voting_address  # type: ignore
