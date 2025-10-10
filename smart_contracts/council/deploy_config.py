import logging
import os

from algokit_utils import AlgoAmount, AlgorandClient, OnSchemaBreak, OnUpdate

from ..xgov_registry.deploy_config import _create_vault_signer_from_env

logger = logging.getLogger(__name__)

deployer_min_spending = AlgoAmount.from_algo(3)
# Cover box storage costs for council members and votes
# mbr on votes is freed after all members vote
council_min_spending = AlgoAmount.from_algo(2)


def deploy() -> None:
    from smart_contracts.artifacts.council.council_client import (
        CouncilFactory,
        CreateArgs,
    )

    algorand_client = AlgorandClient.from_environment()

    # Try to create Vault signer first, fallback to environment if not available
    vault_signer, deployer_address, gh_deployer = _create_vault_signer_from_env()

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer_address, min_spending_balance=deployer_min_spending
    )

    # Get the registry app ID from environment
    registry_app_id = int(os.environ.get("XGOV_REGISTRY_APP_ID", "0"))
    if registry_app_id == 0:
        raise ValueError("XGOV_REGISTRY_APP_ID must be set")

    logger.info(f"Using registry app ID: {registry_app_id}")

    # Get admin address (defaults to deployer)
    admin_address = os.environ.get("COUNCIL_ADMIN", deployer_address)
    logger.info(f"Using admin address: {admin_address}")

    version = os.environ.get("COUNCIL_VERSION", None)

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=CouncilFactory,
        default_sender=deployer_address,
        default_signer=(
            vault_signer
            if vault_signer
            else (gh_deployer.signer if gh_deployer else None)
        ),
        version=version,
    )

    client, result = factory.deploy(
        on_update=OnUpdate.AppendApp,
        on_schema_break=OnSchemaBreak.AppendApp,
        create_params=CreateArgs(
            admin=admin_address,
            registry_id=registry_app_id,
        ),
    )

    logger.info(f"Council deployed with app ID: {client.app_id}")
    logger.info(f"Operation performed: {result.operation_performed}")

    # Fund the council app if it was created
    if result.operation_performed in ["Create", "Replace"]:
        algorand_client.send.payment(
            sender=deployer_address,
            receiver=client.app_address,
            amount=council_min_spending,
            signer=(
                vault_signer
                if vault_signer
                else (gh_deployer.signer if gh_deployer else None)
            ),
        )
        logger.info("Funded council app with 0.1 ALGO")
