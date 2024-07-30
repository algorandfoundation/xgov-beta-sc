import logging

import algokit_utils
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    from smart_contracts.artifacts.proposal.client import (
        ProposalClient,
    )

    app_client = ProposalClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )
    app_client.create_create(
        proposer="YUO5WDTSKVI5VADGDNGDCFDTPDO2TQMH2OZGZ6MLDXA6G2ZU5CD5GWVHBE"
    )
