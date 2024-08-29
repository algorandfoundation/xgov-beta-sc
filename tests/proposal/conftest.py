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
from algosdk.encoding import encode_address
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.client import XgovRegistryMockClient
from tests.proposal.common import INITIAL_FUNDS


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
def xgov_registry_mock_client(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
) -> XgovRegistryMockClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = XgovRegistryMockClient(
        algod_client,
        creator=get_localnet_default_account(algod_client),
        indexer_client=indexer_client,
    )

    client.create_bare()

    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    return client


@pytest.fixture(scope="function")
def proposal_client(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
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
        algod_client,
        app_id=proposal_app_id.return_value,
    )

    return client


@pytest.fixture(scope="session")
def committee_publisher(xgov_registry_mock_client: XgovRegistryMockClient) -> str:
    return encode_address(  # type: ignore
        xgov_registry_mock_client.get_global_state().committee_publisher.as_bytes
    )
