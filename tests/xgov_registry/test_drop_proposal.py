import pytest
from algokit_utils import (
    TransactionParameters,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.encoding import encode_address

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal import enums as enm
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import assert_draft_proposal_global_state
from tests.xgov_registry.common import LogicErrorType, proposer_box_name


def test_drop_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    pending_proposals_before = xgov_registry_client.get_global_state().pending_proposals

    xgov_registry_client.drop_proposal(
        proposal_id=draft_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[draft_proposal_client.app_id],
            accounts=[proposer.address],
            boxes=[
                (
                    0,
                    proposer_box_name(proposer.address),
                ),
                (
                    draft_proposal_client.app_id,
                    METADATA_BOX_KEY.encode(),
                ),
            ],
            suggested_params=sp,
        ),
    )

    proposal_global_state = draft_proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        proposal_global_state,
        proposer.address,
        xgov_registry_client.app_id,
        decommissioned=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=10_000_000,
    )

    pending_proposals_after = xgov_registry_client.get_global_state().pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_drop_proposal_not_proposer(
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
    committee_manager: AddressAndSigner,
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    proposer_address: str = encode_address(  # type: ignore
        draft_proposal_client.get_global_state().proposer.as_bytes
    )

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.drop_proposal(
            proposal_id=draft_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=committee_manager.address,
                signer=committee_manager.signer,
                foreign_apps=[draft_proposal_client.app_id],
                accounts=[proposer_address],
                boxes=[
                    (
                        0,
                        proposer_box_name(proposer_address),
                    ),
                    (
                        draft_proposal_client.app_id,
                        METADATA_BOX_KEY.encode(),
                    ),
                ],
                suggested_params=sp,
            ),
        )


def test_drop_invalid_proposal(
    xgov_registry_client: XGovRegistryClient,
    funded_unassigned_voters_proposal_client: ProposalClient,
    deployer: AddressAndSigner,
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    proposer_address: str = encode_address(  # type: ignore
        funded_unassigned_voters_proposal_client.get_global_state().proposer.as_bytes
    )

    with pytest.raises(LogicErrorType, match=err.INVALID_PROPOSAL):
        xgov_registry_client.drop_proposal(
            proposal_id=xgov_registry_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                foreign_apps=[funded_unassigned_voters_proposal_client.app_id],
                accounts=[proposer_address],
                boxes=[
                    (
                        0,
                        proposer_box_name(proposer_address),
                    ),
                    (
                        funded_unassigned_voters_proposal_client.app_id,
                        METADATA_BOX_KEY.encode(),
                    ),
                ],
                suggested_params=sp,
            ),
        )


def test_drop_paused_registry(
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.drop_proposal(
            proposal_id=draft_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[draft_proposal_client.app_id],
                accounts=[proposer.address],
                boxes=[
                    (
                        0,
                        proposer_box_name(proposer.address),
                    ),
                    (
                        draft_proposal_client.app_id,
                        METADATA_BOX_KEY.encode(),
                    ),
                ],
                suggested_params=sp,
            ),
        )
