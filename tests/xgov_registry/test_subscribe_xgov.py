import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk import abi
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, xgov_box_name


def test_subscribe_xgov_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.subscribe_xgov(
        voting_address=random_account.address,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=before_global_state.xgov_fee,
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(random_account.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + before_global_state.xgov_fee) == after_info["amount"]  # type: ignore
    assert (before_global_state.xgovs + 1) == after_global_state.xgovs

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=xgov_box_name(random_account.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("address")
    voting_address = box_abi.decode(box_value)  # type: ignore

    assert random_account.address == voting_address  # type: ignore


def test_app_subscribe_xgov_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    xgov_subscriber_app.subscribe_xgov(
        app_id=xgov_registry_client.app_id,
        voting_address=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            foreign_apps=[xgov_registry_client.app_id],
            boxes=[
                (
                    xgov_registry_client.app_id,
                    xgov_box_name(xgov_subscriber_app.app_address),
                )
            ],
        ),
    )


def test_subscribe_xgov_already_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.ALREADY_XGOV):
        xgov_registry_client.subscribe_xgov(
            voting_address=xgov.address,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=xgov.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=xgov.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(xgov.address))],
            ),
        )


def test_subscribe_xgov_wrong_recipient(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.subscribe_xgov(
            voting_address=random_account.address,
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
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )


def test_subscribe_xgov_wrong_amount(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.subscribe_xgov(
            voting_address=random_account.address,
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
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )


def test_subscribe_xgov_paused_non_admin_error(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.pause_non_admin()

    with pytest.raises(LogicErrorType, match=err.PAUSED_NON_ADMIN):
        xgov_registry_client.subscribe_xgov(
            voting_address=random_account.address,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=random_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=before_global_state.xgov_fee,
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )

    xgov_registry_client.resume_non_admin()

    xgov_registry_client.subscribe_xgov(
        voting_address=random_account.address,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=random_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=before_global_state.xgov_fee,
                ),
            ),
            signer=random_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(random_account.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + before_global_state.xgov_fee) == after_info["amount"]  # type: ignore
    assert (before_global_state.xgovs + 1) == after_global_state.xgovs

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=xgov_box_name(random_account.address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("address")
    voting_address = box_abi.decode(box_value)  # type: ignore

    assert random_account.address == voting_address  # type: ignore
