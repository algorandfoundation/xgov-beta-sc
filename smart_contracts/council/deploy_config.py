import logging
import os

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    OnSchemaBreak,
    OnUpdate,
)
from algosdk import encoding
from algosdk.atomic_transaction_composer import TransactionSigner

from smart_contracts.artifacts.council.council_client import (
    APP_SPEC,
    AddMemberArgs,
    CouncilClient,
    CouncilFactory,
    CouncilMethodCallCreateParams,
    CreateArgs,
    RemoveMemberArgs,
)

logger = logging.getLogger(__name__)

deployer_min_spending = AlgoAmount.from_algo(3)
# Cover box storage costs for council members and votes
# mbr on votes is freed after all members vote
council_min_spending = AlgoAmount.from_algo(2)


def _get_council_factory(
    algorand_client: AlgorandClient,
    *,
    deployer_address: str,
    signer: TransactionSigner,
    version: str | None = None,
) -> CouncilFactory:
    return algorand_client.client.get_typed_app_factory(
        typed_factory=CouncilFactory,
        default_sender=deployer_address,
        default_signer=signer,
        version=version,
    )


def _get_council_app_client(
    algorand_client: AlgorandClient,
    *,
    deployer_address: str,
    signer: TransactionSigner,
    creator_address: str,
) -> CouncilClient:
    factory = _get_council_factory(
        algorand_client,
        deployer_address=deployer_address,
        signer=signer,
    )

    council_app_id = os.environ.get("COUNCIL_APP_ID", "").strip()
    if council_app_id:
        try:
            app_id = int(council_app_id)
        except ValueError as e:
            raise ValueError("COUNCIL_APP_ID must be an integer") from e

        return factory.get_app_client_by_id(app_id=app_id)

    return factory.get_app_client_by_creator_and_name(
        creator_address=creator_address,
        app_name=APP_SPEC.name,
    )


def _get_member_address() -> str:
    member_address = os.environ.get("COUNCIL_MEMBER_ADDRESS", "").strip()
    if not member_address:
        raise ValueError("COUNCIL_MEMBER_ADDRESS must be set")

    try:
        encoding.decode_address(member_address)  # type: ignore[no-untyped-call]
    except Exception as e:
        raise ValueError("COUNCIL_MEMBER_ADDRESS must be a valid Algorand address") from e

    return member_address


def _get_deployer_sender(algorand_client: AlgorandClient) -> tuple[str, TransactionSigner]:
    deployer = algorand_client.account.from_environment("DEPLOYER")
    logger.info(f"Using deployer address: {deployer.address}")
    return deployer.address, deployer.signer


def _deploy_council(algorand_client: AlgorandClient) -> None:
    deployer_address, signer = _get_deployer_sender(algorand_client)

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer_address, min_spending_balance=deployer_min_spending
    )

    # Get the registry app ID from environment
    if not algorand_client.client.is_localnet():
        registry_app_id = int(os.environ.get("XGOV_REGISTRY_APP_ID", "0"))
        if registry_app_id == 0:
            raise ValueError("XGOV_REGISTRY_APP_ID must be set")
    else:
        registry_app_id = 42  # LocalNet mock registry app ID

    logger.info(f"Using xGov Registry App ID: {registry_app_id} for Council")

    # Get admin address (defaults to deployer)
    admin_address = os.environ.get("COUNCIL_ADMIN", deployer_address)
    logger.info(f"Using admin address: {admin_address}")

    version = os.environ.get("COUNCIL_VERSION", None)

    factory = _get_council_factory(
        algorand_client,
        deployer_address=deployer_address,
        signer=signer,
        version=version,
    )

    client, result = factory.deploy(
        on_update=OnUpdate.AppendApp,
        on_schema_break=OnSchemaBreak.AppendApp,
        create_params=CouncilMethodCallCreateParams(
            args=CreateArgs(
                registry_id=registry_app_id,
            ),
        ),
    )

    logger.info(f"Council deployed with app ID: {client.app_id}")
    logger.info(f"Operation performed: {result.operation_performed}")

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=council_min_spending,
    )


def _update_member(command: str, algorand_client: AlgorandClient) -> None:
    deployer_address, signer = _get_deployer_sender(algorand_client)
    member_address = _get_member_address()

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer_address,
        min_spending_balance=deployer_min_spending,
    )

    client = _get_council_app_client(
        algorand_client,
        deployer_address=deployer_address,
        signer=signer,
        creator_address=deployer_address,
    )

    params = CommonAppCallParams(
        sender=deployer_address,
        signer=signer,
    )
    if command == "add_member":
        client.send.add_member(args=AddMemberArgs(address=member_address), params=params)
        logger.info(f"Added council member: {member_address}")
    elif command == "remove_member":
        client.send.remove_member(
            args=RemoveMemberArgs(address=member_address),
            params=params,
        )
        logger.info(f"Removed council member: {member_address}")
    else:
        raise ValueError(f"Unknown member command: {command}")


def deploy() -> None:
    algorand_client = AlgorandClient.from_environment()
    command = os.environ.get("COUNCIL_DEPLOY_COMMAND", "deploy")
    logger.info(f"COUNCIL_DEPLOY_COMMAND: {command}")

    if command == "deploy":
        _deploy_council(algorand_client)
    elif command in ("add_member", "remove_member"):
        _update_member(command, algorand_client)
    else:
        raise ValueError(f"Unknown command: {command}. Valid commands are: deploy, add_member, remove_member")
