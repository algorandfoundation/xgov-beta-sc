import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, xgov_box_name


def test_subscribe_xgov_success(
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.subscribe_xgov(
        voting_address=no_role_account.address,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=before_global_state.xgov_fee,
                ),
            ),
            signer=no_role_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(no_role_account.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + before_global_state.xgov_fee) == after_info["amount"]  # type: ignore
    assert (before_global_state.xgovs + 1) == after_global_state.xgovs

    xgov_box = xgov_registry_client.get_xgov_box(
        xgov_address=no_role_account.address,
        transaction_parameters=TransactionParameters(
            boxes=[(0, xgov_box_name(no_role_account.address))]
        ),
    )

    assert no_role_account.address == xgov_box.return_value.voting_address


def test_app_subscribe_xgov_success(
    no_role_account: AddressAndSigner,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    xgov_subscriber_app.subscribe_xgov(
        app_id=xgov_registry_client.app_id,
        voting_address=no_role_account.address,
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
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
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
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
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.subscribe_xgov(
            voting_address=no_role_account.address,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=no_role_account.address,
                        amount=global_state.proposer_fee,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(no_role_account.address))],
            ),
        )


def test_subscribe_xgov_wrong_amount(
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(LogicErrorType, match=err.INVALID_PAYMENT):
        xgov_registry_client.subscribe_xgov(
            voting_address=no_role_account.address,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=100,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(no_role_account.address))],
            ),
        )


def test_subscribe_xgov_paused_registry_error(
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    xgov_registry_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.subscribe_xgov(
            voting_address=no_role_account.address,
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=before_global_state.xgov_fee,
                    ),
                ),
                signer=no_role_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(no_role_account.address))],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.subscribe_xgov(
        voting_address=no_role_account.address,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=before_global_state.xgov_fee,
                ),
            ),
            signer=no_role_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(no_role_account.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] + before_global_state.xgov_fee) == after_info["amount"]  # type: ignore
    assert (before_global_state.xgovs + 1) == after_global_state.xgovs

    xgov_box = xgov_registry_client.get_xgov_box(
        xgov_address=no_role_account.address,
        transaction_parameters=TransactionParameters(
            boxes=[(0, xgov_box_name(no_role_account.address))]
        ),
    )

    assert no_role_account.address == xgov_box.return_value.voting_address
