from typing import Final
from algokit_utils import LogicError, AlgoAmount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, TypedGlobalState
)
from smart_contracts.xgov_registry.config import (
    MIN_REQUESTED_AMOUNT,
)

LogicErrorType: type[LogicError] = LogicError

TREASURY_AMOUNT: Final[AlgoAmount] = AlgoAmount(micro_algo=MIN_REQUESTED_AMOUNT)
UNLIMITED_KYC_EXPIRATION = 2**64 - 1


def assert_registry_config(
    xgov_registry_client: XGovRegistryClient,
    *,
    xgov_fee: int,
    daemon_ops_funding_bps: int,
    proposal_commitment_bps: int,
    proposer_fee: int,
    open_proposal_fee: int,
    min_requested_amount: int,
    max_requested_amount_small: int,
    max_requested_amount_medium: int,
    max_requested_amount_large: int,
    discussion_duration_small: int,
    discussion_duration_medium: int,
    discussion_duration_large: int,
    discussion_duration_xlarge: int,
    voting_duration_small: int,
    voting_duration_medium: int,
    voting_duration_large: int,
    voting_duration_xlarge: int,
    quorum_small: int,
    quorum_medium: int,
    quorum_large: int,
    weighted_quorum_small: int,
    weighted_quorum_medium: int,
    weighted_quorum_large: int,
) -> None:
    global_state = xgov_registry_client.state.global_state
    assert global_state.xgov_fee == xgov_fee
    assert global_state.daemon_ops_funding_bps == daemon_ops_funding_bps
    assert global_state.proposal_commitment_bps == proposal_commitment_bps
    assert global_state.proposer_fee == proposer_fee
    assert global_state.open_proposal_fee == open_proposal_fee
    assert global_state.min_requested_amount == min_requested_amount
    assert global_state.max_requested_amount_small == max_requested_amount_small
    assert global_state.max_requested_amount_medium == max_requested_amount_medium
    assert global_state.max_requested_amount_large == max_requested_amount_large
    assert global_state.discussion_duration_small == discussion_duration_small
    assert global_state.discussion_duration_medium == discussion_duration_medium
    assert global_state.discussion_duration_large == discussion_duration_large
    assert global_state.discussion_duration_xlarge == discussion_duration_xlarge
    assert global_state.voting_duration_small == voting_duration_small
    assert global_state.voting_duration_medium == voting_duration_medium
    assert global_state.voting_duration_large == voting_duration_large
    assert global_state.voting_duration_xlarge == voting_duration_xlarge
    assert global_state.quorum_small == quorum_small
    assert global_state.quorum_medium == quorum_medium
    assert global_state.quorum_large == quorum_large
    assert global_state.weighted_quorum_small == weighted_quorum_small
    assert global_state.weighted_quorum_medium == weighted_quorum_medium
    assert global_state.weighted_quorum_large == weighted_quorum_large


def assert_committee(
    xgov_registry_client: XGovRegistryClient,
    *,
    committee_id: bytes,
    committee_size: int,
    committee_votes: int,
) -> None:
    global_state = xgov_registry_client.state.global_state
    assert bytes(global_state.committee_id) == committee_id
    assert global_state.committee_members == committee_size
    assert global_state.committee_votes == committee_votes


def assert_get_state(xgov_registry_client: XGovRegistryClient, get_state: TypedGlobalState) -> None:
    global_state = xgov_registry_client.state.global_state
    assert global_state.xgov_fee == get_state.xgov_fee
    assert global_state.daemon_ops_funding_bps == get_state.daemon_ops_funding_bps
    assert global_state.proposal_commitment_bps == get_state.proposal_commitment_bps
    assert global_state.proposer_fee == get_state.proposer_fee
    assert global_state.open_proposal_fee == get_state.open_proposal_fee
    assert global_state.min_requested_amount == get_state.min_requested_amount
    assert global_state.max_requested_amount_small == get_state.max_requested_amount[0]
    assert global_state.max_requested_amount_medium == get_state.max_requested_amount[1]
    assert global_state.max_requested_amount_large == get_state.max_requested_amount[2]
    assert global_state.discussion_duration_small == get_state.discussion_duration[0]
    assert global_state.discussion_duration_medium == get_state.discussion_duration[1]
    assert global_state.discussion_duration_large == get_state.discussion_duration[2]
    assert global_state.discussion_duration_xlarge == get_state.discussion_duration[3]
    assert global_state.voting_duration_small == get_state.voting_duration[0]
    assert global_state.voting_duration_medium == get_state.voting_duration[1]
    assert global_state.voting_duration_large == get_state.voting_duration[2]
    assert global_state.voting_duration_xlarge == get_state.voting_duration[3]
    assert global_state.quorum_small == get_state.quorum[0]
    assert global_state.quorum_medium == get_state.quorum[1]
    assert global_state.quorum_large == get_state.quorum[2]
    assert global_state.weighted_quorum_small == get_state.weighted_quorum[0]
    assert global_state.weighted_quorum_medium == get_state.weighted_quorum[1]
    assert global_state.weighted_quorum_large == get_state.weighted_quorum[2]


def get_xgov_fee(xgov_registry_client: XGovRegistryClient) -> AlgoAmount:
    return AlgoAmount(micro_algo=xgov_registry_client.state.global_state.xgov_fee)


def get_proposer_fee(xgov_registry_client: XGovRegistryClient) -> AlgoAmount:
    return AlgoAmount(micro_algo=xgov_registry_client.state.global_state.proposer_fee)


def get_open_proposal_fee(xgov_registry_client: XGovRegistryClient) -> AlgoAmount:
    return AlgoAmount(micro_algo=xgov_registry_client.state.global_state.open_proposal_fee)
