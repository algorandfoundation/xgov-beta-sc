import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.models import Account
from algosdk import error

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, request_box_name, xgov_box_name


def test_reject_subscribe_xgov_success(
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
    algorand_client: AlgorandClient,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    request_id = before_global_state.request_id - 1

    xgov_registry_client.reject_subscribe_xgov(
        request_id=request_id,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[
                (0, request_box_name(request_id)),
                (0, xgov_box_name(app_xgov_subscribe_requested.app_address)),
            ],
            foreign_apps=[app_xgov_subscribe_requested.app_id],
        ),
    )

    with pytest.raises(error.AlgodHTTPError):  # type: ignore
        xgov_registry_client.algod_client.application_box_by_name(
            application_id=xgov_registry_client.app_id,
            box_name=xgov_box_name(app_xgov_subscribe_requested.app_address),
        )


def test_reject_subscribe_xgov_not_subscriber(
    random_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
    algorand_client: AlgorandClient,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    request_id = before_global_state.request_id - 1

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.reject_subscribe_xgov(
            request_id=request_id,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[
                    (0, request_box_name(request_id)),
                    (0, xgov_box_name(app_xgov_subscribe_requested.app_address)),
                ],
                foreign_apps=[app_xgov_subscribe_requested.app_id],
            ),
        )
