from typing import Type

from algokit_utils import LogicError
from smart_contracts.artifacts.xgov_registry.client import GlobalState
from algosdk.encoding import encode_address

logic_error_type: Type[LogicError] = LogicError

def assert_registry_global_state(
    global_state: GlobalState,
    *,
    manager_address: str,
    payor_address: str,
    committee_manager_address: str
) -> None:
    assert encode_address(global_state.xgov_manager.as_bytes) == manager_address  # type: ignore
    assert encode_address(global_state.xgov_payor.as_bytes) == payor_address  # type: ignore
    assert encode_address(global_state.committee_manager.as_bytes) == committee_manager_address  # type: ignore

def assert_registry_payor(
    global_state: GlobalState,
    *,
    payor_address: str,
) -> None:
    assert encode_address(global_state.xgov_payor.as_bytes) == payor_address  # type: ignore

def assert_registry_config(
    global_state: GlobalState,
    *,
    xgov_min_balance: int,
    proposer_fee: int,
    proposal_fee: int,
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
    cool_down_duration: int,
    quorum_small: int,
    quorum_medium: int,
    quorum_large: int,
    weighted_quorum_small: int,
    weighted_quorum_medium: int,
    weighted_quorum_large: int,
) -> None:
    assert global_state["xgov_min_balance"] == xgov_min_balance
    assert global_state["proposer_fee"] == proposer_fee
    assert global_state["proposal_fee"] == proposal_fee
    assert global_state["max_requested_amount_small"] == max_requested_amount_small
    assert global_state["max_requested_amount_medium"] == max_requested_amount_medium
    assert global_state["max_requested_amount_large"] == max_requested_amount_large
    assert global_state["discussion_duration_small"] == discussion_duration_small
    assert global_state["discussion_duration_medium"] == discussion_duration_medium
    assert global_state["discussion_duration_large"] == discussion_duration_large
    assert global_state["discussion_duration_xlarge"] == discussion_duration_xlarge
    assert global_state["voting_duration_small"] == voting_duration_small
    assert global_state["voting_duration_medium"] == voting_duration_medium
    assert global_state["voting_duration_large"] == voting_duration_large
    assert global_state["voting_duration_xlarge"] == voting_duration_xlarge
    assert global_state["cool_down_duration"] == cool_down_duration
    assert global_state["quorum_small"] == quorum_small
    assert global_state["quorum_medium"] == quorum_medium
    assert global_state["quorum_large"] == quorum_large
    assert global_state["weighted_quorum_small"] == weighted_quorum_small
    assert global_state["weighted_quorum_medium"] == weighted_quorum_medium
    assert global_state["weighted_quorum_large"] == weighted_quorum_large