import typing
import typing as t

from algopy import arc4

# corresponds to COMMITTEE_ID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors
# which fails compilation.
Bytes32 = arc4.StaticArray[arc4.Byte, typing.Literal[32]]

Error = arc4.String


class ProposalTypedGlobalState(arc4.Struct):
    proposer: arc4.Address
    registry_app_id: arc4.UInt64
    title: arc4.String
    open_ts: arc4.UInt64
    submission_ts: arc4.UInt64
    vote_open_ts: arc4.UInt64
    status: arc4.UInt64
    finalized: arc4.Bool
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


Empty = arc4.StaticArray[arc4.Byte, typing.Literal[0]]


class CouncilVote(arc4.Struct):
    address: arc4.Address
    block: arc4.Bool


CouncilVotingBox = arc4.DynamicArray[CouncilVote]


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
    committee_id: Bytes32
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
    voted_proposals: arc4.UInt64  # Capped presence buffer for absenteeism
    last_vote_timestamp: arc4.UInt64
    subscription_round: arc4.UInt64


class VotingState(arc4.Struct, kw_only=True):
    """The voting state of the Proposal"""

    quorum_voters: arc4.UInt32
    weighted_quorum_votes: arc4.UInt32
    total_voters: arc4.UInt32
    total_approvals: arc4.UInt32
    total_rejections: arc4.UInt32
    total_nulls: arc4.UInt32
    quorum_reached: arc4.Bool
    weighted_quorum_reached: arc4.Bool
    majority_approved: arc4.Bool
    plebiscite: arc4.Bool


# ARC-28 xGov Registry Events


class XGovSubscribed(arc4.Struct, kw_only=True):
    """An xGov subscribed (either through self-onboarding or managed onboarding)"""

    xgov: arc4.Address
    delegate: arc4.Address


class XGovUnsubscribed(arc4.Struct, kw_only=True):
    """An xGov unsubscribed (either through self-onboarding or managed onboarding)"""

    xgov: arc4.Address


class ProposerSubscribed(arc4.Struct, kw_only=True):
    """A Proposer subscribed"""

    proposer: arc4.Address


class ProposerKYC(arc4.Struct, kw_only=True):
    """A Proposer KYC status update"""

    proposer: arc4.Address
    valid_kyc: arc4.Bool


class NewCommittee(arc4.Struct, kw_only=True):
    """A new xGov Committee has been elected"""

    committee_id: Bytes32
    size: arc4.UInt32
    votes: arc4.UInt32


class NewProposal(arc4.Struct, kw_only=True):
    """A new Proposal has been opened"""

    proposal_id: arc4.UInt64
    proposer: arc4.Address


# ARC-28 Proposal Events


class Opened(arc4.Struct, kw_only=True):
    """The Proposal has been opened"""

    funding_type: arc4.UInt8
    requested_amount: arc4.UInt64
    category: arc4.UInt8


class Submitted(arc4.Struct, kw_only=True):
    """The Proposal has been submitted for voting"""

    vote_opening: arc4.UInt64
    vote_closing: arc4.UInt64
    quorum_voters: arc4.UInt32
    weighted_quorum_votes: arc4.UInt32


class Vote(arc4.Struct, kw_only=True):
    """A vote has been cast on the Proposal"""

    xgov: arc4.Address
    total_voters: arc4.UInt32
    total_approvals: arc4.UInt32
    total_rejections: arc4.UInt32
    total_nulls: arc4.UInt32


class Scrutiny(arc4.Struct, kw_only=True):
    """The vote has been scrutinized"""

    approved: arc4.Bool
    plebiscite: arc4.Bool


class Review(arc4.Struct, kw_only=True):
    """The xGov Council has reviewed the Proposal"""

    veto: arc4.Bool
