from pathlib import Path

import pytest
from algokit_utils import (
    get_algod_client,
    get_indexer_client,
    get_localnet_default_account,
    is_localnet,
)
from algosdk.util import algos_to_microalgos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv

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
