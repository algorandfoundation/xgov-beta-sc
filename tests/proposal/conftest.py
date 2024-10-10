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

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.client import XgovRegistryMockClient
from tests.proposal.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    INITIAL_FUNDS,
)


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client


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
def committee_members(algorand_client: AlgorandClient) -> list[AddressAndSigner]:
    accounts = [
        algorand_client.account.random() for _ in range(DEFAULT_COMMITTEE_MEMBERS)
    ]

    for account in accounts:
        ensure_funded(
            algorand_client.client.algod,
            EnsureBalanceParameters(
                account_to_fund=account.address,
                min_spending_balance_micro_algos=INITIAL_FUNDS,
            ),
        )

    return accounts


@pytest.fixture(scope="session")
def xgov_registry_mock_client(
    algorand_client: AlgorandClient,
    committee_publisher: AddressAndSigner,
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
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    client.set_committee_publisher(committee_publisher=committee_publisher.address)
    client.set_committee_id(committee_id=DEFAULT_COMMITTEE_ID)
    client.set_committee_members(committee_members=DEFAULT_COMMITTEE_MEMBERS)
    client.set_committee_votes(committee_votes=DEFAULT_COMMITTEE_VOTES)

    return client


@pytest.fixture(scope="function")
def proposal_client(
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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


@pytest.fixture(scope="session")
def committee_publisher(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account
