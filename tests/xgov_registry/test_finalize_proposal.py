import pytest
from algokit_utils import (
    TransactionParameters,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk.encoding import encode_address
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal import enums as enm
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.common import DEFAULT_COMMITTEE_MEMBERS
from tests.proposal.common import (
    REQUESTED_AMOUNT,
    assert_blocked_proposal_global_state,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_funded_proposal_global_state,
    assert_rejected_proposal_global_state,
)
from tests.xgov_registry.common import LogicErrorType, proposer_box_name


def test_finalize_funded_proposal_success(
    xgov_daemon: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    funded_unassigned_voters_proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        funded_unassigned_voters_proposal_client.get_global_state().proposer.as_bytes
    )

    pending_proposals_before = xgov_registry_client.get_global_state().pending_proposals

    xgov_registry_client.finalize_proposal(
        proposal_id=funded_unassigned_voters_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
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
            suggested_params=sp_min_fee_times_3,
        ),
    )

    proposal_global_state = funded_unassigned_voters_proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        proposal_global_state,
        proposer_address,
        xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        voted_members=DEFAULT_COMMITTEE_MEMBERS,
        approvals=10 * DEFAULT_COMMITTEE_MEMBERS,
    )

    pending_proposals_after = xgov_registry_client.get_global_state().pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_empty_proposal_not_xgov_daemon(
    committee_manager: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        proposal_client.get_global_state().proposer.as_bytes
    )
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.finalize_proposal(
            proposal_id=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=committee_manager.address,
                signer=committee_manager.signer,
                foreign_apps=[proposal_client.app_id],
                accounts=[proposer_address],
                boxes=[
                    (
                        0,
                        proposer_box_name(proposer_address),
                    ),
                    (
                        proposal_client.app_id,
                        METADATA_BOX_KEY.encode(),
                    ),
                ],
                suggested_params=sp_min_fee_times_3,
            ),
        )


def test_finalize_empty_proposal_xgov_daemon(
    xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        proposal_client.get_global_state().proposer.as_bytes
    )

    pending_proposals_before = xgov_registry_client.get_global_state().pending_proposals

    xgov_registry_client.finalize_proposal(
        proposal_id=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
            foreign_apps=[proposal_client.app_id],
            accounts=[proposer_address],
            boxes=[
                (
                    0,
                    proposer_box_name(proposer_address),
                ),
                (
                    proposal_client.app_id,
                    METADATA_BOX_KEY.encode(),
                ),
            ],
            suggested_params=sp_min_fee_times_3,
        ),
    )

    proposal_global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        proposal_global_state,
        proposer_address=proposer_address,
        registry_app_id=xgov_registry_client.app_id,
        finalized=True,
    )

    pending_proposals_after = xgov_registry_client.get_global_state().pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_draft_proposal_not_xgov_daemon(
    committee_manager: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        draft_proposal_client.get_global_state().proposer.as_bytes
    )
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.finalize_proposal(
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
                suggested_params=sp_min_fee_times_3,
            ),
        )


def test_finalize_draft_proposal_xgov_daemon(
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        draft_proposal_client.get_global_state().proposer.as_bytes
    )

    pending_proposals_before = xgov_registry_client.get_global_state().pending_proposals

    xgov_registry_client.finalize_proposal(
        proposal_id=draft_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
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
            suggested_params=sp_min_fee_times_3,
        ),
    )

    proposal_global_state = draft_proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        proposal_global_state,
        proposer_address=proposer_address,
        registry_app_id=xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
    )

    pending_proposals_after = xgov_registry_client.get_global_state().pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_rejected_proposal_not_xgov_daemon(
    xgov_registry_client: XGovRegistryClient,
    rejected_unassigned_voters_proposal_client: ProposalClient,
    no_role_account: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        rejected_unassigned_voters_proposal_client.get_global_state().proposer.as_bytes
    )

    pending_proposals_before = xgov_registry_client.get_global_state().pending_proposals

    xgov_registry_client.finalize_proposal(
        proposal_id=rejected_unassigned_voters_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            foreign_apps=[rejected_unassigned_voters_proposal_client.app_id],
            accounts=[proposer_address],
            boxes=[
                (
                    0,
                    proposer_box_name(proposer_address),
                ),
                (
                    rejected_unassigned_voters_proposal_client.app_id,
                    METADATA_BOX_KEY.encode(),
                ),
            ],
            suggested_params=sp_min_fee_times_3,
        ),
    )

    proposal_global_state = (
        rejected_unassigned_voters_proposal_client.get_global_state()
    )

    assert_rejected_proposal_global_state(
        proposal_global_state,
        proposer_address=proposer_address,
        registry_app_id=xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
    )

    pending_proposals_after = xgov_registry_client.get_global_state().pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_funded_proposal_not_xgov_daemon(
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    funded_unassigned_voters_proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        funded_unassigned_voters_proposal_client.get_global_state().proposer.as_bytes
    )

    pending_proposals_before = xgov_registry_client.get_global_state().pending_proposals

    xgov_registry_client.finalize_proposal(
        proposal_id=funded_unassigned_voters_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
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
            suggested_params=sp_min_fee_times_3,
        ),
    )

    proposal_global_state = funded_unassigned_voters_proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        proposal_global_state,
        proposer_address,
        xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        voted_members=DEFAULT_COMMITTEE_MEMBERS,
        approvals=10 * DEFAULT_COMMITTEE_MEMBERS,
    )

    pending_proposals_after = xgov_registry_client.get_global_state().pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_blocked_proposal_not_xgov_daemon(
    no_role_account: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    blocked_unassigned_voters_proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        blocked_unassigned_voters_proposal_client.get_global_state().proposer.as_bytes
    )

    pending_proposals_before = xgov_registry_client.get_global_state().pending_proposals

    xgov_registry_client.finalize_proposal(
        proposal_id=blocked_unassigned_voters_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            foreign_apps=[blocked_unassigned_voters_proposal_client.app_id],
            accounts=[proposer_address],
            boxes=[
                (
                    0,
                    proposer_box_name(proposer_address),
                ),
                (
                    blocked_unassigned_voters_proposal_client.app_id,
                    METADATA_BOX_KEY.encode(),
                ),
            ],
            suggested_params=sp_min_fee_times_3,
        ),
    )

    proposal_global_state = blocked_unassigned_voters_proposal_client.get_global_state()

    assert_blocked_proposal_global_state(
        proposal_global_state,
        proposer_address,
        xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        voted_members=DEFAULT_COMMITTEE_MEMBERS,
        approvals=10 * DEFAULT_COMMITTEE_MEMBERS,
    )

    pending_proposals_after = xgov_registry_client.get_global_state().pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_finalize_invalid_proposal(
    xgov_daemon: AddressAndSigner,
    alternative_xgov_registry_client: XGovRegistryClient,
    funded_unassigned_voters_proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    proposer_address: str = encode_address(  # type: ignore
        funded_unassigned_voters_proposal_client.get_global_state().proposer.as_bytes
    )
    with pytest.raises(LogicErrorType, match=err.INVALID_PROPOSAL):
        alternative_xgov_registry_client.finalize_proposal(
            proposal_id=funded_unassigned_voters_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
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
                suggested_params=sp_min_fee_times_3,
            ),
        )
