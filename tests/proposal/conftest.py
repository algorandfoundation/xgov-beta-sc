import pytest
from algokit_utils import (
    AlgorandClient,
    TransactionParameters,
    SigningAccount, AlgoAmount, CommonAppCallParams,
)
from algokit_utils.config import config

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient, ReviewArgs
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient, XgovRegistryMockFactory, SetXgovDaemonArgs, SetXgovCouncilArgs, SetCommitteeIdArgs,
    SetCommitteeMembersArgs, SetCommitteeVotesArgs, CreateEmptyProposalArgs, VoteArgs, FundArgs
)
from smart_contracts.xgov_registry.config import MAX_REQUESTED_AMOUNT_LARGE
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    INITIAL_FUNDS,
)
from tests.conftest import min_fee_times_2
from tests.proposal.common import (
    assign_voters,
    open_proposal,
    submit_proposal,
)
from tests.utils import time_warp


@pytest.fixture(scope="function")
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
    client, _ = factory.send.create.bare()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_FUNDS,
    )

    client.send.set_xgov_daemon(args=SetXgovDaemonArgs(xgov_daemon=xgov_daemon.address))
    client.send.set_xgov_council(args=SetXgovCouncilArgs(xgov_council=xgov_council.address))
    client.send.set_committee_id(args=SetCommitteeIdArgs(committee_id=DEFAULT_COMMITTEE_ID))
    client.send.set_committee_members(args=SetCommitteeMembersArgs(committee_members=DEFAULT_COMMITTEE_MEMBERS))
    client.send.set_committee_votes(args=SetCommitteeVotesArgs(committee_votes=DEFAULT_COMMITTEE_VOTES))

    return client


@pytest.fixture(scope="function")
def proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
) -> ProposalClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )

    proposal_app_id = xgov_registry_mock_client.send.create_empty_proposal(
        args=CreateEmptyProposalArgs(proposer=proposer.address),
        params=CommonAppCallParams(static_fee=min_fee_times_3)
    )

    client = ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id.abi_return,
        default_sender=proposer.address
    )

    return client


@pytest.fixture(scope="function")
def draft_proposal_client(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    open_proposal(
        proposal_client,
        algorand_client,
        proposer
    )
    return proposal_client


@pytest.fixture(scope="function")
def submitted_proposal_client(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
) -> ProposalClient:
    submit_proposal(
        draft_proposal_client,
        xgov_registry_mock_client,
        proposer,
    )
    return draft_proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client(
    submitted_proposal_client: ProposalClient,
    committee_members: list[SigningAccount],
    xgov_daemon: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    composer = submitted_proposal_client.new_group()

    assign_voters(
        composer,
        committee_members,
        xgov_daemon,
    )
    composer.send()

    return submitted_proposal_client


@pytest.fixture(scope="function")
def rejected_proposal_client(
    voting_proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> ProposalClient:
    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )

    return voting_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client(
    voting_proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_members: list[SigningAccount],
    min_fee_times_2: AlgoAmount,
) -> ProposalClient:
    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.send.vote(
            args=VoteArgs(
                proposal_app=voting_proposal_client.app_id,
                voter=committee_member.address,
                approvals=10,
                rejections=0,
            ),
            params=CommonAppCallParams(static_fee=min_fee_times_2)
        )

    reg_gs = xgov_registry_mock_client.state.global_state

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.send.scrutiny()

    return voting_proposal_client


@pytest.fixture(scope="function")
def reviewed_proposal_client(
    approved_proposal_client: ProposalClient,
    xgov_council: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(sender=xgov_council.address)
    )
    return approved_proposal_client


@pytest.fixture(scope="function")
def blocked_proposal_client(
    approved_proposal_client: ProposalClient,
    xgov_council: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    min_fee_times_2: AlgoAmount,
) -> ProposalClient:
    approved_proposal_client.send.review(
        args=ReviewArgs(block=True),
        params=CommonAppCallParams(sender=xgov_council.address, static_fee=min_fee_times_2)
    )
    return approved_proposal_client


@pytest.fixture(scope="function")
def funded_proposal_client(
    reviewed_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    xgov_registry_mock_client.send.fund(
        args=FundArgs(proposal_app=reviewed_proposal_client.app_id),
    )
    return reviewed_proposal_client


@pytest.fixture(scope="function")
def alternative_proposal_client(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    proposal_app_id = xgov_registry_mock_client.send.create_empty_proposal(
        args=CreateEmptyProposalArgs(proposer=no_role_account.address),
    )

    client = ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id.return_value,
    )

    return client


@pytest.fixture(scope="function")
def alternative_draft_proposal_client(
    alternative_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    open_proposal(
        alternative_proposal_client,
        algorand_client,
        no_role_account,
    )

    return alternative_proposal_client


@pytest.fixture(scope="function")
def alternative_submitted_proposal_client(
    alternative_draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    no_role_account: SigningAccount,
    xgov_daemon: SigningAccount,
) -> ProposalClient:
    submit_proposal(
        alternative_draft_proposal_client,
        xgov_registry_mock_client,
        no_role_account,
    )

    return alternative_draft_proposal_client
