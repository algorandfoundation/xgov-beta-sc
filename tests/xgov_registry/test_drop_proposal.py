import pytest
from algokit_utils import AlgoAmount, CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    DropProposalArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal import enums as enm
from tests.proposal.common import REQUESTED_AMOUNT, assert_draft_proposal_global_state


def test_drop_proposal_success(
    min_fee_times_3: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
    proposer: SigningAccount,
    draft_proposal_client: ProposalClient,
) -> None:

    pending_proposals_before = xgov_registry_client.state.global_state.pending_proposals

    xgov_registry_client.send.drop_proposal(
        args=DropProposalArgs(proposal_id=draft_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=proposer.address,
            static_fee=min_fee_times_3,
            app_references=[
                draft_proposal_client.app_id
            ],  # FIXME: This should be autopopulated but is not
        ),
    )

    assert_draft_proposal_global_state(
        draft_proposal_client,
        proposer.address,
        xgov_registry_client.app_id,
        finalized=True,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
    )

    pending_proposals_after = xgov_registry_client.state.global_state.pending_proposals
    assert pending_proposals_after == pending_proposals_before - 1


def test_drop_proposal_not_proposer(
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.drop_proposal(
            args=DropProposalArgs(proposal_id=draft_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=no_role_account.address, static_fee=min_fee_times_3
            ),
        )


def test_drop_invalid_proposal(
    min_fee_times_3: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
    proposer: SigningAccount,
    draft_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PROPOSAL):
        xgov_registry_client.send.drop_proposal(
            args=DropProposalArgs(proposal_id=xgov_registry_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_3
            ),
        )


def test_drop_paused_registry(
    min_fee_times_3: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
    proposer: SigningAccount,
    draft_proposal_client: ProposalClient,
) -> None:
    xgov_registry_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.drop_proposal(
            args=DropProposalArgs(proposal_id=draft_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_3
            ),
        )
