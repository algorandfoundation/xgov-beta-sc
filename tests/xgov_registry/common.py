from algokit_utils import LogicError
from algokit_utils.beta.account_manager import (
    AccountTransactionSigner,
    AddressAndSigner,
)
from algokit_utils.models import Account
from algosdk.encoding import decode_address, encode_address

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GlobalState,
    TypedGlobalState,
)
from smart_contracts.proposal.constants import (
    COMMITTEE_ID_LENGTH,
)
from smart_contracts.xgov_registry.config import (
    PROPOSER_BOX_MAP_PREFIX,
    REQUEST_BOX_MAP_PREFIX,
    XGOV_BOX_MAP_PREFIX,
)

LogicErrorType: type[LogicError] = LogicError

XGOV_FEE = 1_000_000
PROPOSER_FEE = 10_000_000
OPEN_PROPOSAL_FEE = 100_000_000
DAEMON_OPS_FUNDING_BPS = 1_000
PROPOSAL_COMMITMENT_BPS = 100
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

QUORUM_SMALL = 100
QUORUM_MEDIUM = 200
QURUM_LARGE = 300

WEIGHTED_QUORUM_SMALL = 200
WEIGHTED_QUORUM_MEDIUM = 300
WEIGHTED_QUORUM_LARGE = 400

COMMITTEE_ID = bytes(COMMITTEE_ID_LENGTH)
COMMITTEE_SIZE = 10
COMMITTEE_VOTES = 100

TREASURY_AMOUNT = 10_000_000

UNLIMITED_KYC_EXPIRATION = 2**64 - 1


def xgov_box_name(address: str) -> bytes:
    return XGOV_BOX_MAP_PREFIX + decode_address(address)  # type: ignore


def request_box_name(rid: int) -> bytes:
    return REQUEST_BOX_MAP_PREFIX + rid.to_bytes(8, "big")


def proposer_box_name(address: str) -> bytes:
    return PROPOSER_BOX_MAP_PREFIX + decode_address(address)  # type: ignore


def address_and_signer_from_account(acc: Account) -> AddressAndSigner:
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
    global_state: GlobalState,
    *,
    committee_id: bytes,
    committee_size: int,
    committee_votes: int,
) -> None:
    assert global_state.committee_id.as_bytes == committee_id
    assert global_state.committee_members == committee_size
    assert global_state.committee_votes == committee_votes


def assert_get_state(global_state: GlobalState, get_state: TypedGlobalState) -> None:
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
