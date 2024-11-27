import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.models import Account
from algosdk import error

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from smart_contracts.artifacts.xgov_subscriber_app_mock.client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, xgov_box_name


def test_unsubscribe_xgov_app_success(
    xgov_registry_client: XGovRegistryClient,
    app_xgov: XGovSubscriberAppMockClient,
    deployer: Account,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.unsubscribe_xgov_app(
        app_id=app_xgov.app_id,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            boxes=[(0, xgov_box_name(app_xgov.app_address))],
            foreign_apps=[app_xgov.app_id],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert (before_global_state.xgovs - 1) == after_global_state.xgovs

    with pytest.raises(error.AlgodHTTPError):  # type: ignore
        xgov_registry_client.algod_client.application_box_by_name(
            application_id=xgov_registry_client.app_id,
            box_name=xgov_box_name(app_xgov.app_address),
        )


def test_unsubscribe_xgov_app_with_voting_address_success(
    xgov_registry_client: XGovRegistryClient,
    app_xgov: XGovSubscriberAppMockClient,
    deployer: Account,
    random_account: AddressAndSigner,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = xgov_registry_client.algod_client.suggested_params()

    xgov_registry_client.set_voting_account(
        xgov_address=app_xgov.app_address,
        voting_address=random_account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(app_xgov.app_address))],
        ),
    )

    xgov_registry_client.unsubscribe_xgov_app(
        app_id=app_xgov.app_id,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            boxes=[(0, xgov_box_name(app_xgov.app_address))],
            foreign_apps=[app_xgov.app_id],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert (before_global_state.xgovs - 1) == after_global_state.xgovs

    with pytest.raises(error.AlgodHTTPError):  # type: ignore
        xgov_registry_client.algod_client.application_box_by_name(
            application_id=xgov_registry_client.app_id,
            box_name=xgov_box_name(app_xgov.app_address),
        )


def test_unsubscribe_xgov_app_not_an_xgov(
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    deployer: Account,
) -> None:
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.unsubscribe_xgov_app(
            app_id=xgov_subscriber_app.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                boxes=[(0, xgov_box_name(xgov_subscriber_app.app_address))],
                foreign_apps=[xgov_subscriber_app.app_id],
            ),
        )
