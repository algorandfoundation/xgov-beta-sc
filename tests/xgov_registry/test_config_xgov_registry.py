import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ConfigXgovRegistryArgs,
    XGovRegistryClient,
    XGovRegistryConfig,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.xgov_registry.constants import (
    ACCOUNT_MBR,
    BPS,
    MAX_MBR_PER_APP,
    MAX_MBR_PER_BOX,
)
from tests.xgov_registry.common import assert_registry_config


def test_config_xgov_registry_success(
    xgov_registry_config: XGovRegistryConfig,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.config_xgov_registry(
        args=ConfigXgovRegistryArgs(config=xgov_registry_config)
    )
    assert_registry_config(
        xgov_registry_client=xgov_registry_client,
        xgov_fee=xgov_registry_config.xgov_fee,
        daemon_ops_funding_bps=xgov_registry_config.daemon_ops_funding_bps,
        proposal_commitment_bps=xgov_registry_config.proposal_commitment_bps,
        proposer_fee=xgov_registry_config.proposer_fee,
        open_proposal_fee=xgov_registry_config.open_proposal_fee,
        min_requested_amount=xgov_registry_config.min_requested_amount,
        max_requested_amount_small=xgov_registry_config.max_requested_amount[0],
        max_requested_amount_medium=xgov_registry_config.max_requested_amount[1],
        max_requested_amount_large=xgov_registry_config.max_requested_amount[2],
        discussion_duration_small=xgov_registry_config.discussion_duration[0],
        discussion_duration_medium=xgov_registry_config.discussion_duration[1],
        discussion_duration_large=xgov_registry_config.discussion_duration[2],
        discussion_duration_xlarge=xgov_registry_config.discussion_duration[3],
        voting_duration_small=xgov_registry_config.voting_duration[0],
        voting_duration_medium=xgov_registry_config.voting_duration[1],
        voting_duration_large=xgov_registry_config.voting_duration[2],
        voting_duration_xlarge=xgov_registry_config.voting_duration[3],
        quorum_small=xgov_registry_config.quorum[0],
        quorum_medium=xgov_registry_config.quorum[1],
        quorum_large=xgov_registry_config.quorum[2],
        weighted_quorum_small=xgov_registry_config.weighted_quorum[0],
        weighted_quorum_medium=xgov_registry_config.weighted_quorum[1],
        weighted_quorum_large=xgov_registry_config.weighted_quorum[2],
    )


def test_config_xgov_registry_not_manager(
    no_role_account: SigningAccount,
    xgov_registry_config: XGovRegistryConfig,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(config=xgov_registry_config),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_config_xgov_registry_pending_proposals(
    xgov_registry_config: XGovRegistryConfig,
    proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.config_xgov_registry(
        args=ConfigXgovRegistryArgs(config=xgov_registry_config)
    )


def test_config_xgov_registry_open_proposal_fee_too_low(
    xgov_registry_config_dict: dict,  # type: ignore
    xgov_registry_config: XGovRegistryConfig,
    xgov_registry_client: XGovRegistryClient,
) -> None:

    daemon_ops_funding_bps = xgov_registry_config.daemon_ops_funding_bps
    xgov_registry_config_dict["open_proposal_fee"] = (  # type: ignore
        (MAX_MBR_PER_APP + MAX_MBR_PER_BOX + ACCOUNT_MBR)
        * BPS
        // (BPS - daemon_ops_funding_bps)
    )

    with pytest.raises(LogicError, match=err.INVALID_OPEN_PROPOSAL_FEE):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=XGovRegistryConfig(**xgov_registry_config_dict)  # type: ignore
            ),
        )


def test_config_xgov_registry_inconsistent_requested_amount(
    xgov_registry_config_dict: dict,  # type: ignore
    xgov_registry_client: XGovRegistryClient,
) -> None:
    # Test case where max_requested_amount values are not in ascending order
    xgov_registry_config_dict["max_requested_amount"] = [
        3_000_000,
        2_000_000,
        1_000_000,
    ]  # type: ignore

    with pytest.raises(LogicError, match=err.INCONSISTENT_REQUESTED_AMOUNT_CONFIG):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=XGovRegistryConfig(**xgov_registry_config_dict)
                # type: ignore
            ),
        )


def test_config_xgov_registry_min_requested_amount_not_less_than_small(
    xgov_registry_config_dict: dict,  # type: ignore
    xgov_registry_client: XGovRegistryClient,
) -> None:
    # Test case where min_requested_amount is not less than max_requested_amount_small
    xgov_registry_config_dict["min_requested_amount"] = 2_000_000  # type: ignore
    xgov_registry_config_dict["max_requested_amount"] = [
        1_000_000,
        5_000_000,
        10_000_000,
    ]  # type: ignore

    with pytest.raises(LogicError, match=err.INCONSISTENT_REQUESTED_AMOUNT_CONFIG):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=XGovRegistryConfig(**xgov_registry_config_dict)
                # type: ignore
            ),
        )


def test_config_xgov_registry_inconsistent_discussion_duration(
    xgov_registry_config_dict: dict,  # type: ignore
    xgov_registry_client: XGovRegistryClient,
) -> None:
    # Test case where discussion_duration values are not in ascending order
    xgov_registry_config_dict["discussion_duration"] = [400, 300, 200, 100]  # type: ignore

    with pytest.raises(LogicError, match=err.INCONSISTENT_DISCUSSION_DURATION_CONFIG):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=XGovRegistryConfig(**xgov_registry_config_dict)  # type: ignore
            ),
        )


def test_config_xgov_registry_inconsistent_voting_duration(
    xgov_registry_config_dict: dict,  # type: ignore
    xgov_registry_client: XGovRegistryClient,
) -> None:
    # Test case where voting_duration values are not in ascending order
    xgov_registry_config_dict["voting_duration"] = [400, 300, 200, 100]  # type: ignore

    with pytest.raises(LogicError, match=err.INCONSISTENT_VOTING_DURATION_CONFIG):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=XGovRegistryConfig(**xgov_registry_config_dict)  # type: ignore
            ),
        )


def test_config_xgov_registry_inconsistent_quorum(
    xgov_registry_config_dict: dict,  # type: ignore
    xgov_registry_client: XGovRegistryClient,
) -> None:
    # Test case where quorum values are not in ascending order
    xgov_registry_config_dict["quorum"] = [300, 200, 100]  # type: ignore

    with pytest.raises(LogicError, match=err.INCONSISTENT_QUORUM_CONFIG):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=XGovRegistryConfig(**xgov_registry_config_dict)
                # type: ignore
            ),
        )


def test_config_xgov_registry_inconsistent_weighted_quorum(
    xgov_registry_config_dict: dict,  # type: ignore
    xgov_registry_client: XGovRegistryClient,
) -> None:
    # Test case where weighted_quorum values are not in ascending order
    xgov_registry_config_dict["weighted_quorum"] = [3000, 2000, 1000]  # type: ignore

    with pytest.raises(LogicError, match=err.INCONSISTENT_WEIGHTED_QUORUM_CONFIG):
        xgov_registry_client.send.config_xgov_registry(
            args=ConfigXgovRegistryArgs(
                config=XGovRegistryConfig(**xgov_registry_config_dict)
                # type: ignore
            ),
        )
