from pathlib import Path

import pytest

from algokit_utils import (
    EnsureBalanceParameters,
    ensure_funded,
    get_algod_client,
    get_indexer_client,
    get_localnet_default_account,
    is_localnet,
)

from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.util import algos_to_microalgos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv
from tests.xgov_registry.common import AddressAndSignerFromAccount

from models.account import Account

INITIAL_FUNDS: int = algos_to_microalgos(10_000)  # type: ignore[no-untyped-call]


@pytest.fixture(autouse=True, scope="session")
def environment_fixture() -> None:
    env_path = Path(__file__).parent.parent / ".env.localnet"
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    client = get_algod_client()

    # you can remove this assertion to test on other networks,
    # included here to prevent accidentally running against other networks
    assert is_localnet(client)
    return client


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return get_indexer_client()


@pytest.fixture(scope="session")
def faucet(algod_client: AlgodClient) -> Account:
    faucet = get_localnet_default_account(algod_client)
    return Account(private_key=faucet.private_key, client=algod_client)

@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client

@pytest.fixture(scope="function")
def deployer(algorand_client: AlgorandClient) -> Account:
    deployer = get_localnet_default_account(algorand_client.client.algod)
    account = AddressAndSignerFromAccount(deployer)
    algorand_client.account.set_signer(deployer.address, account.signer)

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=deployer.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    return deployer