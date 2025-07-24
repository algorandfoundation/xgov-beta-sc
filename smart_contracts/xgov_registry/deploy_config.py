import logging
import os
import random

from algokit_utils import (
    AlgorandClient,
    AppClientCompilationParams,
    CommonAppCallCreateParams,
    OnSchemaBreak,
    OnUpdate,
)

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy() -> None:
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
    )

    algorand_client = AlgorandClient.from_environment()
    deployer = algorand_client.account.from_environment("DEPLOYER")

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

    app_client, _ = factory.deploy(
        on_schema_break=OnSchemaBreak.AppendApp,
        on_update=(OnUpdate.UpdateApp if not fresh_deploy else OnUpdate.AppendApp),
        create_params=XGovRegistryMethodCallCreateParams(
            extra_program_pages=create_params.extra_program_pages,
            method=create_params.method.name,
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
