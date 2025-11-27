import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    SigningAccount,
)
from algokit_utils.config import config

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
    ReviewArgs,
)
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    CreateEmptyProposalArgs,
    DeclareCommitteeArgs,
    PayGrantProposalArgs,
    SetXgovCouncilArgs,
    SetXgovDaemonArgs,
    VoteProposalArgs,
    XgovRegistryMockClient,
    XgovRegistryMockFactory,
)
from smart_contracts.xgov_registry.config import MAX_REQUESTED_AMOUNT_LARGE
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    INITIAL_FUNDS,
    CommitteeMember,
)
from tests.proposal.common import (
    assign_voters,
    open_proposal,
    quorums_reached,
    scrutinize_proposal,
    submit_proposal,
    unassign_voters,
)


@pytest.fixture(scope="session")
def proposer(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_LARGE),
    )
    return account


@pytest.fixture(scope="session")
def xgov_registry_mock_client(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_council: SigningAccount,
) -> XgovRegistryMockClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XgovRegistryMockFactory,
        default_sender=deployer.address,
    )
    client, _ = factory.send.create.create()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=AlgoAmount(micro_algo=int(INITIAL_FUNDS.micro_algo) * 100),
    )

    client.send.set_xgov_daemon(args=SetXgovDaemonArgs(xgov_daemon=xgov_daemon.address))
    client.send.set_xgov_council(args=SetXgovCouncilArgs(council=xgov_council.address))
    client.send.declare_committee(
        args=DeclareCommitteeArgs(
            committee_id=DEFAULT_COMMITTEE_ID,
            size=DEFAULT_COMMITTEE_MEMBERS,
            votes=DEFAULT_COMMITTEE_VOTES,
        )
    )

    return client


@pytest.fixture(scope="function")
def proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )

    proposal_app_id = xgov_registry_mock_client.send.create_empty_proposal(
        args=CreateEmptyProposalArgs(proposer=proposer.address),
        params=CommonAppCallParams(static_fee=min_fee_times_3),
    )

    client = ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id.abi_return,  # type: ignore
    )

    return client


@pytest.fixture(scope="function")
def draft_proposal_client(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> ProposalClient:
    open_proposal(proposal_client, algorand_client, proposer)
    return proposal_client


@pytest.fixture(scope="function")
def submitted_proposal_client(
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> ProposalClient:
    submit_proposal(
        draft_proposal_client,
        xgov_registry_mock_client,
        proposer,
    )
    return draft_proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client(
    committee: list[CommitteeMember],
    xgov_daemon: SigningAccount,
    submitted_proposal_client: ProposalClient,
) -> ProposalClient:
    composer = submitted_proposal_client.new_group()

    assign_voters(
        composer,
        committee,
        xgov_daemon,
    )
    composer.send()
    return submitted_proposal_client


@pytest.fixture(scope="function")
def rejected_proposal_client(
    no_role_account: SigningAccount,
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
) -> ProposalClient:
    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)
    return voting_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client(
    no_role_account: SigningAccount,
    committee: list[CommitteeMember],
    min_fee_times_2: AlgoAmount,
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    voted_members, total_votes, member_idx = 0, 0, 0
    while not quorums_reached(voting_proposal_client, voted_members, total_votes):
        xgov_registry_mock_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee[member_idx].account.address,
                approvals=committee[member_idx].votes,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2),
        )
        voted_members += 1
        total_votes += committee[member_idx].votes
        member_idx += 1

    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)
    return voting_proposal_client


@pytest.fixture(scope="function")
def cleaned_approved_proposal_client(
    no_role_account: SigningAccount,
    committee: list[CommitteeMember],
    approved_proposal_client: ProposalClient,
) -> ProposalClient:
    composer = approved_proposal_client.new_group()
    unassign_voters(
        composer,
        committee,
        no_role_account,
    )
    composer.send()
    return approved_proposal_client


@pytest.fixture(scope="function")
def reviewed_proposal_client(
    xgov_council: SigningAccount,
    min_fee_times_2: AlgoAmount,
    cleaned_approved_proposal_client: ProposalClient,
) -> ProposalClient:
    cleaned_approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(
            sender=xgov_council.address, static_fee=min_fee_times_2
        ),
    )
    return cleaned_approved_proposal_client


@pytest.fixture(scope="function")
def blocked_proposal_client(
    xgov_council: SigningAccount,
    min_fee_times_2: AlgoAmount,
    cleaned_approved_proposal_client: ProposalClient,
) -> ProposalClient:
    cleaned_approved_proposal_client.send.review(
        args=ReviewArgs(block=True),
        params=CommonAppCallParams(
            sender=xgov_council.address, static_fee=min_fee_times_2
        ),
    )
    return cleaned_approved_proposal_client


@pytest.fixture(scope="function")
def funded_proposal_client(
    min_fee_times_3: AlgoAmount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    reviewed_proposal_client: ProposalClient,
) -> ProposalClient:
    xgov_registry_mock_client.send.pay_grant_proposal(
        args=PayGrantProposalArgs(proposal_app=reviewed_proposal_client.app_id),
        params=CommonAppCallParams(static_fee=min_fee_times_3),
    )
    return reviewed_proposal_client


@pytest.fixture(scope="function")
def alternative_proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )

    proposal_app_id = xgov_registry_mock_client.send.create_empty_proposal(
        args=CreateEmptyProposalArgs(proposer=no_role_account.address),
        params=CommonAppCallParams(static_fee=min_fee_times_3),
    )

    client = ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id.abi_return,  # type: ignore
        default_sender=no_role_account.address,
    )

    return client


@pytest.fixture(scope="function")
def alternative_draft_proposal_client(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    alternative_proposal_client: ProposalClient,
) -> ProposalClient:
    open_proposal(
        alternative_proposal_client,
        algorand_client,
        no_role_account,
    )

    return alternative_proposal_client


@pytest.fixture(scope="function")
def alternative_submitted_proposal_client(
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    alternative_draft_proposal_client: ProposalClient,
) -> ProposalClient:
    submit_proposal(
        alternative_draft_proposal_client,
        xgov_registry_mock_client,
        no_role_account,
    )

    return alternative_draft_proposal_client
