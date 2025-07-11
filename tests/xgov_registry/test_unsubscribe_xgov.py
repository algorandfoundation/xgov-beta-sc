import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk import error
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, xgov_box_name


def test_unsubscribe_xgov_success(
    xgov: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.unsubscribe_xgov(
        xgov_address=xgov.address,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            boxes=[(0, xgov_box_name(xgov.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert (before_global_state.xgovs - 1) == after_global_state.xgovs

    with pytest.raises(error.AlgodHTTPError):  # type: ignore
        xgov_registry_client.algod_client.application_box_by_name(
            application_id=xgov_registry_client.app_id,
            box_name=xgov_box_name(xgov.address),
        )


def test_app_unsubscribe_xgov_success(
    random_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    xgov_subscriber_app.subscribe_xgov(
        app_id=xgov_registry_client.app_id,
        voting_address=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            suggested_params=sp_min_fee_times_3,
            foreign_apps=[xgov_registry_client.app_id],
            boxes=[
                (
                    xgov_registry_client.app_id,
                    xgov_box_name(xgov_subscriber_app.app_address),
                )
            ],
        ),
    )

    xgov_subscriber_app.unsubscribe_xgov(
        app_id=xgov_registry_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            foreign_apps=[xgov_registry_client.app_id],
            boxes=[
                (
                    xgov_registry_client.app_id,
                    xgov_box_name(xgov_subscriber_app.app_address),
                )
            ],
        ),
    )


def test_unsubscribe_xgov_not_an_xgov(
    random_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.unsubscribe_xgov(
            xgov_address=random_account.address,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                boxes=[(0, xgov_box_name(random_account.address))],
            ),
        )


def test_unsubscribe_xgov_paused_registry_error(
    xgov: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.unsubscribe_xgov(
            xgov_address=xgov.address,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                boxes=[(0, xgov_box_name(xgov.address))],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.unsubscribe_xgov(
        xgov_address=xgov.address,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            boxes=[(0, xgov_box_name(xgov.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert (before_global_state.xgovs - 1) == after_global_state.xgovs

    with pytest.raises(error.AlgodHTTPError):  # type: ignore
        xgov_registry_client.algod_client.application_box_by_name(
            application_id=xgov_registry_client.app_id,
            box_name=xgov_box_name(xgov.address),
        )
