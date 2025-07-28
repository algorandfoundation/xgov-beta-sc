import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    PaymentParams,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import (
    AssignVotersArgs,
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetXgovBoxArgs,
    SubscribeXgovArgs,
    VoteProposalArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_COMMITTEE_VOTES, CommitteeMember, DEFAULT_MEMBER_VOTES
from tests.proposal.common import submit_proposal
from tests.xgov_registry.common import get_xgov_fee


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
    draft_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    min_fee_times_2: AlgoAmount,
) -> None:
    xgov_fee = get_xgov_fee(xgov_registry_client)
    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=proposer,
    )
    for cm in committee[:1]:
        algorand_client.account.ensure_funded_from_environment(
            account_to_fund=cm.account.address,
            min_spending_balance=AlgoAmount(algo=xgov_fee.algo * 2),
            min_funding_increment=xgov_fee,
        )
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=cm.account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=xgov_fee,
                    )
                ),
                voting_address=cm.account.address,
            ),
            params=CommonAppCallParams(sender=cm.account.address),
        )

        draft_proposal_client.send.assign_voters(
            args=AssignVotersArgs(
                voters=[(cm.account.address, DEFAULT_MEMBER_VOTES)],
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address),
        )

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=draft_proposal_client.app_id,
                xgov_address=committee[0].account.address,
                approval_votes=DEFAULT_MEMBER_VOTES,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(
                sender=committee[0].account.address,
                static_fee=min_fee_times_2,
                app_references=[
                    draft_proposal_client.app_id
                ],  # FIXME: This should have been autopopulated
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
