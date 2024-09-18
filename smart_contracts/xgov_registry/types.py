import typing as t

from algopy import arc4


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
