import pytest
from algokit_utils import SigningAccount
from algosdk.constants import ZERO_ADDRESS
from algosdk.error import AlgodHTTPError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetXgovBoxArgs,
    XGovBoxValue,
    XGovRegistryClient,
)


def test_get_xgov_box_exists_success(
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    result = xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(xgov_address=xgov.address)
    )
    get_xgov_box, exists = result.abi_return

    state_xgov_box = xgov_registry_client.state.box.xgov_box.get_value(xgov.address)

    assert exists
    assert (
        XGovBoxValue(
            voting_address=get_xgov_box[0],
            tolerated_absences=get_xgov_box[1],
            last_vote_timestamp=get_xgov_box[2],
            subscription_round=get_xgov_box[3],
        )
        == state_xgov_box
    )


def test_get_xgov_box_not_exists_success(
    xgov_registry_client: XGovRegistryClient,
) -> None:
    result = xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(xgov_address=ZERO_ADDRESS),
    )
    get_xgov_box, exists = result.abi_return

    assert not exists
    assert XGovBoxValue(
        voting_address=get_xgov_box[0],
        tolerated_absences=get_xgov_box[1],
        last_vote_timestamp=get_xgov_box[2],
        subscription_round=get_xgov_box[3],
    ) == XGovBoxValue(
        voting_address=ZERO_ADDRESS,
        tolerated_absences=0,
        last_vote_timestamp=0,
        subscription_round=0,
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.xgov_box.get_value(ZERO_ADDRESS)
