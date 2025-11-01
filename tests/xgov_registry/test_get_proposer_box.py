import pytest
from algokit_utils import SigningAccount
from algosdk.constants import ZERO_ADDRESS
from algosdk.error import AlgodHTTPError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetProposerBoxArgs,
    ProposerBoxValue,
    XGovRegistryClient,
)


def test_get_proposer_box_exists_success(
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    result = xgov_registry_client.send.get_proposer_box(
        args=GetProposerBoxArgs(proposer_address=proposer.address)
    )
    get_proposer_box, exists = result.abi_return

    state_proposer_box = xgov_registry_client.state.box.proposer_box.get_value(
        proposer.address
    )

    assert exists
    assert (
        ProposerBoxValue(
            active_proposal=get_proposer_box[0],
            kyc_status=get_proposer_box[1],
            kyc_expiring=get_proposer_box[2],
        )
        == state_proposer_box
    )


def test_get_proposer_box_not_exists_success(
    xgov_registry_client: XGovRegistryClient,
) -> None:
    result = xgov_registry_client.send.get_proposer_box(
        args=GetProposerBoxArgs(proposer_address=ZERO_ADDRESS),
    )
    get_proposer_box, exists = result.abi_return

    assert not exists
    assert ProposerBoxValue(
        active_proposal=get_proposer_box[0],
        kyc_status=get_proposer_box[1],
        kyc_expiring=get_proposer_box[2],
    ) == ProposerBoxValue(
        active_proposal=False,
        kyc_status=False,
        kyc_expiring=0,
    )

    with pytest.raises(AlgodHTTPError, match="box not found"):
        xgov_registry_client.state.box.proposer_box.get_value(ZERO_ADDRESS)
