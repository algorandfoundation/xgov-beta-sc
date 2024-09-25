import pytest

from algokit_utils import (
    EnsureBalanceParameters,
    ensure_funded,
    get_localnet_default_account,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.config import config

from smart_contracts.artifacts.xgov_registry.client import (
    XGovRegistryClient,
    XGovRegistryConfig
)

from tests.proposal.common import INITIAL_FUNDS


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client

@pytest.fixture(scope="session")
def deployer(algorand_client: AlgorandClient) -> AddressAndSigner:
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
def random_account(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account

@pytest.fixture(scope="function")
def xgov_registry_client(
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
) -> XGovRegistryClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = XGovRegistryClient(
        algorand_client.client.algod,
        creator=get_localnet_default_account(algorand_client.client.algod),
        indexer_client=algorand_client.client.indexer,
    )

    client.create_create(
        manager=deployer.address,
        payor=deployer.address,
        comittee_manager=deployer.address
    )

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    return client

@pytest.fixture(scope="function")
def xgov_registry_config() -> XGovRegistryConfig:
    return XGovRegistryConfig(
        xgov_min_balance=1_000_000,
        proposer_fee=10_000_000,
        proposal_fee=1_000_000,
        proposal_publishing_perc=1_000,
        proposal_commitment_perc=1_000,
        min_req_amount=1_000,
        max_req_amount=[
            100_000_000,
            1_000_000_000,
            10_000_000_000,
        ],
        discussion_duration=[
            86400,
            172800,
            259200,
            345600,
        ],
        voting_duration=[
            86400,
            172800,
            259200,
            345600,
        ],
        cool_down_duration=86400,
        quorum=[
            100,
            200,
            300,
        ],
        weighted_quorum=[
            200,
            300,
            400,
        ]
    )