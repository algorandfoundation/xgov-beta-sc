import typing as t

from algopy import (
    arc4,
    UInt64
)

class XGovRegistryConfig(arc4.Struct):
    xgov_min_balance: UInt64
    proposer_fee: UInt64
    proposal_fee: UInt64
    proposal_publishing_perc: UInt64
    proposal_commitment_perc: UInt64
    min_req_amount: UInt64
    max_req_amount: arc4.StaticArray[UInt64, t.Literal[3]]
    discussion_duration: arc4.StaticArray[UInt64, t.Literal[4]]
    voting_duration: arc4.StaticArray[UInt64, t.Literal[4]]
    cool_down_duration: UInt64
    quorum: arc4.StaticArray[UInt64, t.Literal[3]]
    weighted_quorum: arc4.StaticArray[UInt64, t.Literal[3]]


class XgovBoxValue(arc4.Struct):
    voting_addr: arc4.Address


class ProposerBoxValue(arc4.Struct):
    active_proposal: arc4.Bool
    kyc_status: arc4.Bool
    kyc_expiring: UInt64
