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
    SetVotingAccountArgs,
    SubscribeXgovArgs,
    VoteProposalArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import DEFAULT_COMMITTEE_VOTES, DEFAULT_MEMBER_VOTES, CommitteeMember
from tests.proposal.common import submit_proposal
from tests.xgov_registry.common import get_xgov_fee


@pytest.mark.parametrize(
    "account_role",
    ["xgov_address", "voting_address"],
)
@pytest.mark.parametrize(
    "voting_proposal", ["voting_proposal_client", "alternative_voting_proposal_client"]
)
def test_vote_proposal_success(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    account_role: str,
    voting_proposal: str,
    request: pytest.FixtureRequest,
) -> None:
    proposal_client: ProposalClient = request.getfixturevalue(voting_proposal)

    xgov = committee[0].account
    if account_role == "xgov_address":
        sender = xgov.address
    elif account_role == "voting_address":
        voting_address = no_role_account.address
        xgov_registry_client.send.set_voting_account(
            args=SetVotingAccountArgs(
                xgov_address=xgov.address,
                voting_address=voting_address,
            ),
            params=CommonAppCallParams(sender=xgov.address),
        )
        sender = voting_address

    xgov_box = xgov_registry_client.state.box.xgov_box.get_value(
        committee[0].account.address
    )
    absence_tolerance = xgov_registry_client.state.global_state.absence_tolerance
    if voting_proposal == "voting_proposal_client":
        assert xgov_box.voted_proposals == absence_tolerance
    else:
        assert xgov_box.voted_proposals == absence_tolerance - 1
    assert xgov_box.last_vote_timestamp == 0

    xgov_registry_client.send.vote_proposal(
        args=VoteProposalArgs(
            proposal_id=proposal_client.app_id,
            xgov_address=committee[0].account.address,
            approval_votes=committee[0].votes,
            rejection_votes=0,
        ),
        params=CommonAppCallParams(
            sender=sender,
            static_fee=min_fee_times_2,
        ),
    )

    xgov_box = xgov_registry_client.state.box.xgov_box.get_value(
        committee[0].account.address
    )

    assert xgov_box.voted_proposals == absence_tolerance
    assert xgov_box.last_vote_timestamp > 0  # type: ignore

    # Tear down test
    xgov_registry_client.send.set_voting_account(
        args=SetVotingAccountArgs(
            xgov_address=xgov.address,
            voting_address=xgov.address,
        ),
        params=CommonAppCallParams(sender=xgov.address),
    )


def test_vote_proposal_not_in_voting_phase(
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    draft_proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient,
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
    voting_proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient,
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


def test_vote_proposal_not_xgov_or_voting_address(
    no_role_account: SigningAccount,
    xgov: SigningAccount,
    voting_proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.MUST_BE_XGOV_OR_VOTING_ADDRESS):
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
    voting_proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient,
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
        ),
    )
