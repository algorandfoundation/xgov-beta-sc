import pytest
from algokit_utils import (
    EnsureBalanceParameters,
    TransactionParameters,
    ensure_funded,
    get_localnet_default_account,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.config import config
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    get_voter_box_key,
)
from tests.proposal.common import (
    INITIAL_FUNDS,
    assign_voters,
    finalize_proposal,
    submit_proposal,
)
from tests.utils import time_warp


@pytest.fixture(scope="function")
def proposer(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def not_proposer(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def committee_member(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def xgov_registry_mock_client(
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    xgov_council: AddressAndSigner,
) -> XgovRegistryMockClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = XgovRegistryMockClient(
        algorand_client.client.algod,
        creator=get_localnet_default_account(algorand_client.client.algod),
        indexer_client=algorand_client.client.indexer,
    )

    client.create_bare()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=INITIAL_FUNDS * 1_000,
        ),
    )

    client.set_xgov_daemon(xgov_daemon=xgov_daemon.address)
    client.set_xgov_council(xgov_council=xgov_council.address)
    client.set_committee_id(committee_id=DEFAULT_COMMITTEE_ID)
    client.set_committee_members(committee_members=DEFAULT_COMMITTEE_MEMBERS)
    client.set_committee_votes(committee_votes=DEFAULT_COMMITTEE_VOTES)

    return client


@pytest.fixture(scope="function")
def proposal_client(
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_3

    proposal_app_id = xgov_registry_mock_client.create_empty_proposal(
        proposer=proposer.address,
        transaction_parameters=TransactionParameters(
            suggested_params=sp,
        ),
    )

    client = ProposalClient(
        algorand_client.client.algod,
        app_id=proposal_app_id.return_value,
    )

    return client


@pytest.fixture(scope="function")
def submitted_proposal_client(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    return proposal_client


@pytest.fixture(scope="function")
def finalized_proposal_client(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_2

    finalize_proposal(
        submitted_proposal_client,
        xgov_registry_mock_client,
        proposer,
        xgov_daemon,
        sp,
    )

    return submitted_proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client(
    finalized_proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
    xgov_daemon: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_3

    composer = finalized_proposal_client.compose()

    assign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    return finalized_proposal_client


@pytest.fixture(scope="function")
def rejected_proposal_client(
    voting_proposal_client: ProposalClient,
    sp_min_fee_times_2: SuggestedParams,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    reg_gs = xgov_registry_mock_client.get_global_state()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    sp = sp_min_fee_times_2

    voting_proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    return voting_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client(
    voting_proposal_client: ProposalClient,
    sp_min_fee_times_2: SuggestedParams,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_members: list[AddressAndSigner],
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_2

    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.vote(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_member.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[
                    xgov_registry_mock_client.app_id,
                    voting_proposal_client.app_id,
                ],
                boxes=[
                    (
                        voting_proposal_client.app_id,
                        get_voter_box_key(committee_member.address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    reg_gs = xgov_registry_mock_client.get_global_state()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    voting_proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    return voting_proposal_client


@pytest.fixture(scope="function")
def reviewed_proposal_client(
    approved_proposal_client: ProposalClient,
    xgov_council: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    approved_proposal_client.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_council.address,
            signer=xgov_council.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    return approved_proposal_client


@pytest.fixture(scope="function")
def blocked_proposal_client(
    approved_proposal_client: ProposalClient,
    xgov_council: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    sp_min_fee_times_2: SuggestedParams,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_2

    approved_proposal_client.review(
        block=True,
        transaction_parameters=TransactionParameters(
            sender=xgov_council.address,
            signer=xgov_council.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    return approved_proposal_client


@pytest.fixture(scope="function")
def funded_proposal_client(
    reviewed_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_3

    xgov_registry_mock_client.fund(
        proposal_app=reviewed_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[reviewed_proposal_client.app_id],
        ),
    )

    return reviewed_proposal_client


@pytest.fixture(scope="function")
def alternative_proposal_client(
    not_proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_3

    proposal_app_id = xgov_registry_mock_client.create_empty_proposal(
        proposer=not_proposer.address,
        transaction_parameters=TransactionParameters(
            suggested_params=sp,
        ),
    )

    client = ProposalClient(
        algorand_client.client.algod,
        app_id=proposal_app_id.return_value,
    )

    return client


@pytest.fixture(scope="function")
def alternative_submitted_proposal_client(
    alternative_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    not_proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    submit_proposal(
        alternative_proposal_client,
        algorand_client,
        not_proposer,
        xgov_registry_mock_client.app_id,
    )

    return alternative_proposal_client


@pytest.fixture(scope="function")
def alternative_finalized_proposal_client(
    alternative_submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    not_proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_2

    finalize_proposal(
        alternative_submitted_proposal_client,
        xgov_registry_mock_client,
        not_proposer,
        xgov_daemon,
        sp,
    )

    return alternative_submitted_proposal_client


@pytest.fixture(scope="session")
def xgov_daemon(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def xgov_council(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def not_xgov_council(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account
