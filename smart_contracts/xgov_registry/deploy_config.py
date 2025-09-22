import logging
import os
import random
from typing import Optional

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AppClientCompilationParams,
    CommonAppCallCreateParams,
    CommonAppCallParams,
    OnSchemaBreak,
    OnUpdate,
)
from algosdk import encoding
from algosdk.transaction import Multisig

from smart_contracts.artifacts.proposal.proposal_client import ProposalFactory
from smart_contracts.xgov_registry.helpers import (
    load_proposal_contract_data_size_per_transaction,
)
from smart_contracts.xgov_registry.vault_tx_signer import (
    HashicorpVaultMultisigTransactionSigner,
    TransitSecretEngine,
    _create_vault_auth_from_env,
    create_vault_multisig_signer_from_env,
)

logger = logging.getLogger(__name__)

deployer_min_spending = AlgoAmount.from_algo(3)
registry_min_spending = AlgoAmount.from_algo(4)  # min balance for proposal box storage


def _create_vault_signer_from_env() -> (
    tuple[Optional[HashicorpVaultMultisigTransactionSigner], str, Optional[object]]
):
    """Helper function to create vault multisig signer from environment variables.

    Creates a 1-of-2 multisig where:
    - One key comes from HashiCorp Vault (retrieved by VAULT_KEY_NAME)
    - Other key is an Algorand address from environment (MULTISIG_ALGORAND_ADDRESS),
      defaulting to DEPLOYER address if not set

    The function connects to Vault, retrieves the public key for the specified key name,
    converts it to an Algorand address, and creates a proper multisig with both addresses.

    Environment variables needed:
    - VAULT_URL: HashiCorp Vault URL
    - VAULT_KEY_NAME: Name of the key in Vault's transit engine
    - MULTISIG_ALGORAND_ADDRESS: Algorand address for the other multisig key
    - VAULT_TRANSIT_MOUNT_PATH: Transit engine mount path (optional, defaults to "transit")
    - Plus all standard Vault authentication variables (VAULT_TOKEN, VAULT_ROLE_ID, etc.)

    Returns tuple of (vault_signer, deployer_address, deployer_account) where:
    - vault_signer is the HashiCorp Vault multisig signer or None if not available
    - deployer_address is the multisig address to use for deployment
    - deployer_account is the AlgoKit account object or None if using vault
    """
    algorand_client = AlgorandClient.from_environment()
    github_deployer = algorand_client.account.from_environment("DEPLOYER")

    try:
        # Get the Algorand address for the multisig
        algorand_address = os.environ.get(
            "MULTISIG_ALGORAND_ADDRESS", github_deployer.address
        )
        if not algorand_address:
            raise ValueError(
                "MULTISIG_ALGORAND_ADDRESS environment variable is required for vault multisig"
            )

        # Get the vault key name
        vault_key_name = os.environ.get("VAULT_KEY_NAME")
        if not vault_key_name:
            raise ValueError("VAULT_KEY_NAME environment variable is required")

        # Get Vault connection details
        vault_url = os.environ.get("VAULT_URL")
        transit_mount_path = os.environ.get("VAULT_TRANSIT_MOUNT_PATH", "transit")

        if not vault_url:
            raise ValueError("VAULT_URL environment variable is required")

        # Create Vault authentication and transit engine to get the public key
        vault_auth = _create_vault_auth_from_env()
        transit_engine = TransitSecretEngine(
            vault_url=vault_url, vault_auth=vault_auth, mount_path=transit_mount_path
        )

        # Get the public key bytes from Vault for the specified key
        vault_public_key_bytes = transit_engine.setup_and_derive_public_key(
            vault_key_name
        )

        # Convert to Algorand address
        vault_address: str = encoding.encode_address(vault_public_key_bytes)  # type: ignore
        logger.info(
            f"Retrieved Vault public key for key '{vault_key_name}': {vault_address}"
        )

        # Set VAULT_KEY_NAMES for the multisig function (it expects comma-separated names)
        # For a 1-of-2 multisig, we only need one vault key
        os.environ["VAULT_KEY_NAMES"] = vault_key_name

        # Create 1-of-2 multisig with both addresses (Vault key and provided Algorand address)
        # Sort addresses to ensure consistent multisig address generation
        addresses: list[str] = sorted([vault_address, algorand_address])
        multisig = Multisig(  # type: ignore
            version=1,
            threshold=1,
            addresses=addresses,
        )

        vault_signer = create_vault_multisig_signer_from_env(multisig)
        deployer_address = vault_signer.address
        logger.info(
            f"Using Vault multisig transaction signer with address: {deployer_address}"
        )
        return vault_signer, deployer_address, None

    except (ValueError, KeyError) as e:
        logger.info(
            f"Vault signer not available ({e}), falling back to environment-based deployer"
        )
        deployer = algorand_client.account.from_environment("DEPLOYER")
        return None, deployer.address, deployer


def _deploy_xgov_registry() -> None:
    from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
        ConfigXgovRegistryArgs,
        InitProposalContractArgs,
        SetCommitteeManagerArgs,
        SetKycProviderArgs,
        SetPayorArgs,
        SetXgovCouncilArgs,
        SetXgovDaemonArgs,
        SetXgovSubscriberArgs,
        XGovRegistryConfig,
        XGovRegistryFactory,
        XGovRegistryFactoryCreateParams,
        XGovRegistryMethodCallCreateParams,
        XGovRegistryMethodCallUpdateParams,
    )

    algorand_client = AlgorandClient.from_environment()

    # Try to create Vault signer first, fallback to environment if not available
    vault_signer, deployer_address, deployer = _create_vault_signer_from_env()

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer_address, min_spending_balance=deployer_min_spending
    )

    template_values = {"entropy": b""}

    fresh_deploy = os.environ.get("XGOV_REG_FRESH_DEPLOY", "false").lower() == "true"
    if fresh_deploy:
        logger.info("Fresh deployment requested")
        template_values = {
            "entropy": random.randbytes(16),  # trick to ensure a fresh deployment
        }

    version = os.environ.get("XGOV_REGISTRY_VERSION", None)

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XGovRegistryFactory,
        default_sender=deployer_address,
        default_signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
        compilation_params=AppClientCompilationParams(
            deploy_time_params=template_values
        ),
        version=version,
    )

    create_params = XGovRegistryFactoryCreateParams(factory.app_factory).create(
        params=CommonAppCallCreateParams(
            extra_program_pages=3,
        ),
        compilation_params=AppClientCompilationParams(
            deploy_time_params=template_values,
        ),
    )

    update_params = XGovRegistryFactoryCreateParams(
        factory.app_factory
    ).update_xgov_registry(
        compilation_params=AppClientCompilationParams(
            deploy_time_params=template_values,
        ),
    )

    app_client, _ = factory.deploy(
        on_schema_break=OnSchemaBreak.AppendApp,
        on_update=(OnUpdate.UpdateApp if not fresh_deploy else OnUpdate.AppendApp),
        create_params=XGovRegistryMethodCallCreateParams(
            extra_program_pages=create_params.extra_program_pages,
            method=create_params.method.name,
        ),
        update_params=XGovRegistryMethodCallUpdateParams(
            method=update_params.method.name,
        ),
    )

    logger.info("uploading proposal approval program to box")

    proposal_factory = algorand_client.client.get_typed_app_factory(
        typed_factory=ProposalFactory,
    )

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=app_client.app_address,
        min_spending_balance=registry_min_spending,
    )

    compiled_proposal = proposal_factory.app_factory.compile()
    app_client.send.init_proposal_contract(
        args=InitProposalContractArgs(
            size=len(compiled_proposal.approval_program),
        ),
        params=CommonAppCallParams(
            sender=deployer_address,
            signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
        ),
    )

    data_size_per_transaction = load_proposal_contract_data_size_per_transaction()
    bulks = 1 + len(compiled_proposal.approval_program) // data_size_per_transaction
    for i in range(bulks):
        chunk = compiled_proposal.approval_program[
            i * data_size_per_transaction : (i + 1) * data_size_per_transaction
        ]
        app_client.send.load_proposal_contract(
            args=(i * data_size_per_transaction, chunk),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )

    should_set_roles = os.environ.get("XGOV_REG_SET_ROLES", "false").lower() == "true"
    if should_set_roles:
        test_admin = os.environ["TEST_ADMIN"]
        test_xgov_daemon = os.environ["TEST_XGOV_DAEMON"]
        logger.info(f"Setting administrative roles to {test_admin}")
        admin_roles = app_client.new_group()
        admin_roles.set_committee_manager(
            args=SetCommitteeManagerArgs(
                manager=test_admin,
            ),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )
        admin_roles.set_xgov_daemon(
            args=SetXgovDaemonArgs(xgov_daemon=test_xgov_daemon),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )
        admin_roles.set_xgov_council(
            args=SetXgovCouncilArgs(council=test_admin),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )
        admin_roles.set_xgov_subscriber(
            args=SetXgovSubscriberArgs(subscriber=test_admin),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )
        admin_roles.set_payor(
            args=SetPayorArgs(payor=test_admin),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )
        admin_roles.set_kyc_provider(
            args=SetKycProviderArgs(provider=test_admin),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )
        admin_roles.send()

    else:
        logger.info("Skipping setting roles as requested")

    should_configure = os.environ.get("XGOV_REG_CONFIGURE", "false").lower() == "true"
    if should_configure:
        logger.info("Configuring xGov registry")
        max_requested_amounts = [
            int(num) for num in os.environ["XGOV_CFG_MAX_REQUESTED_AMOUNT"].split(",")
        ]
        discussion_durations = [
            int(num) for num in os.environ["XGOV_CFG_DISCUSSION_DURATION"].split(",")
        ]
        voting_durations = [
            int(num) for num in os.environ["XGOV_CFG_VOTING_DURATION"].split(",")
        ]
        quorums = [int(num) for num in os.environ["XGOV_CFG_QUORUM"].split(",")]
        weighted_quorums = [
            int(num) for num in os.environ["XGOV_CFG_WEIGHTED_QUORUM"].split(",")
        ]
        config = XGovRegistryConfig(
            xgov_fee=int(os.environ["XGOV_CFG_XGOV_FEE"]),
            proposer_fee=int(os.environ["XGOV_CFG_PROPOSER_FEE"]),
            open_proposal_fee=int(os.environ["XGOV_CFG_OPEN_PROPOSAL_FEE"]),
            daemon_ops_funding_bps=int(os.environ["XGOV_CFG_DAEMON_OPS_FUNDING_BPS"]),
            proposal_commitment_bps=int(os.environ["XGOV_CFG_PROPOSAL_COMMITMENT_BPS"]),
            min_requested_amount=int(os.environ["XGOV_CFG_MIN_REQUESTED_AMOUNT"]),
            max_requested_amount=(
                max_requested_amounts[0],
                max_requested_amounts[1],
                max_requested_amounts[2],
            ),
            discussion_duration=(
                discussion_durations[0],
                discussion_durations[1],
                discussion_durations[2],
                discussion_durations[3],
            ),
            voting_duration=(
                voting_durations[0],
                voting_durations[1],
                voting_durations[2],
                voting_durations[3],
            ),
            quorum=(quorums[0], quorums[1], quorums[2]),
            weighted_quorum=(
                weighted_quorums[0],
                weighted_quorums[1],
                weighted_quorums[2],
            ),
        )
        app_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=config,
            ),
            params=CommonAppCallParams(
                sender=deployer_address,
                signer=vault_signer if vault_signer else (deployer.signer if deployer else None),  # type: ignore
            ),
        )
    else:
        logger.info("Skipping xGov registry configuration as requested")


def _set_roles() -> None:
    from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
        APP_SPEC,
        SetCommitteeManagerArgs,
        SetKycProviderArgs,
        SetPayorArgs,
        SetXgovCouncilArgs,
        SetXgovDaemonArgs,
        SetXgovManagerArgs,
        SetXgovSubscriberArgs,
        XGovRegistryFactory,
    )

    algorand_client = AlgorandClient.from_environment()

    # Try to create Vault signer first, fallback to environment if not available
    vault_signer, deployer_address, deployer = _create_vault_signer_from_env()

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer_address, min_spending_balance=deployer_min_spending
    )

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XGovRegistryFactory,
        default_sender=deployer_address,
    )

    app_client = factory.get_app_client_by_creator_and_name(
        creator_address=deployer_address,
        app_name=APP_SPEC.name,
    )

    roles_group = app_client.new_group()

    if xgov_manager := os.environ.get("XGOV_REG_SET_ROLES_XGOV_MANAGER"):
        roles_group.set_xgov_manager(args=SetXgovManagerArgs(manager=xgov_manager))
    if payor := os.environ.get("XGOV_REG_SET_ROLES_PAYOR"):
        roles_group.set_payor(args=SetPayorArgs(payor=payor))
    if xgov_council := os.environ.get("XGOV_REG_SET_ROLES_XGOV_COUNCIL"):
        roles_group.set_xgov_council(args=SetXgovCouncilArgs(council=xgov_council))
    if xgov_subscriber := os.environ.get("XGOV_REG_SET_ROLES_XGOV_SUBSCRIBER"):
        roles_group.set_xgov_subscriber(
            args=SetXgovSubscriberArgs(subscriber=xgov_subscriber)
        )
    if kyc_provider := os.environ.get("XGOV_REG_SET_ROLES_KYC_PROVIDER"):
        roles_group.set_kyc_provider(args=SetKycProviderArgs(provider=kyc_provider))
    if committee_manager := os.environ.get("XGOV_REG_SET_ROLES_COMMITTEE_MANAGER"):
        roles_group.set_committee_manager(
            args=SetCommitteeManagerArgs(manager=committee_manager)
        )
    if xgov_daemon := os.environ.get("XGOV_REG_SET_ROLES_XGOV_DAEMON"):
        roles_group.set_xgov_daemon(args=SetXgovDaemonArgs(xgov_daemon=xgov_daemon))

    try:
        roles_group.send()
        logger.info("Roles successfully set using roles_group.send()")
    except Exception as e:
        logger.error(f"Failed to set roles using roles_group.send(): {e}")
        raise


def _configure_xgov_registry() -> None:
    from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
        APP_SPEC,
        ConfigXgovRegistryArgs,
        XGovRegistryConfig,
        XGovRegistryFactory,
    )

    algorand_client = AlgorandClient.from_environment()

    # Try to create Vault signer first, fallback to environment if not available
    vault_signer, deployer_address, deployer = _create_vault_signer_from_env()

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer_address, min_spending_balance=deployer_min_spending
    )

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XGovRegistryFactory,
        default_sender=deployer_address,
    )

    app_client = factory.get_app_client_by_creator_and_name(
        creator_address=deployer_address,
        app_name=APP_SPEC.name,
    )

    current_state = app_client.state.global_state

    # Helper function to parse comma-separated integers with fallback to defaults
    def parse_comma_separated_ints(env_var_name: str, defaults: list[int]) -> list[int]:
        env_value = os.environ.get(env_var_name, "")
        if not env_value or env_value.strip() == "":
            return defaults
        try:
            return [int(num.strip()) for num in env_value.split(",") if num.strip()]
        except ValueError:
            logger.warning(f"Invalid format for {env_var_name}, using defaults")
            return defaults

    # Helper function to parse single integer with fallback to default
    def parse_int(env_var_name: str, default: int) -> int:
        env_value = os.environ.get(env_var_name, "")
        if not env_value or env_value.strip() == "":
            return default
        try:
            return int(env_value.strip())
        except ValueError:
            logger.warning(
                f"Invalid format for {env_var_name}, using default: {default}"
            )
            return default

    max_requested_amounts = parse_comma_separated_ints(
        "XGOV_CFG_MAX_REQUESTED_AMOUNT",
        [
            current_state.max_requested_amount_small,
            current_state.max_requested_amount_medium,
            current_state.max_requested_amount_large,
        ],
    )
    discussion_durations = parse_comma_separated_ints(
        "XGOV_CFG_DISCUSSION_DURATION",
        [
            current_state.discussion_duration_small,
            current_state.discussion_duration_medium,
            current_state.discussion_duration_large,
            current_state.discussion_duration_xlarge,
        ],
    )
    voting_durations = parse_comma_separated_ints(
        "XGOV_CFG_VOTING_DURATION",
        [
            current_state.voting_duration_small,
            current_state.voting_duration_medium,
            current_state.voting_duration_large,
            current_state.voting_duration_xlarge,
        ],
    )
    quorums = parse_comma_separated_ints(
        "XGOV_CFG_QUORUM",
        [
            current_state.quorum_small,
            current_state.quorum_medium,
            current_state.quorum_large,
        ],
    )
    weighted_quorums = parse_comma_separated_ints(
        "XGOV_CFG_WEIGHTED_QUORUM",
        [
            current_state.weighted_quorum_small,
            current_state.weighted_quorum_medium,
            current_state.weighted_quorum_large,
        ],
    )

    config = XGovRegistryConfig(
        xgov_fee=parse_int("XGOV_CFG_XGOV_FEE", current_state.xgov_fee),
        proposer_fee=parse_int("XGOV_CFG_PROPOSER_FEE", current_state.proposer_fee),
        open_proposal_fee=parse_int(
            "XGOV_CFG_OPEN_PROPOSAL_FEE", current_state.open_proposal_fee
        ),
        daemon_ops_funding_bps=parse_int(
            "XGOV_CFG_DAEMON_OPS_FUNDING_BPS", current_state.daemon_ops_funding_bps
        ),
        proposal_commitment_bps=parse_int(
            "XGOV_CFG_PROPOSAL_COMMITMENT_BPS", current_state.proposal_commitment_bps
        ),
        min_requested_amount=parse_int(
            "XGOV_CFG_MIN_REQUESTED_AMOUNT", current_state.min_requested_amount
        ),
        max_requested_amount=(
            max_requested_amounts[0],
            max_requested_amounts[1],
            max_requested_amounts[2],
        ),
        discussion_duration=(
            discussion_durations[0],
            discussion_durations[1],
            discussion_durations[2],
            discussion_durations[3],
        ),
        voting_duration=(
            voting_durations[0],
            voting_durations[1],
            voting_durations[2],
            voting_durations[3],
        ),
        quorum=(quorums[0], quorums[1], quorums[2]),
        weighted_quorum=(
            weighted_quorums[0],
            weighted_quorums[1],
            weighted_quorums[2],
        ),
    )

    logger.info(f"Configuring xGov registry with: {config}")
    try:
        app_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=config,
            )
        )
        logger.info("xGov registry configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure xGov registry: {e}")
        raise


def deploy() -> None:
    command = os.environ.get("XGOV_REG_DEPLOY_COMMAND")
    if command == "deploy":
        _deploy_xgov_registry()
    elif command == "set_roles":
        _set_roles()
    elif command == "configure_xgov_registry":
        _configure_xgov_registry()
    elif command == "test_vault_signer":
        # Just test creating the vault signer and print the address
        vault_signer, deployer_address, _ = _create_vault_signer_from_env()
        if vault_signer:
            logger.info(f"Vault multisig signer address: {deployer_address}")
        else:
            logger.info(
                "Vault multisig signer not configured, using environment deployer"
            )
    else:
        raise ValueError(
            f"Unknown command: {command}. Valid commands are: deploy, set_roles, configure_xgov_registry, "
            "test_vault_signer"
        )
