# pyright: reportMissingModuleSource=false
from algopy import (
    ARC4Contract,
    GlobalState,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    compile_contract,
)

import smart_contracts.errors.std_errors as err
from smart_contracts.proposal.contract import Proposal

from ..xgov_registry import config as reg_cfg
from . import config as mock_cfg


class XgovRegistryMock(
    ARC4Contract,
    state_totals=StateTotals(
        global_bytes=mock_cfg.GLOBAL_BYTES,
        global_uints=mock_cfg.GLOBAL_UINTS,
        local_bytes=mock_cfg.LOCAL_BYTES,
        local_uints=mock_cfg.LOCAL_UINTS,
    ),
):
    def __init__(self) -> None:
        # Preconditions
        assert (
            Txn.global_num_byte_slice == mock_cfg.GLOBAL_BYTES
        ), err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == mock_cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == mock_cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == mock_cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

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
            key=reg_cfg.GS_KEY_PUBLISHING_FEE_BPS,
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
        compiled = compile_contract(Proposal)
        res = arc4.arc4_create(
            Proposal,
            proposer,
            compiled=compiled,
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
