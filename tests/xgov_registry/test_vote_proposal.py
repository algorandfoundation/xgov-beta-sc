import pytest
from algokit_utils import AlgoAmount, CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetXgovBoxArgs,
    VoteProposalArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_COMMITTEE_VOTES, CommitteeMember


def test_vote_proposal_success(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> None:
    xgov_registry_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=committee[0].votes,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(
            sender=committee[0].account.address,
            static_fee=min_fee_times_2,
            app_references=[
                voting_proposal_client.app_id
            ],  # FIXME: This should have been autopopulated
        ),
    )

    xgov_box = xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(xgov_address=committee[0].account.address)
    ).abi_return

    assert xgov_box.voted_proposals == 1  # type: ignore
    assert xgov_box.last_vote_timestamp > 0  # type: ignore


def test_vote_proposal_not_in_voting_phase(
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.PROPOSAL_IS_NOT_VOTING):
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
        )


def test_vote_proposal_not_a_proposal_app(
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PROPOSAL):
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=xgov_registry_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
        )


def test_vote_proposal_not_an_xgov(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=no_role_account.address,
                approval_votes=DEFAULT_COMMITTEE_VOTES,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_vote_proposal_wrong_voting_address(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov: SigningAccount,
    voting_proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=err.MUST_BE_VOTING_ADDRESS):
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=xgov.address,
                approval_votes=0,
                rejection_votes=DEFAULT_COMMITTEE_VOTES,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_vote_proposal_paused_registry_error(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> None:
    xgov_registry_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=committee[0].votes,
                rejection_votes=0,
            ),
        )

    xgov_registry_client.send.resume_registry()
    xgov_registry_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=committee[0].votes,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(
            sender=committee[0].account.address,
            static_fee=min_fee_times_2,
            app_references=[
                voting_proposal_client.app_id
            ],  # FIXME: This should have been autopopulated
        ),
    )
