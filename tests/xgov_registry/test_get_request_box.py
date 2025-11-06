import pytest
from algosdk.constants import ZERO_ADDRESS
from algosdk.error import AlgodHTTPError
from artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetRequestBoxArgs,
    XGovRegistryClient,
    XGovSubscribeRequestBoxValue,
)


def test_get_request_box_exists_success(
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    request_id = xgov_registry_client.state.global_state.request_id - 1
    result = xgov_registry_client.send.get_request_box(
        args=GetRequestBoxArgs(request_id=request_id),
    )
    get_request_box, exists = result.abi_return

    state_request_box = xgov_registry_client.state.box.request_box.get_value(request_id)

    assert exists
    assert (
        XGovSubscribeRequestBoxValue(
            xgov_addr=get_request_box[0],
            owner_addr=get_request_box[1],
            relation_type=get_request_box[2],
        )
        == state_request_box
    )


def test_get_request_box_not_exists_success(
    xgov_registry_client: XGovRegistryClient,
) -> None:
    request_id = xgov_registry_client.state.global_state.request_id + 1
    result = xgov_registry_client.send.get_request_box(
        args=GetRequestBoxArgs(request_id=request_id),
    )
    get_request_box, exists = result.abi_return

    assert not exists
    assert XGovSubscribeRequestBoxValue(
        xgov_addr=get_request_box[0],
        owner_addr=get_request_box[1],
        relation_type=get_request_box[2],
    ) == XGovSubscribeRequestBoxValue(
        xgov_addr=ZERO_ADDRESS,
        owner_addr=ZERO_ADDRESS,
        relation_type=0,
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.request_box.get_value(request_id)
