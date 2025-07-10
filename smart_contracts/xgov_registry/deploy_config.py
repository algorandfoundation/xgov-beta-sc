import logging
import os
import random

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
    from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
        CreateArgs,
        Deploy,
        DeployCreate,
        UpdateXgovRegistryArgs,
        XGovRegistryClient,
        XGovRegistryConfig,
    )

    app_client = XGovRegistryClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    template_values = {"entropy": b""}

    fresh_deploy = os.environ.get("XGOV_REG_FRESH_DEPLOY", "false").lower() == "true"
    if fresh_deploy:
        logger.info("Fresh deployment requested")
        template_values = {
            "entropy": random.randbytes(16),  # trick to ensure a fresh deployment
        }

    app_client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=(
            algokit_utils.OnUpdate.UpdateApp
            if not fresh_deploy
            else algokit_utils.OnUpdate.AppendApp
        ),
        create_args=DeployCreate(args=CreateArgs(), extra_pages=3),
        update_args=Deploy(args=UpdateXgovRegistryArgs()),
        template_values=template_values,
    )

    test_admin = os.environ["TEST_ADMIN"]
    test_xgov_daemon = os.environ["TEST_XGOV_DAEMON"]
    logger.info(f"Setting administrative roles to {test_admin}")
    admin_roles = app_client.compose()
    admin_roles.set_committee_manager(manager=test_admin)
    admin_roles.set_xgov_daemon(xgov_daemon=test_xgov_daemon)
    admin_roles.set_xgov_council(council=test_admin)
    admin_roles.set_xgov_subscriber(subscriber=test_admin)
    admin_roles.set_payor(payor=test_admin)
    admin_roles.set_kyc_provider(provider=test_admin)
    admin_roles.execute()

    should_configure = os.environ.get("XGOV_REG_CONFIGURE", "false").lower() == "true"
    if should_configure:
        logger.info("Configuring xGov registry")
        config = XGovRegistryConfig(
            xgov_fee=int(os.environ["XGOV_CFG_XGOV_FEE"]),
            proposer_fee=int(os.environ["XGOV_CFG_PROPOSER_FEE"]),
            open_proposal_fee=int(os.environ["XGOV_CFG_OPEN_PROPOSAL_FEE"]),
            daemon_ops_funding_bps=int(os.environ["XGOV_CFG_DAEMON_OPS_FUNDING_BPS"]),
            proposal_commitment_bps=int(os.environ["XGOV_CFG_PROPOSAL_COMMITMENT_BPS"]),
            min_requested_amount=int(os.environ["XGOV_CFG_MIN_REQUESTED_AMOUNT"]),
            max_requested_amount=[
                int(num)
                for num in os.environ["XGOV_CFG_MAX_REQUESTED_AMOUNT"].split(",")
            ],
            discussion_duration=[
                int(num)
                for num in os.environ["XGOV_CFG_DISCUSSION_DURATION"].split(",")
            ],
            voting_duration=[
                int(num) for num in os.environ["XGOV_CFG_VOTING_DURATION"].split(",")
            ],
            quorum=[int(num) for num in os.environ["XGOV_CFG_QUORUM"].split(",")],
            weighted_quorum=[
                int(num) for num in os.environ["XGOV_CFG_WEIGHTED_QUORUM"].split(",")
            ],
        )
        app_client.config_xgov_registry(config=config)
    else:
        logger.info("Skipping xGov registry configuration as requested")
