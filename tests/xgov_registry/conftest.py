import algokit_utils
import pytest
from algokit_utils import get_localnet_default_account
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.xgov_registry.client import XgovRegistryClient


@pytest.fixture(scope="session")
def xgov_registry_client(
    algod_client: AlgodClient, indexer_client: IndexerClient
) -> XgovRegistryClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = XgovRegistryClient(
        algod_client,
        creator=get_localnet_default_account(algod_client),
        indexer_client=indexer_client,
    )

    client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )
    return client
