import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, request_box_name, xgov_box_name


def test_approve_subscribe_xgov_success(
    algorand_client: AlgorandClient,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
    xgov_subscriber: AddressAndSigner,
    no_role_account: AddressAndSigner,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    request_id = before_global_state.request_id - 1

    xgov_registry_client.approve_subscribe_xgov(
        request_id=request_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_subscriber.address,
            signer=xgov_subscriber.signer,
            suggested_params=sp,
            boxes=[
                (0, request_box_name(request_id)),
                (0, xgov_box_name(app_xgov_subscribe_requested.app_address)),
            ],
            foreign_apps=[app_xgov_subscribe_requested.app_id],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert (before_global_state.xgovs + 1) == after_global_state.xgovs

    xgov_box = xgov_registry_client.get_xgov_box(
        xgov_address=app_xgov_subscribe_requested.app_address,
        transaction_parameters=TransactionParameters(
            boxes=[(0, xgov_box_name(app_xgov_subscribe_requested.app_address))],
        ),
    )

    assert no_role_account.address == xgov_box.return_value.voting_address


def test_approve_subscribe_xgov_not_subscriber(
    algorand_client: AlgorandClient,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
    no_role_account: AddressAndSigner,
) -> None:
    before_global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    request_id = before_global_state.request_id - 1

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.approve_subscribe_xgov(
            request_id=request_id,
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[
                    (0, request_box_name(request_id)),
                    (0, xgov_box_name(app_xgov_subscribe_requested.app_address)),
                ],
                foreign_apps=[app_xgov_subscribe_requested.app_id],
            ),
        )
