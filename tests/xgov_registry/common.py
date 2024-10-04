from typing import Type

from algokit_utils import LogicError
from algokit_utils.models import Account
from algokit_utils.beta.account_manager import (
    AddressAndSigner,
    AccountTransactionSigner
)
from smart_contracts.artifacts.xgov_registry.client import (
    GlobalState,
    TypedGlobalState
)
from algosdk.encoding import encode_address

logicErrorType: Type[LogicError] = LogicError

XGOV_MIN_BALANCE = 1_000_000
PROPOSER_FEE = 10_000_000
PROPOSAL_FEE = 100_000_000
PROPOSAL_PUBLISHING_BPS = 1_000
PROPOSAL_COMMITTMENT_BPS = 1_000
MIN_REQUESTED_AMOUNT = 1_000

MAX_REQUESTED_AMOUNT_SMALL = 100_000_000
MAX_REQUESTED_AMOUNT_MEDIUM = 1_000_000_000
MAX_REQUESTED_AMOUNT_LARGE = 10_000_000_000

DISCUSSION_DURATION_SMALL = 86400
DISCUSSION_DURATION_MEDIUM = 172800
DISCUSSION_DURATION_LARGE = 259200
DISCUSSION_DURATION_XLARGE = 345600

VOTING_DURATION_SMALL = 86400
VOTING_DURATION_MEDIUM = 172800
VOTING_DURATION_LARGE = 259200
VOTING_DURATION_XLARGE = 345600

COOL_DOWN_DURATION = 86400

QUORUM_SMALL = 100
QUORUM_MEDIUM = 200
QURUM_LARGE = 300

WEIGHTED_QUORUM_SMALL = 200
WEIGHTED_QUORUM_MEDIUM = 300
WEIGHTED_QUORUM_LARGE = 400

COMMITTEE_ID = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
COMMITTEE_SIZE = 10
COMMITTEE_VOTES = 100

def AddressAndSignerFromAccount(acc: Account) -> AddressAndSigner:
    signer = AccountTransactionSigner(acc.private_key)
    return AddressAndSigner(address=acc.address, signer=signer)

def assert_registry_global_state(
    global_state: GlobalState,
    *,
    manager_address: str,
) -> None:
    assert encode_address(global_state.xgov_manager.as_bytes) == manager_address  # type: ignore

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
    proposal_publishing_bps: int,
    proposal_commitment_bps: int,
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
    assert global_state.xgov_min_balance == xgov_min_balance
    assert global_state.proposal_publishing_bps == proposal_publishing_bps
    assert global_state.proposal_commitment_bps == proposal_commitment_bps
    assert global_state.proposer_fee == proposer_fee
    assert global_state.proposal_fee == proposal_fee
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
    assert global_state.cool_down_duration == cool_down_duration
    assert global_state.quorum_small == quorum_small
    assert global_state.quorum_medium == quorum_medium
    assert global_state.quorum_large == quorum_large
    assert global_state.weighted_quorum_small == weighted_quorum_small
    assert global_state.weighted_quorum_medium == weighted_quorum_medium
    assert global_state.weighted_quorum_large == weighted_quorum_large

def assert_get_state(
    global_state: GlobalState,
    get_state: TypedGlobalState
) -> None:
    assert global_state.xgov_min_balance == get_state.xgov_min_balance
    assert global_state.proposal_publishing_bps == get_state.proposal_publishing_bps
    assert global_state.proposal_commitment_bps == get_state.proposal_commitment_bps
    assert global_state.proposer_fee == get_state.proposer_fee
    assert global_state.proposal_fee == get_state.proposal_fee
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
    assert global_state.cool_down_duration == get_state.cool_down_duration
    assert global_state.quorum_small == get_state.quorum[0]
    assert global_state.quorum_medium == get_state.quorum[1]
    assert global_state.quorum_large == get_state.quorum[2]
    assert global_state.weighted_quorum_small == get_state.weighted_quorum[0]
    assert global_state.weighted_quorum_medium == get_state.weighted_quorum[1]
    assert global_state.weighted_quorum_large == get_state.weighted_quorum[2]