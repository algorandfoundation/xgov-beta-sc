import logging
import os
import random

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AppClientCompilationParams,
    CommonAppCallCreateParams,
    OnSchemaBreak,
    OnUpdate,
)

logger = logging.getLogger(__name__)

deployer_min_spending = AlgoAmount.from_algo(3)


def _deploy_xgov_registry() -> None:
    from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
        ConfigXgovRegistryArgs,
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
    deployer = algorand_client.account.from_environment("DEPLOYER")
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer.address, min_spending_balance=deployer_min_spending
    )

    template_values = {"entropy": b""}

    fresh_deploy = os.environ.get("XGOV_REG_FRESH_DEPLOY", "false").lower() == "true"
    if fresh_deploy:
        logger.info("Fresh deployment requested")
        template_values = {
            "entropy": random.randbytes(16),  # trick to ensure a fresh deployment
        }

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XGovRegistryFactory,
        default_sender=deployer.address,
        compilation_params=AppClientCompilationParams(
            deploy_time_params=template_values
        ),
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

    test_admin = os.environ["TEST_ADMIN"]
    test_xgov_daemon = os.environ["TEST_XGOV_DAEMON"]
    logger.info(f"Setting administrative roles to {test_admin}")
    admin_roles = app_client.new_group()
    admin_roles.set_committee_manager(
        args=SetCommitteeManagerArgs(
            manager=test_admin,
        )
    )
    admin_roles.set_xgov_daemon(args=SetXgovDaemonArgs(xgov_daemon=test_xgov_daemon))
    admin_roles.set_xgov_council(args=SetXgovCouncilArgs(council=test_admin))
    admin_roles.set_xgov_subscriber(args=SetXgovSubscriberArgs(subscriber=test_admin))
    admin_roles.set_payor(args=SetPayorArgs(payor=test_admin))
    admin_roles.set_kyc_provider(args=SetKycProviderArgs(provider=test_admin))
    admin_roles.send()

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
            )
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
    deployer = algorand_client.account.from_environment("DEPLOYER")
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer.address, min_spending_balance=deployer_min_spending
    )

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XGovRegistryFactory,
        default_sender=deployer.address,
    )

    app_client = factory.get_app_client_by_creator_and_name(
        creator_address=deployer.address,
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
    deployer = algorand_client.account.from_environment("DEPLOYER")
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer.address, min_spending_balance=deployer_min_spending
    )

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XGovRegistryFactory,
        default_sender=deployer.address,
    )

    app_client = factory.get_app_client_by_creator_and_name(
        creator_address=deployer.address,
        app_name=APP_SPEC.name,
    )

    current_state = app_client.state.global_state
    max_requested_amounts = [
        int(num)
        for num in os.environ.get(
            "XGOV_CFG_MAX_REQUESTED_AMOUNT",
            ",".join(
                [
                    str(current_state.max_requested_amount_small),
                    str(current_state.max_requested_amount_medium),
                    str(current_state.max_requested_amount_large),
                ]
            ),
        ).split(",")
    ]
    discussion_durations = [
        int(num)
        for num in os.environ.get(
            "XGOV_CFG_DISCUSSION_DURATION",
            ",".join(
                [
                    str(current_state.discussion_duration_small),
                    str(current_state.discussion_duration_medium),
                    str(current_state.discussion_duration_large),
                    str(current_state.discussion_duration_xlarge),
                ]
            ),
        ).split(",")
    ]
    voting_durations = [
        int(num)
        for num in os.environ.get(
            "XGOV_CFG_VOTING_DURATION",
            ",".join(
                [
                    str(current_state.voting_duration_small),
                    str(current_state.voting_duration_medium),
                    str(current_state.voting_duration_large),
                    str(current_state.voting_duration_xlarge),
                ]
            ),
        ).split(",")
    ]
    quorums = [
        int(num)
        for num in os.environ.get(
            "XGOV_CFG_QUORUM",
            ",".join(
                [
                    str(current_state.quorum_small),
                    str(current_state.quorum_medium),
                    str(current_state.quorum_large),
                ]
            ),
        ).split(",")
    ]
    weighted_quorums = [
        int(num)
        for num in os.environ.get(
            "XGOV_CFG_WEIGHTED_QUORUM",
            ",".join(
                [
                    str(current_state.weighted_quorum_small),
                    str(current_state.weighted_quorum_medium),
                    str(current_state.weighted_quorum_large),
                ]
            ),
        ).split(",")
    ]

    config = XGovRegistryConfig(
        xgov_fee=int(os.environ.get("XGOV_CFG_XGOV_FEE", current_state.xgov_fee)),
        proposer_fee=int(
            os.environ.get("XGOV_CFG_PROPOSER_FEE", current_state.proposer_fee)
        ),
        open_proposal_fee=int(
            os.environ.get(
                "XGOV_CFG_OPEN_PROPOSAL_FEE", current_state.open_proposal_fee
            )
        ),
        daemon_ops_funding_bps=int(
            os.environ.get(
                "XGOV_CFG_DAEMON_OPS_FUNDING_BPS", current_state.daemon_ops_funding_bps
            )
        ),
        proposal_commitment_bps=int(
            os.environ.get(
                "XGOV_CFG_PROPOSAL_COMMITMENT_BPS",
                current_state.proposal_commitment_bps,
            )
        ),
        min_requested_amount=int(
            os.environ.get(
                "XGOV_CFG_MIN_REQUESTED_AMOUNT", current_state.min_requested_amount
            )
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
    else:
        raise ValueError(
            f"Unknown command: {command}. Valid commands are: deploy, set_roles, configure_xgov_registry"
        )
