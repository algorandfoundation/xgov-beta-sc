import typing as t

from algopy import Account, FixedArray, String, Struct, UInt64, arc4

# corresponds to COMMITTEE_ID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors
# which fails compilation.
Bytes32 = arc4.StaticArray[arc4.Byte, t.Literal[32]]
TimeStamp: t.TypeAlias = UInt64
MicroAlgo: t.TypeAlias = UInt64
Error: t.TypeAlias = String


class ProposalTypedGlobalState(Struct, kw_only=True):
    proposer: Account
    registry_app_id: UInt64
    title: String
    open_ts: TimeStamp
    submission_ts: TimeStamp
    vote_open_ts: TimeStamp
    status: UInt64
    finalized: bool
    funding_category: UInt64
    focus: arc4.UInt8
    funding_type: UInt64
    requested_amount: MicroAlgo
    locked_amount: MicroAlgo
    committee_id: Bytes32
    committee_members: UInt64
    committee_votes: UInt64
    voted_members: UInt64
    boycotted_members: UInt64
    approvals: UInt64
    rejections: UInt64
    nulls: UInt64


class CommitteeMember(Struct, kw_only=True):
    address: Account
    voting_power: UInt64


Empty = arc4.StaticArray[arc4.Byte, t.Literal[0]]


class CouncilVote(Struct, kw_only=True):
    address: Account
    block: bool


CouncilVotingBox = arc4.DynamicArray[CouncilVote]


class TypedGlobalState(Struct, kw_only=True):
    paused_registry: bool
    paused_proposals: bool
    xgov_manager: Account
    xgov_payor: Account
    xgov_council: Account
    xgov_subscriber: Account
    kyc_provider: Account
    committee_manager: Account
    xgov_daemon: Account
    xgov_fee: MicroAlgo
    proposer_fee: MicroAlgo
    open_proposal_fee: MicroAlgo
    daemon_ops_funding_bps: UInt64
    proposal_commitment_bps: UInt64
    min_requested_amount: MicroAlgo
    max_requested_amount: FixedArray[MicroAlgo, t.Literal[3]]
    discussion_duration: FixedArray[UInt64, t.Literal[4]]
    voting_duration: FixedArray[UInt64, t.Literal[4]]
    quorum: FixedArray[UInt64, t.Literal[3]]
    weighted_quorum: FixedArray[UInt64, t.Literal[3]]
    outstanding_funds: MicroAlgo
    pending_proposals: UInt64
    committee_id: Bytes32
    committee_members: UInt64
    committee_votes: UInt64
    absence_tolerance: UInt64
    governance_period: UInt64
    committee_grace_period: UInt64
    committee_last_anchor: UInt64


class XGovRegistryConfig(Struct, kw_only=True):
    xgov_fee: MicroAlgo
    proposer_fee: MicroAlgo
    open_proposal_fee: MicroAlgo
    daemon_ops_funding_bps: UInt64
    proposal_commitment_bps: UInt64
    min_requested_amount: MicroAlgo
    max_requested_amount: FixedArray[MicroAlgo, t.Literal[3]]
    discussion_duration: FixedArray[UInt64, t.Literal[4]]
    voting_duration: FixedArray[UInt64, t.Literal[4]]
    quorum: FixedArray[UInt64, t.Literal[3]]
    weighted_quorum: FixedArray[UInt64, t.Literal[3]]
    absence_tolerance: UInt64
    governance_period: UInt64
    committee_grace_period: UInt64


class XGovSubscribeRequestBoxValue(Struct, kw_only=True):
    xgov_addr: Account
    owner_addr: Account
    relation_type: UInt64


class ProposerBoxValue(Struct, kw_only=True):
    active_proposal: bool
    kyc_status: bool
    kyc_expiring: UInt64


class XGovBoxValue(Struct, kw_only=True):
    voting_address: Account
    tolerated_absences: UInt64
    unsubscribed_round: UInt64
    subscription_round: UInt64


class VotingState(Struct, kw_only=True):
    """The voting state of the Proposal"""

    quorum_voters: arc4.UInt32
    weighted_quorum_votes: arc4.UInt32
    total_voters: arc4.UInt32
    total_boycott: arc4.UInt32
    total_approvals: arc4.UInt32
    total_rejections: arc4.UInt32
    total_nulls: arc4.UInt32
    quorum_reached: bool
    weighted_quorum_reached: bool
    majority_approved: bool
    plebiscite: bool


# ARC-28 xGov Registry Events


class XGovSubscribed(arc4.Struct, kw_only=True):
    """An xGov subscribed (either through self-onboarding or managed onboarding)"""

    xgov: Account
    delegate: Account


class XGovUnsubscribed(arc4.Struct, kw_only=True):
    """An xGov unsubscribed (either through self-onboarding or managed onboarding)"""

    xgov: Account


class ProposerSubscribed(arc4.Struct, kw_only=True):
    """A Proposer subscribed"""

    proposer: Account


class ProposerKYC(arc4.Struct, kw_only=True):
    """A Proposer KYC status update"""

    proposer: Account
    valid_kyc: bool


class NewCommittee(arc4.Struct, kw_only=True):
    """A new xGov Committee has been elected"""

    committee_id: Bytes32
    size: arc4.UInt32
    votes: arc4.UInt32


class NewProposal(arc4.Struct, kw_only=True):
    """A new Proposal has been opened"""

    proposal_id: UInt64
    proposer: Account


# ARC-28 Proposal Events


class Opened(arc4.Struct, kw_only=True):
    """The Proposal has been opened"""

    funding_type: arc4.UInt8
    requested_amount: UInt64
    category: arc4.UInt8


class Submitted(arc4.Struct, kw_only=True):
    """The Proposal has been submitted for voting"""

    vote_opening: TimeStamp
    vote_closing: TimeStamp
    quorum_voters: arc4.UInt32
    weighted_quorum_votes: arc4.UInt32


class Vote(arc4.Struct, kw_only=True):
    """A vote has been cast on the Proposal"""

    xgov: arc4.Address
    approvals: arc4.UInt32
    rejections: arc4.UInt32
    nulls: arc4.UInt32
    boycotted: bool
    total_voters: arc4.UInt32
    total_boycott: arc4.UInt32
    total_approvals: arc4.UInt32
    total_rejections: arc4.UInt32
    total_nulls: arc4.UInt32


class Scrutiny(arc4.Struct, kw_only=True):
    """The vote has been scrutinized"""

    approved: bool
    plebiscite: bool


class Review(arc4.Struct, kw_only=True):
    """The xGov Council has reviewed the Proposal"""

    veto: bool
