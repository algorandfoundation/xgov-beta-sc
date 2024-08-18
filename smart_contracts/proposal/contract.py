# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Global,
    StateTotals,
    String,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    subroutine,
)

import smart_contracts.errors.std_errors as err

from . import config as cfg
from . import constants as const
from . import enums as enm
from . import types as typ


class Proposal(
    ARC4Contract,
    state_totals=StateTotals(
        global_bytes=cfg.GLOBAL_BYTES,
        global_uints=cfg.GLOBAL_UINTS,
        local_bytes=cfg.LOCAL_BYTES,
        local_uints=cfg.LOCAL_UINTS,
    ),
):
    def __init__(self) -> None:
        # Preconditions
        assert Txn.global_num_byte_slice == cfg.GLOBAL_BYTES, err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

        self.committee_publisher = (
            arc4.Address()
        )  # TODO: remove after we have the registry SC

        self.proposer = arc4.Address()
        self.registry_app_id = UInt64()  # Registry App ID
        self.title = String()  # UTF-8 encoded, max 123 bytes
        self.cid = typ.Cid.from_bytes(
            b""
        )  # IPFS V1 CID, updated on each update of the Draft
        self.submission_ts = UInt64()  # Proposal finalization timestamp
        self.finalization_ts = UInt64()  # Proposal finalization timestamp
        self.status = UInt64(enm.STATUS_EMPTY)  # Enumerated status
        self.category = UInt64(
            enm.CATEGORY_NULL
        )  # Proposal category (small, medium, large)
        self.funding_type = UInt64(
            enm.FUNDING_NULL
        )  # Funding type (Proactive / Retroactive)
        self.requested_amount = UInt64()  # Requested amount in microAlgos
        self.locked_amount = (
            UInt64()
        )  # Locked amount in microAlgos, 1% of requested amount
        self.committee_id = typ.CommitteeId.from_bytes(b"")  # xGov Voting Committee ID
        self.committee_members = UInt64()  # xGov Voting Committee size
        self.committee_votes = UInt64()  # xGov Voting Committee total voting power
        self.voted_members = UInt64()  # xGov Voting Committee members who voted
        self.approvals = (
            UInt64()
        )  # Approval votes received by xGov Voting Committee members
        self.rejections = (
            UInt64()
        )  # Rejection votes received by xGov Voting Committee members

    # @subroutine
    # def finalize_check_authorization(self) -> None:
    #
    #     assert self.is_proposer(), err.UNAUTHORIZED
    #     assert self.status == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS
    #     assert self.is_kyc_verified(), err.KYC_NOT_VERIFIED
    #
    #     discussion_duration = Global.latest_timestamp - self.submission_ts
    #     minimum_discussion_duration = self.get_discussion_duration(self.category)
    #
    #     assert discussion_duration >= minimum_discussion_duration, err.TOO_EARLY

    @subroutine
    def drop_check_authorization(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
        assert self.status == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS

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
        assert self.status == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def submit_check_authorization(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
        assert self.is_kyc_verified(), err.KYC_NOT_VERIFIED
        assert self.status == enm.STATUS_EMPTY, err.WRONG_PROPOSAL_STATUS

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

        min_requested_amount = self.get_min_requested_amount()
        max_requested_amount_large = self.get_max_requested_amount_large()

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
            requested_amount, self.get_proposal_commitment_bps()
        )

    @subroutine
    def submit_payment_validation(
        self, payment: gtxn.PaymentTransaction, requested_amount: UInt64
    ) -> None:
        expected_lock_amount = self.get_expected_locked_amount(requested_amount)

        assert payment.sender == self.proposer, err.WRONG_SENDER
        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        assert payment.amount == expected_lock_amount, err.WRONG_LOCKED_AMOUNT

    @subroutine
    def set_category(self, requested_amount: UInt64) -> None:
        max_requested_amount_small = self.get_max_requested_amount_small()
        max_requested_amount_medium = self.get_max_requested_amount_medium()

        if requested_amount <= max_requested_amount_small:
            self.category = UInt64(enm.CATEGORY_SMALL)
        elif requested_amount <= max_requested_amount_medium:
            self.category = UInt64(enm.CATEGORY_MEDIUM)
        else:
            self.category = UInt64(enm.CATEGORY_LARGE)

    @subroutine
    def is_creator(self) -> bool:
        return Txn.sender == Global.creator_address

    @subroutine
    def is_proposer(self) -> bool:
        return Txn.sender == self.proposer

    @arc4.abimethod(create="require")
    def create(self, proposer: arc4.Address, committee_publisher: arc4.Address) -> None:
        """Create a new proposal.

        Args:
            proposer (arc4.Address): Address of the proposer
            committee_publisher (arc4.Address), temporary: Address of the committee publisher

        """
        # assert Global.caller_application_id != 0, err.UNAUTHORIZED  # Only callable by another contract

        self.committee_publisher = (
            committee_publisher  # TODO: remove after we have the registry SC
        )

        self.proposer = proposer
        self.registry_app_id = Global.caller_application_id

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

        self.title = title
        self.cid = cid.copy()
        self.set_category(requested_amount)
        self.funding_type = funding_type
        self.requested_amount = requested_amount
        self.locked_amount = self.get_expected_locked_amount(requested_amount)
        self.submission_ts = Global.latest_timestamp
        self.status = UInt64(enm.STATUS_DRAFT)

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

        self.title = title
        self.cid = cid.copy()

    @arc4.abimethod()
    def drop_proposal(self) -> None:
        """Drop the proposal.

        Raises:
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT

        """
        self.drop_check_authorization()

        itxn.Payment(
            receiver=self.proposer.native,
            amount=self.locked_amount,
            fee=UInt64(0),  # enforces the proposer to pay the fee
        ).submit()

        #  Clear the proposal data TODO: check if this can be in a struct and clear the struct
        self.title = String()
        self.cid = typ.Cid.from_bytes(b"")
        self.category = UInt64(enm.CATEGORY_NULL)
        self.funding_type = UInt64(enm.FUNDING_NULL)
        self.requested_amount = UInt64(0)
        self.locked_amount = UInt64(0)
        self.submission_ts = UInt64(0)
        self.status = UInt64(enm.STATUS_EMPTY)

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
    #     self.status = UInt64(enm.STATUS_FINAL)
    #     self.finalization_ts = Global.latest_timestamp
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
    # def get_config_from_registry(self, registry_app_id: UInt64) -> typ.XGovRegistryConfig:
    #     return typ.XGovRegistryConfig(
    #         min_requested_amount=arc4.UInt64(10_000),
    #         max_requested_amount_small=arc4.UInt64(50_000),
    #         max_requested_amount_medium=arc4.UInt64(250_000),
    #         max_requested_amount_large=arc4.UInt64(500_000),
    #         discussion_duration_small=arc4.UInt64(1),
    #         discussion_duration_medium=arc4.UInt64(2),
    #         discussion_duration_large=arc4.UInt64(3),
    #     )
    @subroutine
    def get_min_requested_amount(self) -> UInt64:
        return UInt64(const.MIN_REQUESTED_AMOUNT)

    @subroutine
    def get_max_requested_amount_small(self) -> UInt64:
        return UInt64(const.MAX_REQUESTED_AMOUNT_SMALL)

    @subroutine
    def get_max_requested_amount_medium(self) -> UInt64:
        return UInt64(const.MAX_REQUESTED_AMOUNT_MEDIUM)

    @subroutine
    def get_max_requested_amount_large(self) -> UInt64:
        return UInt64(const.MAX_REQUESTED_AMOUNT_LARGE)

    @subroutine
    def get_proposal_commitment_bps(self) -> UInt64:
        return UInt64(const.PROPOSAL_COMMITMENT_BPS)

    @subroutine
    def get_committee_publisher_address(self) -> arc4.Address:
        return self.committee_publisher

    @subroutine
    def get_publishing_fee(self) -> UInt64:
        return UInt64(const.PUBLISHING_FEE)

    @subroutine
    def get_discussion_duration(self, category: UInt64) -> UInt64:
        if category == enm.CATEGORY_SMALL:
            return UInt64(const.DISCUSSION_DURATION_SMALL)
        elif category == enm.CATEGORY_MEDIUM:
            return UInt64(const.DISCUSSION_DURATION_MEDIUM)
        else:
            return UInt64(const.DISCUSSION_DURATION_LARGE)

    # Stub subroutines end
    ####################################################################################################################
