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

    @subroutine
    def algos_to_microalgos(self, algos: UInt64) -> UInt64:
        return algos * const.MICROALGOS_TO_ALGOS

    @subroutine
    def submit_authorization(self) -> bool:
        return (
            self.is_proposer()
            and self.is_kyc_verified()
            and self.status == enm.STATUS_EMPTY
        )

    @subroutine
    def submit_input_validation(
        self,
        title: String,
        cid: typ.Cid,
        funding_type: UInt64,
        requested_amount: UInt64,
    ) -> None:

        assert title.bytes.length <= const.TITLE_MAX_BYTES, err.WRONG_TITLE_LENGTH
        assert title != "", err.WRONG_TITLE_LENGTH
        assert (
            cid.length == const.CID_LENGTH
        ), err.WRONG_CID_LENGTH  # redundant, protected by type
        assert (
            funding_type == enm.FUNDING_PROACTIVE
            or funding_type == enm.FUNDING_RETROACTIVE
        ), err.WRONG_FUNDING_TYPE

        min_requested_algo_amount = self.get_min_requested_algo_amount()
        max_requested_algo_amount_large = self.get_max_requested_algo_amount_large()

        assert requested_amount >= self.algos_to_microalgos(
            min_requested_algo_amount
        ), err.WRONG_MIN_REQUESTED_AMOUNT
        assert requested_amount <= self.algos_to_microalgos(
            max_requested_algo_amount_large
        ), err.WRONG_MAX_REQUESTED_AMOUNT

    @subroutine
    def submit_payment_validation(
        self, payment: gtxn.PaymentTransaction, requested_amount: UInt64
    ) -> None:
        expected_lock_amount = requested_amount // 100

        assert payment.sender == self.proposer, err.WRONG_SENDER
        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        assert payment.amount == expected_lock_amount, err.WRONG_LOCKED_AMOUNT

    @subroutine
    def set_category(self, requested_amount: UInt64) -> None:
        max_requested_amount_small = self.get_max_requested_algo_amount_small()
        max_requested_amount_medium = self.get_max_requested_algo_amount_medium()

        if requested_amount <= self.algos_to_microalgos(max_requested_amount_small):
            self.category = UInt64(enm.CATEGORY_SMALL)
        elif requested_amount <= self.algos_to_microalgos(max_requested_amount_medium):
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
    def create(self, proposer: arc4.Address) -> None:
        # assert Global.caller_application_id != 0, err.UNAUTHORIZED  # Only callable by another contract

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

        assert self.submit_authorization(), err.UNAUTHORIZED

        self.submit_input_validation(title, cid, funding_type, requested_amount)
        self.submit_payment_validation(payment, requested_amount)

        self.title = title
        self.cid = cid.copy()
        self.set_category(requested_amount)
        self.funding_type = funding_type
        self.requested_amount = requested_amount
        self.locked_amount = requested_amount // 100
        self.submission_ts = Global.latest_timestamp
        self.status = UInt64(enm.STATUS_DRAFT)

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
    def get_min_requested_algo_amount(self) -> UInt64:
        return UInt64(const.MIN_REQUESTED_ALGO_AMOUNT)

    @subroutine
    def get_max_requested_algo_amount_small(self) -> UInt64:
        return UInt64(const.MAX_REQUESTED_ALGO_AMOUNT_SMALL)

    @subroutine
    def get_max_requested_algo_amount_medium(self) -> UInt64:
        return UInt64(const.MAX_REQUESTED_ALGO_AMOUNT_MEDIUM)

    @subroutine
    def get_max_requested_algo_amount_large(self) -> UInt64:
        return UInt64(const.MAX_REQUESTED_ALGO_AMOUNT_LARGE)

    # Stub subroutines end
    ####################################################################################################################
