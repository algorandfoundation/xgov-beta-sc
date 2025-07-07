import typing

from algopy import arc4

# corresponds to COMMITTEE_ID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors
# which fails compilation.
Bytes32 = arc4.StaticArray[arc4.Byte, typing.Literal[32]]

Error = arc4.String


class VoterBox(arc4.Struct, kw_only=True):
    votes: arc4.UInt64  # Outstanding votes to be used as Approval or Rejection
    voted: arc4.Bool  # Whether the voter has voted


class ProposalTypedGlobalState(arc4.Struct):
    proposer: arc4.Address
    registry_app_id: arc4.UInt64
    title: arc4.String
    submission_ts: arc4.UInt64
    finalization_ts: arc4.UInt64
    vote_open_ts: arc4.UInt64
    status: arc4.UInt64
    decommissioned: arc4.Bool
    funding_category: arc4.UInt64
    focus: arc4.UInt8
    funding_type: arc4.UInt64
    requested_amount: arc4.UInt64
    locked_amount: arc4.UInt64
    committee_id: Bytes32
    committee_members: arc4.UInt64
    committee_votes: arc4.UInt64
    voted_members: arc4.UInt64
    approvals: arc4.UInt64
    rejections: arc4.UInt64
    nulls: arc4.UInt64


class CommitteeMember(arc4.Struct):
    address: arc4.Address
    voting_power: arc4.UInt64
