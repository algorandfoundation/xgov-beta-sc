import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk import abi

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

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=xgov_box_name(app_xgov_subscribe_requested.app_address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(address,uint64,uint64)")
    voting_address, _, _ = box_abi.decode(box_value)  # type: ignore

    assert no_role_account.address == voting_address  # type: ignore


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
