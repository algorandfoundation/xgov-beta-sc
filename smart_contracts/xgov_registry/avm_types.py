import typing as t

from algopy import arc4

from ..common import abi_types as ptyp


class TypedGlobalState(arc4.Struct):
    paused_registry: arc4.Bool
    paused_proposals: arc4.Bool
    xgov_manager: arc4.Address
    xgov_payor: arc4.Address
    xgov_council: arc4.Address
    xgov_subscriber: arc4.Address
    kyc_provider: arc4.Address
    committee_manager: arc4.Address
    xgov_daemon: arc4.Address
    xgov_fee: arc4.UInt64
    proposer_fee: arc4.UInt64
    open_proposal_fee: arc4.UInt64
    daemon_ops_funding_bps: arc4.UInt64
    proposal_commitment_bps: arc4.UInt64
    min_requested_amount: arc4.UInt64
    max_requested_amount: arc4.StaticArray[arc4.UInt64, t.Literal[3]]
    discussion_duration: arc4.StaticArray[arc4.UInt64, t.Literal[4]]
    voting_duration: arc4.StaticArray[arc4.UInt64, t.Literal[4]]
    quorum: arc4.StaticArray[arc4.UInt64, t.Literal[3]]
    weighted_quorum: arc4.StaticArray[arc4.UInt64, t.Literal[3]]
    outstanding_funds: arc4.UInt64
    pending_proposals: arc4.UInt64
    committee_id: ptyp.Bytes32
    committee_members: arc4.UInt64
    committee_votes: arc4.UInt64


class XGovRegistryConfig(arc4.Struct):
    xgov_fee: arc4.UInt64
    proposer_fee: arc4.UInt64
    open_proposal_fee: arc4.UInt64
    daemon_ops_funding_bps: arc4.UInt64
    proposal_commitment_bps: arc4.UInt64
    min_requested_amount: arc4.UInt64
    max_requested_amount: arc4.StaticArray[arc4.UInt64, t.Literal[3]]
    discussion_duration: arc4.StaticArray[arc4.UInt64, t.Literal[4]]
    voting_duration: arc4.StaticArray[arc4.UInt64, t.Literal[4]]
    quorum: arc4.StaticArray[arc4.UInt64, t.Literal[3]]
    weighted_quorum: arc4.StaticArray[arc4.UInt64, t.Literal[3]]


class XGovSubscribeRequestBoxValue(arc4.Struct):
    xgov_addr: arc4.Address
    owner_addr: arc4.Address
    relation_type: arc4.UInt64


class ProposerBoxValue(arc4.Struct):
    active_proposal: arc4.Bool
    kyc_status: arc4.Bool
    kyc_expiring: arc4.UInt64


class XGovBoxValue(arc4.Struct):
    voting_address: arc4.Address
    voted_proposals: arc4.UInt64
    last_vote_timestamp: arc4.UInt64
    subscription_round: arc4.UInt64
