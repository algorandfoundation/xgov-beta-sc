import typing

from algopy import arc4

# corresponds to CID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors which
# fails compilation.
Cid = arc4.StaticArray[arc4.Byte, typing.Literal[36]]

Error = arc4.String


class VoterBox(arc4.Struct, kw_only=True):
    votes: arc4.UInt64  # Outstanding votes to be used as Approval or Rejection
    voted: arc4.Bool  # Whether the voter has voted


class ProposalTypedGlobalState(arc4.Struct):
    proposer: arc4.Address
    registry_app_id: arc4.UInt64
    title: arc4.String
    cid: Cid
    submission_ts: arc4.UInt64
    finalization_ts: arc4.UInt64
    vote_open_ts: arc4.UInt64
    status: arc4.UInt64
    funding_category: arc4.UInt64
    focus: arc4.UInt8
    funding_type: arc4.UInt64
    requested_amount: arc4.UInt64
    locked_amount: arc4.UInt64
    committee_id: Cid
    committee_members: arc4.UInt64
    committee_votes: arc4.UInt64
    voted_members: arc4.UInt64
    approvals: arc4.UInt64
    rejections: arc4.UInt64
    nulls: arc4.UInt64
    cool_down_start_ts: arc4.UInt64
