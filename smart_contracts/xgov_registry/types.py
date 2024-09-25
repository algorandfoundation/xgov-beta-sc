import typing as t

from algopy import arc4

class TypedGlobalState(arc4.Struct):
    xgov_manager: arc4.Address
    xgov_payor: arc4.Address
    kyc_provider: arc4.Address
    committee_manager: arc4.Address
    committee_publisher: arc4.Address
    xgov_min_balance: arc4.UInt64
    proposer_fee: arc4.UInt64
    proposal_fee: arc4.UInt64
    proposal_publishing_bps: arc4.UInt64
    proposal_commitment_bps: arc4.UInt64
    min_requested_amount: arc4.UInt64
    max_requested_amount_small: arc4.UInt64
    max_requested_amount_medium: arc4.UInt64
    max_requested_amount_large: arc4.UInt64
    discussion_duration_small: arc4.UInt64
    discussion_duration_medium: arc4.UInt64
    discussion_duration_large: arc4.UInt64
    discussion_duration_xlarge: arc4.UInt64
    voting_duration_small: arc4.UInt64
    voting_duration_medium: arc4.UInt64
    voting_duration_large: arc4.UInt64
    voting_duration_xlarge: arc4.UInt64
    cool_down_duration: arc4.UInt64
    quorum_small: arc4.UInt64
    quorum_medium: arc4.UInt64
    quorum_large: arc4.UInt64
    weighted_quorum_small: arc4.UInt64
    weighted_quorum_medium: arc4.UInt64
    weighted_quorum_large: arc4.UInt64
    outstanding_funds: arc4.UInt64
    pending_proposals: arc4.UInt64
    committee_id: arc4.StaticArray[arc4.Byte, t.Literal[32]]
    committee_members: arc4.UInt64
    committee_votes: arc4.UInt64


class XGovRegistryConfig(arc4.Struct):
    xgov_min_balance: arc4.UInt64
    proposer_fee: arc4.UInt64
    proposal_fee: arc4.UInt64
    proposal_publishing_perc: arc4.UInt64
    proposal_commitment_perc: arc4.UInt64
    min_req_amount: arc4.UInt64
    max_req_amount: arc4.StaticArray[arc4.UInt64, t.Literal[3]]
    discussion_duration: arc4.StaticArray[arc4.UInt64, t.Literal[4]]
    voting_duration: arc4.StaticArray[arc4.UInt64, t.Literal[4]]
    cool_down_duration: arc4.UInt64
    quorum: arc4.StaticArray[arc4.UInt64, t.Literal[3]]
    weighted_quorum: arc4.StaticArray[arc4.UInt64, t.Literal[3]]


class ProposerBoxValue(arc4.Struct):
    active_proposal: arc4.Bool
    kyc_status: arc4.Bool
    kyc_expiring: arc4.UInt64
