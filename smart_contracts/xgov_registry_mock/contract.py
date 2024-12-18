# pyright: reportMissingModuleSource=false
from algopy import (
    ARC4Contract,
    GlobalState,
    UInt64,
    arc4,
)

from smart_contracts.proposal.contract import Proposal

from ..common.types import CommitteeId
from ..xgov_registry import config as reg_cfg
from . import config as mock_cfg


class XgovRegistryMock(ARC4Contract):
    def __init__(self) -> None:
        self.proposal_commitment_bps = GlobalState(
            UInt64(mock_cfg.PROPOSAL_COMMITMENT_BPS),
            key=reg_cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS,
        )
        self.min_requested_amount = GlobalState(
            UInt64(mock_cfg.MIN_REQUESTED_AMOUNT),
            key=reg_cfg.GS_KEY_MIN_REQUESTED_AMOUNT,
        )
        self.max_requested_amount_small = GlobalState(
            UInt64(mock_cfg.MAX_REQUESTED_AMOUNT_SMALL),
            key=reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_SMALL,
        )
        self.max_requested_amount_medium = GlobalState(
            UInt64(mock_cfg.MAX_REQUESTED_AMOUNT_MEDIUM),
            key=reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM,
        )
        self.max_requested_amount_large = GlobalState(
            UInt64(mock_cfg.MAX_REQUESTED_AMOUNT_LARGE),
            key=reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_LARGE,
        )
        self.publishing_fee_bps = GlobalState(
            UInt64(mock_cfg.PUBLISHING_FEE_BPS),
            key=reg_cfg.GS_KEY_PROPOSAL_PUBLISHING_BPS,
        )
        self.discussion_duration_small = GlobalState(
            UInt64(mock_cfg.DISCUSSION_DURATION_SMALL),
            key=reg_cfg.GS_KEY_DISCUSSION_DURATION_SMALL,
        )
        self.discussion_duration_medium = GlobalState(
            UInt64(mock_cfg.DISCUSSION_DURATION_MEDIUM),
            key=reg_cfg.GS_KEY_DISCUSSION_DURATION_MEDIUM,
        )
        self.discussion_duration_large = GlobalState(
            UInt64(mock_cfg.DISCUSSION_DURATION_LARGE),
            key=reg_cfg.GS_KEY_DISCUSSION_DURATION_LARGE,
        )
        self.committee_publisher = GlobalState(
            arc4.Address(mock_cfg.COMMITTEE_PUBLISHER),
            key=reg_cfg.GS_KEY_COMMITTEE_PUBLISHER,
        )
        self.proposal_fee = GlobalState(
            UInt64(mock_cfg.PROPOSAL_FEE),
            key=reg_cfg.GS_KEY_PROPOSAL_FEE,
        )
        self.committee_id = GlobalState(
            CommitteeId.from_bytes(mock_cfg.COMMITTEE_ID),
            key=reg_cfg.GS_KEY_COMMITTEE_ID,
        )
        self.committee_members = GlobalState(
            UInt64(mock_cfg.COMMITTEE_MEMBERS),
            key=reg_cfg.GS_KEY_COMMITTEE_MEMBERS,
        )
        self.committee_votes = GlobalState(
            UInt64(mock_cfg.COMMITTEE_VOTES),
            key=reg_cfg.GS_KEY_COMMITTEE_VOTES,
        )

    @arc4.abimethod()
    def create_empty_proposal(
        self,
        proposer: arc4.Address,
    ) -> UInt64:
        """
        Create an empty proposal

        Args:
            proposer (arc4.Address): The proposer's address

        Returns:
            UInt64: The ID of the created proposal

        """
        res = arc4.arc4_create(
            Proposal,
            proposer,
        )

        return res.created_app.id

    @arc4.abimethod()
    def set_proposal_commitment_bps(self, commitment_bps: UInt64) -> None:
        """
        Set the proposal commitment in basis points

        Args:
            commitment_bps (UInt64): The commitment in basis points

        """
        self.proposal_commitment_bps.value = commitment_bps

    @arc4.abimethod()
    def set_min_requested_amount(self, min_requested_amount: UInt64) -> None:
        """
        Set the minimum requested amount

        Args:
            min_requested_amount (UInt64): The minimum requested amount

        """
        self.min_requested_amount.value = min_requested_amount

    @arc4.abimethod()
    def set_max_requested_amount_small(self, max_requested_amount: UInt64) -> None:
        """
        Set the maximum requested amount for small proposals

        Args:
            max_requested_amount (UInt64): The maximum requested amount

        """
        self.max_requested_amount_small.value = max_requested_amount

    @arc4.abimethod()
    def set_max_requested_amount_medium(self, max_requested_amount: UInt64) -> None:
        """
        Set the maximum requested amount for medium proposals

        Args:
            max_requested_amount (UInt64): The maximum requested amount

        """
        self.max_requested_amount_medium.value = max_requested_amount

    @arc4.abimethod()
    def set_max_requested_amount_large(self, max_requested_amount: UInt64) -> None:
        """
        Set the maximum requested amount for large proposals

        Args:
            max_requested_amount (UInt64): The maximum requested amount

        """
        self.max_requested_amount_large.value = max_requested_amount

    @arc4.abimethod()
    def set_publishing_fee(self, publishing_fee_bps: UInt64) -> None:
        """
        Set the publishing fee

        Args:
            publishing_fee_bps (UInt64): The publishing fee

        """
        self.publishing_fee_bps.value = publishing_fee_bps

    @arc4.abimethod()
    def set_discussion_duration_small(self, discussion_duration: UInt64) -> None:
        """
        Set the discussion duration for small proposals

        Args:
            discussion_duration (UInt64): The discussion duration

        """
        self.discussion_duration_small.value = discussion_duration

    @arc4.abimethod()
    def set_discussion_duration_medium(self, discussion_duration: UInt64) -> None:
        """
        Set the discussion duration for medium proposals

        Args:
            discussion_duration (UInt64): The discussion duration

        """
        self.discussion_duration_medium.value = discussion_duration

    @arc4.abimethod()
    def set_discussion_duration_large(self, discussion_duration: UInt64) -> None:
        """
        Set the discussion duration for large proposals

        Args:
            discussion_duration (UInt64): The discussion duration

        """
        self.discussion_duration_large.value = discussion_duration

    @arc4.abimethod()
    def set_committee_publisher(self, committee_publisher: arc4.Address) -> None:
        """
        Set the committee publisher

        Args:
            committee_publisher (arc4.Address): The committee publisher

        """
        self.committee_publisher.value = committee_publisher

    @arc4.abimethod()
    def set_proposal_fee(self, proposal_fee: UInt64) -> None:
        """
        Set the proposal fee

        Args:
            proposal_fee (UInt64): The proposal fee

        """
        self.proposal_fee.value = proposal_fee

    @arc4.abimethod()
    def set_committee_id(self, committee_id: CommitteeId) -> None:
        """
        Set the committee ID

        Args:
            committee_id (CommitteeId): The committee ID

        """
        self.committee_id.value = committee_id.copy()

    @arc4.abimethod()
    def clear_committee_id(self) -> None:
        """
        Clear the committee ID

        """
        self.committee_id.value = CommitteeId.from_bytes(mock_cfg.COMMITTEE_ID)

    @arc4.abimethod()
    def set_committee_members(self, committee_members: UInt64) -> None:
        """
        Set the number of committee members

        Args:
            committee_members (UInt64): The number of committee members

        """
        self.committee_members.value = committee_members

    @arc4.abimethod()
    def set_committee_votes(self, committee_votes: UInt64) -> None:
        """
        Set the number of committee votes

        Args:
            committee_votes (UInt64): The number of committee votes

        """
        self.committee_votes.value = committee_votes
