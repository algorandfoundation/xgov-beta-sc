# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Bytes,
    Global,
    GlobalState,
    StateTotals,
    String,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    subroutine,
)
from algopy.op import AppGlobal

import smart_contracts.errors.std_errors as err

from ..xgov_registry import config as reg_cfg
from . import config as prop_cfg
from . import constants as const
from . import enums as enm
from . import types as typ


class Proposal(
    ARC4Contract,
    state_totals=StateTotals(
        global_bytes=prop_cfg.GLOBAL_BYTES,
        global_uints=prop_cfg.GLOBAL_UINTS,
        local_bytes=prop_cfg.LOCAL_BYTES,
        local_uints=prop_cfg.LOCAL_UINTS,
    ),
):
    def __init__(self) -> None:
        # Preconditions
        assert (
            Txn.global_num_byte_slice == prop_cfg.GLOBAL_BYTES
        ), err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == prop_cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == prop_cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == prop_cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

        self.proposer = GlobalState(
            arc4.Address(),
            key=prop_cfg.GS_KEY_PROPOSER,
        )
        self.registry_app_id = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_REGISTRY_APP_ID,
        )
        self.title = GlobalState(
            String(),
            key=prop_cfg.GS_KEY_TITLE,
        )
        self.cid = GlobalState(
            typ.Cid.from_bytes(b""),
            key=prop_cfg.GS_KEY_CID,
        )
        self.submission_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_SUBMISSION_TS,
        )
        self.finalization_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_FINALIZATION_TS,
        )
        self.status = GlobalState(
            UInt64(enm.STATUS_EMPTY),
            key=prop_cfg.GS_KEY_STATUS,
        )
        self.category = GlobalState(
            UInt64(enm.CATEGORY_NULL),
            key=prop_cfg.GS_KEY_CATEGORY,
        )
        self.funding_type = GlobalState(
            UInt64(enm.FUNDING_NULL),
            key=prop_cfg.GS_KEY_FUNDING_TYPE,
        )
        self.requested_amount = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_REQUESTED_AMOUNT,
        )
        self.locked_amount = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_LOCKED_AMOUNT,
        )
        self.committee_id = GlobalState(
            typ.CommitteeId.from_bytes(b""),
            key=prop_cfg.GS_KEY_COMMITTEE_ID,
        )
        self.committee_members = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_COMMITTEE_MEMBERS,
        )
        self.committee_votes = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_COMMITTEE_VOTES,
        )
        self.voted_members = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_VOTED_MEMBERS,
        )
        self.approvals = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_APPROVALS,
        )
        self.rejections = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_REJECTIONS,
        )

    # @subroutine
    # def finalize_check_authorization(self) -> None:
    #
    #     assert self.is_proposer(), err.UNAUTHORIZED
    #     assert self.status.value == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS
    #     assert self.is_kyc_verified(), err.KYC_NOT_VERIFIED
    #
    #     discussion_duration = Global.latest_timestamp - self.submission_ts.value
    #     minimum_discussion_duration = self.get_discussion_duration(self.category.value)
    #
    #     assert discussion_duration >= minimum_discussion_duration, err.TOO_EARLY

    @subroutine
    def drop_check_authorization(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
        assert self.status.value == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def updateable_input_validation(self, title: String, cid: typ.Cid) -> None:
        assert title.bytes.length <= const.TITLE_MAX_BYTES, err.WRONG_TITLE_LENGTH
        assert title != "", err.WRONG_TITLE_LENGTH
        assert (
            cid.length == const.CID_LENGTH
        ), err.WRONG_CID_LENGTH  # redundant, protected by type

    @subroutine
    def update_check_authorization(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
        assert self.is_kyc_verified(), err.KYC_NOT_VERIFIED
        assert self.status.value == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def submit_check_authorization(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
        assert self.is_kyc_verified(), err.KYC_NOT_VERIFIED
        assert self.status.value == enm.STATUS_EMPTY, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def submit_input_validation(
        self,
        title: String,
        cid: typ.Cid,
        funding_type: UInt64,
        requested_amount: UInt64,
    ) -> None:

        self.updateable_input_validation(title, cid)

        assert (
            funding_type == enm.FUNDING_PROACTIVE
            or funding_type == enm.FUNDING_RETROACTIVE
        ), err.WRONG_FUNDING_TYPE

        min_requested_amount = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MIN_REQUESTED_AMOUNT)
        )
        max_requested_amount_large = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_LARGE)
        )

        assert requested_amount >= min_requested_amount, err.WRONG_MIN_REQUESTED_AMOUNT
        assert (
            requested_amount <= max_requested_amount_large
        ), err.WRONG_MAX_REQUESTED_AMOUNT

    @subroutine
    def relative_to_absolute_amount(
        self, amount: UInt64, fraction_in_bps: UInt64
    ) -> UInt64:
        return amount * fraction_in_bps // const.BPS

    @subroutine
    def get_expected_locked_amount(self, requested_amount: UInt64) -> UInt64:
        return self.relative_to_absolute_amount(
            requested_amount,
            self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS)
            ),
        )

    @subroutine
    def submit_payment_validation(
        self, payment: gtxn.PaymentTransaction, requested_amount: UInt64
    ) -> None:
        expected_lock_amount = self.get_expected_locked_amount(requested_amount)

        assert payment.sender == self.proposer.value, err.WRONG_SENDER
        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        assert payment.amount == expected_lock_amount, err.WRONG_LOCKED_AMOUNT

    @subroutine
    def set_category(self, requested_amount: UInt64) -> None:
        max_requested_amount_small = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_SMALL)
        )
        max_requested_amount_medium = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM)
        )

        if requested_amount <= max_requested_amount_small:
            self.category.value = UInt64(enm.CATEGORY_SMALL)
        elif requested_amount <= max_requested_amount_medium:
            self.category.value = UInt64(enm.CATEGORY_MEDIUM)
        else:
            self.category.value = UInt64(enm.CATEGORY_LARGE)

    @subroutine
    def get_uint_from_registry_config(self, global_state_key: Bytes) -> UInt64:
        value, exists = AppGlobal.get_ex_uint64(
            self.registry_app_id.value, global_state_key
        )
        assert exists, err.MISSING_CONFIG
        return value

    @subroutine
    def get_bytes_from_registry_config(self, global_state_key: Bytes) -> Bytes:
        value, exists = AppGlobal.get_ex_bytes(
            self.registry_app_id.value, global_state_key
        )
        assert exists, err.MISSING_CONFIG
        return value

    @subroutine
    def is_creator(self) -> bool:
        return Txn.sender == Global.creator_address

    @subroutine
    def is_proposer(self) -> bool:
        return Txn.sender == self.proposer.value

    @arc4.abimethod(create="require")
    def create(self, proposer: arc4.Address) -> None:
        """Create a new proposal.

        Args:
            proposer (arc4.Address): Address of the proposer
        """
        assert (
            Global.caller_application_id != 0
        ), err.UNAUTHORIZED  # Only callable by another contract

        self.proposer.value = proposer
        self.registry_app_id.value = Global.caller_application_id

    @arc4.abimethod()
    def submit_proposal(
        self,
        payment: gtxn.PaymentTransaction,
        title: String,
        cid: typ.Cid,
        funding_type: UInt64,
        requested_amount: UInt64,
    ) -> None:
        """Submit the first draft of the proposal.

        Args:
            payment (gtxn.PaymentTransaction): Commitment payment transaction from the proposer to the contract
            title (String): Proposal title, max TITLE_MAX_BYTES bytes
            cid (typ.Cid): IPFS V1 CID
            funding_type (UInt64): Funding type (Proactive / Retroactive)
            requested_amount (UInt64): Requested amount in microAlgos

        Raises:
            err.UNAUTHORIZED: If the sender is not the proposer
            err.KYC_NOT_VERIFIED: If the proposer's KYC is not verified
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_EMPTY
            err.WRONG_TITLE_LENGTH: If the title length is not within the limits
            err.WRONG_CID_LENGTH: If the CID length is not equal to CID_LENGTH
            err.WRONG_FUNDING_TYPE: If the funding type is not FUNDING_PROACTIVE or FUNDING_RETROACTIVE
            err.WRONG_MIN_REQUESTED_AMOUNT: If the requested amount is less than the minimum requested amount
            err.WRONG_MAX_REQUESTED_AMOUNT: If the requested amount is more than the maximum requested amount
            err.WRONG_SENDER: If the sender of the payment transaction is not the proposer
            err.WRONG_RECEIVER: If the receiver of the payment transaction is not the current application address
            err.WRONG_LOCKED_AMOUNT: If the amount in the payment transaction is not equal to the expected locked amount

        """
        self.submit_check_authorization()

        self.submit_input_validation(title, cid, funding_type, requested_amount)
        self.submit_payment_validation(payment, requested_amount)

        self.title.value = title
        self.cid.value = cid.copy()
        self.set_category(requested_amount)
        self.funding_type.value = funding_type
        self.requested_amount.value = requested_amount
        self.locked_amount.value = self.get_expected_locked_amount(requested_amount)
        self.submission_ts.value = Global.latest_timestamp
        self.status.value = UInt64(enm.STATUS_DRAFT)

    @arc4.abimethod()
    def update_proposal(self, title: String, cid: typ.Cid) -> None:
        """Update the proposal.

        Args:
            title (String): Proposal title, max TITLE_MAX_BYTES bytes
            cid (typ.Cid): IPFS V1 CID

        Raises:
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT
            err.WRONG_TITLE_LENGTH: If the title length is not within the limits
            err.WRONG_CID_LENGTH: If the CID length is not equal to CID_LENGTH

        """
        self.update_check_authorization()

        self.updateable_input_validation(title, cid)

        self.title.value = title
        self.cid.value = cid.copy()

    @arc4.abimethod()
    def drop_proposal(self) -> None:
        """Drop the proposal.

        Raises:
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT

        """
        self.drop_check_authorization()

        itxn.Payment(
            receiver=self.proposer.value.native,
            amount=self.locked_amount.value,
            fee=UInt64(0),  # enforces the proposer to pay the fee
        ).submit()

        #  Clear the proposal data TODO: check if this can be in a struct and clear the struct
        self.title.value = String()
        self.cid.value = typ.Cid.from_bytes(b"")
        self.category.value = UInt64(enm.CATEGORY_NULL)
        self.funding_type.value = UInt64(enm.FUNDING_NULL)
        self.requested_amount.value = UInt64(0)
        self.locked_amount.value = UInt64(0)
        self.submission_ts.value = UInt64(0)
        self.status.value = UInt64(enm.STATUS_EMPTY)

    # @arc4.abimethod()
    # def finalize_proposal(self) -> None:
    #     """Finalize the proposal.
    #
    #     Raises:
    #         err.UNAUTHORIZED: If the sender is not the proposer
    #         err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT
    #
    #     """
    #     self.finalize_check_authorization()
    #
    #     self.status.value = UInt64(enm.STATUS_FINAL)
    #     self.finalization_ts.value = Global.latest_timestamp
    #
    #     itxn.Payment(
    #         receiver=self.get_committee_publisher_address().native,
    #         amount=self.get_publishing_fee(),
    #         fee=UInt64(0),  # enforces the proposer to pay the fee
    #     ).submit()

    ####################################################################################################################
    # Stub subroutines
    # these subroutines are placeholders for the actual implementation
    @subroutine
    def is_kyc_verified(self) -> bool:
        return True

    # @subroutine
    # def get_committee_publisher_address(self) -> arc4.Address:
    #     return self.committee_publisher

    # Stub subroutines end
    ####################################################################################################################
