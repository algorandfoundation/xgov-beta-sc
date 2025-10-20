# pyright: reportMissingModuleSource=false

from algopy import (
    Account,
    Application,
    ARC4Contract,
    Box,
    BoxMap,
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
    urange,
)
from algopy.op import AppGlobal, GTxn

import smart_contracts.errors.std_errors as err
from smart_contracts.common import abi_types as typ

from ..common.abi_types import CommitteeMember
from ..xgov_registry import config as reg_cfg
from . import config as prop_cfg
from . import constants as const
from . import enums as enm


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

        # Global Variables
        self.proposer = GlobalState(
            Account(),
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
        self.open_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_OPEN_TS,
        )
        self.submission_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_SUBMISSION_TS,
        )
        self.vote_open_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_VOTE_OPEN_TS,
        )
        self.status = GlobalState(
            UInt64(enm.STATUS_EMPTY),
            key=prop_cfg.GS_KEY_STATUS,
        )
        self.finalized = GlobalState(
            False,  # noqa: FBT003
            key=prop_cfg.GS_KEY_FINALIZED,
        )
        self.funding_category = GlobalState(
            UInt64(enm.FUNDING_CATEGORY_NULL),
            key=prop_cfg.GS_KEY_FUNDING_CATEGORY,
        )
        self.focus = GlobalState(
            UInt64(enm.FOCUS_NULL),
            key=prop_cfg.GS_KEY_FOCUS,
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
            typ.Bytes32.from_bytes(b""),
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
        self.nulls = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_NULLS,
        )
        self.voters_count = UInt64(0)
        self.assigned_votes = UInt64(0)
        self.metadata_uploaded = False

        # Boxes
        self.voters = BoxMap(
            Account, typ.VoterBox, key_prefix=prop_cfg.VOTER_BOX_KEY_PREFIX
        )
        self.metadata = Box(
            Bytes, key=prop_cfg.METADATA_BOX_KEY,
        )

    @subroutine
    def is_voting_open(self) -> tuple[bool, typ.Error]:
        voting_duration = Global.latest_timestamp - self.vote_open_ts.value
        maximum_voting_duration, error = self.get_voting_duration(
            self.funding_category.value
        )
        if error != typ.Error(""):
            return False, error

        return voting_duration <= maximum_voting_duration, typ.Error("")

    @subroutine
    def review_check_authorization(self) -> None:
        assert self.is_council(), err.UNAUTHORIZED
        assert self.status.value == enm.STATUS_APPROVED, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def fund_check_authorization(self) -> typ.Error:
        assert self.is_registry_call(), err.UNAUTHORIZED
        if self.status.value != enm.STATUS_REVIEWED:
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_PROPOSAL_STATUS)

        return typ.Error("")

    @subroutine
    def unassign_voters_check_authorization(self) -> None:
        if self.status.value == enm.STATUS_SUBMITTED:
            assert self.is_xgov_daemon(), err.UNAUTHORIZED
        else:
            assert (
                self.status.value == enm.STATUS_FUNDED
                or self.status.value == enm.STATUS_BLOCKED
                or self.status.value == enm.STATUS_REJECTED
            ) and not self.finalized.value, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def finalize_check_authorization(self) -> typ.Error:
        assert self.is_registry_call(), err.UNAUTHORIZED

        if self.finalized.value or (
            self.status.value != enm.STATUS_EMPTY
            and self.status.value != enm.STATUS_DRAFT
            and self.status.value != enm.STATUS_FUNDED
            and self.status.value != enm.STATUS_BLOCKED
            and self.status.value != enm.STATUS_REJECTED
        ):
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_PROPOSAL_STATUS)

        return typ.Error("")

    @subroutine
    def delete_check_authorization(self) -> None:
        assert self.is_xgov_daemon(), err.UNAUTHORIZED
        assert self.finalized.value, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def vote_check_authorization(self) -> typ.Error:
        assert self.is_registry_call(), err.UNAUTHORIZED

        if self.status.value != enm.STATUS_VOTING:
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_PROPOSAL_STATUS)

        is_voting_open, error = self.is_voting_open()
        if error != typ.Error(""):
            return error

        if not is_voting_open:
            return typ.Error(err.ARC_65_PREFIX + err.VOTING_PERIOD_EXPIRED)

        return typ.Error("")

    @subroutine
    def vote_input_validation(
        self, voter: Account, approvals: UInt64, rejections: UInt64
    ) -> typ.Error:
        if voter not in self.voters:
            return typ.Error(err.ARC_65_PREFIX + err.VOTER_NOT_FOUND)

        voter_box = self.voters[voter].copy()
        if voter_box.voted:
            return typ.Error(err.ARC_65_PREFIX + err.VOTER_ALREADY_VOTED)

        if approvals + rejections > voter_box.votes:
            return typ.Error(err.ARC_65_PREFIX + err.VOTES_EXCEEDED)

        return typ.Error("")

    @subroutine
    def scrutiny_check_authorization(self) -> None:
        assert self.status.value == enm.STATUS_VOTING, err.WRONG_PROPOSAL_STATUS

        is_voting_open, error = self.is_voting_open()
        assert error == typ.Error(""), err.MISSING_CONFIG

        assert (
            not is_voting_open  # voting period has ended
            or self.voted_members.value
            == self.committee_members.value  # all committee members have voted
        ), err.VOTING_ONGOING

    @subroutine
    def assign_voters_check_authorization(self) -> None:
        assert self.is_xgov_daemon(), err.UNAUTHORIZED
        assert self.status.value == enm.STATUS_SUBMITTED, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def assign_voter_input_validation(
        self, voter: Account, voting_power: UInt64
    ) -> None:
        assert voter not in self.voters, err.VOTER_ALREADY_ASSIGNED
        assert voting_power > 0, err.INVALID_VOTING_POWER

    @subroutine
    def get_discussion_duration(self, category: UInt64) -> UInt64:
        if category == enm.FUNDING_CATEGORY_SMALL:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_DISCUSSION_DURATION_SMALL)
            )
        elif category == enm.FUNDING_CATEGORY_MEDIUM:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_DISCUSSION_DURATION_MEDIUM)
            )
        else:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_DISCUSSION_DURATION_LARGE)
            )
        assert error == typ.Error(""), err.MISSING_CONFIG
        return value

    @subroutine
    def get_voting_duration(self, category: UInt64) -> tuple[UInt64, typ.Error]:
        if category == enm.FUNDING_CATEGORY_SMALL:
            return self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_VOTING_DURATION_SMALL)
            )
        elif category == enm.FUNDING_CATEGORY_MEDIUM:
            return self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_VOTING_DURATION_MEDIUM)
            )
        else:
            return self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_VOTING_DURATION_LARGE)
            )

    @subroutine
    def get_quorum(self, category: UInt64) -> UInt64:
        if category == enm.FUNDING_CATEGORY_SMALL:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_QUORUM_SMALL)
            )
        elif category == enm.FUNDING_CATEGORY_MEDIUM:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_QUORUM_MEDIUM)
            )
        else:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_QUORUM_LARGE)
            )
        assert error == typ.Error(""), err.MISSING_CONFIG
        return value

    @subroutine
    def get_weighted_quorum(self, category: UInt64) -> UInt64:
        if category == enm.FUNDING_CATEGORY_SMALL:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_WEIGHTED_QUORUM_SMALL)
            )
        elif category == enm.FUNDING_CATEGORY_MEDIUM:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_WEIGHTED_QUORUM_MEDIUM)
            )
        else:
            value, error = self.get_uint_from_registry_config(
                Bytes(reg_cfg.GS_KEY_WEIGHTED_QUORUM_LARGE)
            )
        assert error == typ.Error(""), err.MISSING_CONFIG
        return value

    @subroutine
    def verify_and_set_committee(self) -> typ.Error:

        committee_id = typ.Bytes32.from_bytes(
            self.get_bytes_from_registry_config(Bytes(reg_cfg.GS_KEY_COMMITTEE_ID))
        )
        if committee_id == typ.Bytes32.from_bytes(b""):
            return typ.Error(err.ARC_65_PREFIX + err.EMPTY_COMMITTEE_ID)

        committee_members, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_COMMITTEE_MEMBERS)
        )
        if error != typ.Error(""):
            return error
        if committee_members <= UInt64(0):
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_COMMITTEE_MEMBERS)

        committee_votes, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_COMMITTEE_VOTES)
        )
        if error != typ.Error(""):
            return error
        if committee_votes <= UInt64(0):
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_COMMITTEE_VOTES)

        self.committee_id.value = committee_id.copy()
        self.committee_members.value = committee_members
        self.committee_votes.value = committee_votes

        return typ.Error("")

    @subroutine
    def assert_draft_and_proposer(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
        assert (
            self.status.value == enm.STATUS_DRAFT and not self.finalized.value
        ), err.WRONG_PROPOSAL_STATUS

    @subroutine
    def submit_check_authorization(self) -> None:

        self.assert_draft_and_proposer()

        discussion_duration = Global.latest_timestamp - self.open_ts.value
        minimum_discussion_duration = self.get_discussion_duration(
            self.funding_category.value
        )

        assert discussion_duration >= minimum_discussion_duration, err.TOO_EARLY

    @subroutine
    def drop_check_authorization(self) -> typ.Error:
        assert self.is_registry_call(), err.UNAUTHORIZED
        if self.status.value != enm.STATUS_DRAFT or self.finalized.value:
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_PROPOSAL_STATUS)
        return typ.Error("")

    @subroutine
    def upload_metadata_check_authorization(self) -> None:
        self.assert_draft_and_proposer()

    @subroutine
    def upload_metadata_input_validation(self, payload: arc4.DynamicBytes) -> None:
        assert payload.length > 0, err.EMPTY_PAYLOAD

    @subroutine
    def open_check_authorization(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
        assert (
            self.status.value == enm.STATUS_EMPTY and not self.finalized.value
        ), err.WRONG_PROPOSAL_STATUS

    @subroutine
    def open_input_validation(
        self,
        title: String,
        funding_type: UInt64,
        requested_amount: UInt64,
    ) -> None:

        assert title.bytes.length <= const.TITLE_MAX_BYTES, err.WRONG_TITLE_LENGTH
        assert title != "", err.WRONG_TITLE_LENGTH

        assert (
            funding_type == enm.FUNDING_PROACTIVE
            or funding_type == enm.FUNDING_RETROACTIVE
        ), err.WRONG_FUNDING_TYPE

        min_requested_amount, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MIN_REQUESTED_AMOUNT)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

        max_requested_amount_large, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_LARGE)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

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
        proposal_commitment_bps, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG
        return self.relative_to_absolute_amount(
            requested_amount,
            proposal_commitment_bps,
        )

    @subroutine
    def open_payment_validation(
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
        max_requested_amount_small, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_SMALL)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

        max_requested_amount_medium, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

        if requested_amount <= max_requested_amount_small:
            self.funding_category.value = UInt64(enm.FUNDING_CATEGORY_SMALL)
        elif requested_amount <= max_requested_amount_medium:
            self.funding_category.value = UInt64(enm.FUNDING_CATEGORY_MEDIUM)
        else:
            self.funding_category.value = UInt64(enm.FUNDING_CATEGORY_LARGE)

    @subroutine
    def get_uint_from_registry_config(
        self, global_state_key: Bytes
    ) -> tuple[UInt64, typ.Error]:
        value, exists = AppGlobal.get_ex_uint64(
            self.registry_app_id.value, global_state_key
        )
        error = typ.Error("")
        if not exists:
            error = typ.Error(err.ARC_65_PREFIX + err.MISSING_CONFIG)
        return value, error

    @subroutine
    def get_bytes_from_registry_config(self, global_state_key: Bytes) -> Bytes:
        value, exists = AppGlobal.get_ex_bytes(
            self.registry_app_id.value, global_state_key
        )
        assert exists, err.MISSING_CONFIG
        return value

    @subroutine
    def check_registry_not_paused(self) -> None:
        registry_paused, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_PAUSED_REGISTRY)
        )

        assert error == typ.Error(""), err.MISSING_CONFIG
        assert not registry_paused, err.PAUSED_REGISTRY

    @subroutine
    def is_creator(self) -> bool:
        return Txn.sender == Global.creator_address

    @subroutine
    def is_proposer(self) -> bool:
        return Txn.sender == self.proposer.value

    @subroutine
    def is_council(self) -> bool:
        return Txn.sender == Account(
            self.get_bytes_from_registry_config(Bytes(reg_cfg.GS_KEY_XGOV_COUNCIL))
        )

    @subroutine
    def is_xgov_daemon(self) -> bool:
        return Txn.sender == Account(
            self.get_bytes_from_registry_config(Bytes(reg_cfg.GS_KEY_XGOV_DAEMON))
        )

    @subroutine
    def is_registry_call(self) -> bool:
        return Global.caller_application_id == self.registry_app_id.value

    @subroutine
    def pay(self, receiver: Account, amount: UInt64) -> None:
        itxn.Payment(
            receiver=receiver,
            amount=amount,
            fee=UInt64(0),  # enforces the sender to pay the fee
        ).submit()

    @subroutine
    def transfer_locked_amount(self, receiver: Account) -> None:
        self.pay(receiver, self.locked_amount.value)
        self.locked_amount.value = UInt64(0)

    @subroutine
    def assert_same_app_and_method(self, group_index: UInt64) -> None:
        assert (
            GTxn.application_id(group_index) == Global.current_application_id
        ), err.WRONG_APP_ID
        assert GTxn.application_args(group_index, 0) == Txn.application_args(
            0
        ), err.WRONG_METHOD_CALL

    @arc4.abimethod(create="require")
    def create(self, proposer: arc4.Address) -> typ.Error:
        """Create a new proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.

        Args:
            proposer (arc4.Address): Address of the proposer

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Registry
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.EMPTY_COMMITTEE_ID: If the committee ID is not available from the registry
            err.WRONG_COMMITTEE_MEMBERS: If the committee members do not match the required number
            err.WRONG_COMMITTEE_VOTES: If the committee votes do not match the required number
        """
        assert (
            Global.caller_application_id != 0
        ), err.UNAUTHORIZED  # Only callable by another contract

        self.proposer.value = proposer.native
        self.registry_app_id.value = Global.caller_application_id

        return self.verify_and_set_committee()

    @arc4.abimethod()
    def open(
        self,
        payment: gtxn.PaymentTransaction,
        title: arc4.String,
        funding_type: arc4.UInt64,
        requested_amount: arc4.UInt64,
        focus: arc4.UInt8,
    ) -> None:
        """Open the first draft of the proposal.

        Args:
            payment (gtxn.PaymentTransaction): Commitment payment transaction from the proposer to the contract
            title (String): Proposal title, max TITLE_MAX_BYTES bytes
            funding_type (UInt64): Funding type (Proactive / Retroactive)
            requested_amount (UInt64): Requested amount in microAlgos
            focus (UInt8): Proposal focus area

        Raises:
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.PAUSED_REGISTRY: Registry's non-admin methods are paused
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_EMPTY
            err.WRONG_TITLE_LENGTH: If the title length is not within the limits
            err.WRONG_FUNDING_TYPE: If the funding type is not FUNDING_PROACTIVE or FUNDING_RETROACTIVE
            err.WRONG_MIN_REQUESTED_AMOUNT: If the requested amount is less than the minimum requested amount
            err.WRONG_MAX_REQUESTED_AMOUNT: If the requested amount is more than the maximum requested amount
            err.WRONG_SENDER: If the sender of the payment transaction is not the proposer
            err.WRONG_RECEIVER: If the receiver of the payment transaction is not the current application address
            err.WRONG_LOCKED_AMOUNT: If the amount in the payment transaction is not equal to the expected locked amount

        """

        self.check_registry_not_paused()

        self.open_check_authorization()

        self.open_input_validation(
            title.native, funding_type.as_uint64(), requested_amount.as_uint64()
        )
        self.open_payment_validation(payment, requested_amount.as_uint64())

        self.title.value = title.native
        self.set_category(requested_amount.as_uint64())
        self.funding_type.value = funding_type.as_uint64()
        self.requested_amount.value = requested_amount.as_uint64()
        self.focus.value = focus.as_uint64()
        self.locked_amount.value = self.get_expected_locked_amount(
            requested_amount.as_uint64()
        )
        self.open_ts.value = Global.latest_timestamp
        self.status.value = UInt64(enm.STATUS_DRAFT)

    @arc4.abimethod()
    def upload_metadata(
        self, payload: arc4.DynamicBytes, is_first_in_group: arc4.Bool
    ) -> None:
        """Upload the proposal metadata.

        Args:
            payload (DynamicBytes): Metadata payload
            is_first_in_group (bool): True if this is the first upload call in a group transaction

        Raises:
            err.PAUSED_REGISTRY: Registry's non-admin methods are paused
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT
            err.EMPTY_PAYLOAD: If the payload is empty
        """

        self.check_registry_not_paused()

        self.upload_metadata_check_authorization()
        self.upload_metadata_input_validation(payload)

        self.metadata_uploaded = True

        if is_first_in_group:
            # clear and write the metadata to the box
            del self.metadata.value
            self.metadata.value = payload.native
        else:
            # append the metadata to the box
            old_size = self.metadata.length
            self.metadata.resize(self.metadata.length + payload.length)
            self.metadata.replace(old_size, payload.native)

    @arc4.abimethod()
    def drop(self) -> typ.Error:
        """Drop the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.

        Raises:
            err.UNAUTHORIZED: If the sender is not the registry contract
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT

        """

        error = self.drop_check_authorization()
        if error != typ.Error(""):
            return error

        self.transfer_locked_amount(
            receiver=self.proposer.value,
        )

        del self.metadata.value
        self.finalized.value = True

        return typ.Error("")

    @arc4.abimethod()
    def submit(self) -> None:
        """submit the proposal.

        Raises:
            err.PAUSED_REGISTRY: Registry's non-admin methods are paused
            err.UNAUTHORIZED: If the sender is not the proposer
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.MISSING_METADATA: The proposal description metadata is missing
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT
            err.TOO_EARLY: If the proposal is submitted before the minimum time
        """
        self.check_registry_not_paused()

        self.submit_check_authorization()

        self.status.value = UInt64(enm.STATUS_SUBMITTED)
        self.submission_ts.value = Global.latest_timestamp

        open_proposal_fee, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_OPEN_PROPOSAL_FEE)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

        assert self.metadata_uploaded, err.MISSING_METADATA

        daemon_ops_funding_bps, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_DAEMON_OPS_FUNDING_BPS)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

        self.pay(
            receiver=Account(
                self.get_bytes_from_registry_config(Bytes(reg_cfg.GS_KEY_XGOV_DAEMON))
            ),
            amount=self.relative_to_absolute_amount(
                open_proposal_fee, daemon_ops_funding_bps
            ),
        )

    @subroutine
    def _assign_voter(self, voter: Account, voting_power: UInt64) -> None:
        self.assign_voter_input_validation(voter, voting_power)

        self.voters[voter] = typ.VoterBox(
            votes=arc4.UInt64(voting_power),
            voted=arc4.Bool(False),  # noqa: FBT003
        )

        self.voters_count += 1
        self.assigned_votes += voting_power

    @arc4.abimethod()
    def assign_voters(
        self,
        voters: arc4.DynamicArray[CommitteeMember],
    ) -> None:
        """Assign multiple voters to the proposal.

        Args:
            voters (DynamicArray[CommitteeMember]): List of voter addresses with their voting power

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Daemon
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_SUBMITTED
            err.WRONG_APP_ID: If the app ID is not as expected
            err.WRONG_METHOD_CALL: If the method call is not as expected
            err.VOTER_ALREADY_ASSIGNED: If the voter is already assigned
            err.INVALID_VOTING_POWER: If the voting power is not within the limits
            err.VOTING_POWER_MISMATCH: If the total voting power does not match the committee votes

        """

        self.assign_voters_check_authorization()

        if Txn.group_index == 0:
            # Check that the entire group calls the same app and method
            for i in urange(1, Global.group_size):
                self.assert_same_app_and_method(i)
        else:
            # Check that the first transaction in the group calls the same app and method
            self.assert_same_app_and_method(UInt64(0))

        for i in urange(voters.length):
            self._assign_voter(
                voters[i].address.native, voters[i].voting_power.as_uint64()
            )

        if self.voters_count == self.committee_members.value:
            assert (
                self.assigned_votes == self.committee_votes.value
            ), err.VOTING_POWER_MISMATCH
            self.status.value = UInt64(enm.STATUS_VOTING)
            self.vote_open_ts.value = Global.latest_timestamp

    @arc4.abimethod()
    def vote(
        self, voter: arc4.Address, approvals: arc4.UInt64, rejections: arc4.UInt64
    ) -> typ.Error:
        """Vote on the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.

        Args:
            voter (arc4.Address): Voter address
            approvals (arc4.UInt64): Number of approvals
            rejections (arc4.UInt64): Number of rejections

        Raises:
            err.UNAUTHORIZED: If the sender is not the registry contract
            err.VOTER_NOT_FOUND: If the voter is not assigned to the proposal
            err.VOTER_ALREADY_VOTED: If the voter has already voted
            err.VOTES_EXCEEDED: If the total votes exceed the assigned voting power
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_VOTING
            err.VOTING_PERIOD_EXPIRED: If the voting period has expired

        """

        error = self.vote_check_authorization()
        if error != typ.Error(""):
            return error

        error = self.vote_input_validation(
            voter.native, approvals.as_uint64(), rejections.as_uint64()
        )
        if error != typ.Error(""):
            return error

        voter_box = self.voters[voter.native].copy()
        self.voters[voter.native] = typ.VoterBox(
            votes=voter_box.votes,
            voted=arc4.Bool(True),  # noqa: FBT003
        )

        self.voted_members.value += 1

        nulls = (
            voter_box.votes.as_uint64() - approvals.as_uint64() - rejections.as_uint64()
        )

        self.approvals.value += approvals.as_uint64()
        self.rejections.value += rejections.as_uint64()
        self.nulls.value += nulls

        return typ.Error("")

    @arc4.abimethod()
    def scrutiny(self) -> None:
        """Scrutinize the proposal.

        Raises:
            err.PAUSED_REGISTRY: Registry's non-admin methods are paused
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_VOTING
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.VOTING_ONGOING: If the voting period is still ongoing

        """
        self.check_registry_not_paused()

        self.scrutiny_check_authorization()

        # A category dependent quorum of all xGov Voting Committee (1 xGov, 1 vote) is reached.
        # Null votes affect this quorum.
        quorum_bps = self.get_quorum(self.funding_category.value)
        minimum_voters_required = self.relative_to_absolute_amount(
            self.committee_members.value, quorum_bps
        )

        # A category dependent weighted quorum of all xGov Voting Committee voting power (1 vote) is reached.
        # Null votes affect this quorum.
        weighted_quorum_bps = self.get_weighted_quorum(self.funding_category.value)
        total_votes = self.approvals.value + self.rejections.value + self.nulls.value
        minimum_votes_required = self.relative_to_absolute_amount(
            self.committee_votes.value, weighted_quorum_bps
        )

        if (
            self.voted_members.value >= minimum_voters_required
            and total_votes >= minimum_votes_required
            # The relative majority of Approved over Rejected votes is reached.
            # Null votes do not affect the relative majority.
            and self.approvals.value > self.rejections.value
        ):
            self.status.value = UInt64(enm.STATUS_APPROVED)
        else:
            self.status.value = UInt64(enm.STATUS_REJECTED)
            self.transfer_locked_amount(
                receiver=self.proposer.value,
            )

    @arc4.abimethod()
    def review(self, block: bool) -> None:  # noqa: FBT001
        """Review the proposal.

        Args:
            block (bool): Whether to block the proposal or not

        Raises:
            err.UNAUTHORIZED: If the sender is not the xgov council
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_APPROVED
            err.MISSING_CONFIG: If one of the required configuration values is missing

        """
        self.review_check_authorization()

        if block:
            self.status.value = UInt64(enm.STATUS_BLOCKED)

            # slashing: send locked amount to the registry treasury
            reg_app = Application(self.registry_app_id.value)
            self.transfer_locked_amount(
                receiver=reg_app.address,
            )

        else:
            self.status.value = UInt64(enm.STATUS_REVIEWED)

    @arc4.abimethod()
    def fund(self) -> typ.Error:
        """Fund the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.

        Raises:
            err.UNAUTHORIZED: If the sender is not the registry contract
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_APPROVED

        """
        error = self.fund_check_authorization()
        if error != typ.Error(""):
            return error

        self.status.value = UInt64(enm.STATUS_FUNDED)

        # refund the locked amount to the proposer
        self.transfer_locked_amount(
            receiver=self.proposer.value,
        )

        return typ.Error("")

    @arc4.abimethod()
    def unassign_voters(self, voters: arc4.DynamicArray[arc4.Address]) -> None:
        """Unassign voters from the proposal.

        Args:
            voters: List of voters to be unassigned

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Daemon
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not as expected
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.WRONG_APP_ID: If the app ID is not as expected
            err.WRONG_METHOD_CALL: If the method call is not as expected

        """
        self.unassign_voters_check_authorization()
        if Txn.group_index == 0:
            # Check that the entire group calls the same app and method
            for i in urange(1, Global.group_size):
                self.assert_same_app_and_method(i)
        else:
            # Check that the first transaction in the group calls the same app and method
            self.assert_same_app_and_method(UInt64(0))

        # remove voters
        for voter in voters:
            if voter.native in self.voters:
                self.voters_count -= 1
                self.assigned_votes -= self.voters[voter.native].votes.native
                del self.voters[voter.native]

    @arc4.abimethod()
    def finalize(self) -> typ.Error:
        """Finalize the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.

        Raises:
            err.UNAUTHORIZED: If the sender is not the registry contract
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not as expected
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.VOTERS_ASSIGNED: If there are still assigned voters

        """
        error = self.finalize_check_authorization()
        if error != typ.Error(""):
            return error

        # check no assigned voters
        if self.voters_count > UInt64(0):
            return typ.Error(err.ARC_65_PREFIX + err.VOTERS_ASSIGNED)

        # refund the locked amount for DRAFT proposals
        # for REJECTED proposals, the locked amount is already refunded in the scrutiny method
        # for EMPTY, FUNDED, or BLOCKED proposals, the locked amount is not refundable
        if self.status.value == enm.STATUS_DRAFT:
            self.transfer_locked_amount(
                receiver=self.proposer.value,
            )
        reg_app = Application(self.registry_app_id.value)
        self.pay(
            receiver=reg_app.address,
            amount=Global.current_application_address.balance
            - Global.current_application_address.min_balance,
        )
        self.finalized.value = True

        return typ.Error("")

    @arc4.abimethod(allow_actions=("DeleteApplication",))
    def delete(self) -> None:
        """Delete the proposal.

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Daemon
            err.WRONG_PROPOSAL_STATUS: If the proposal is not finalized

        """

        self.delete_check_authorization()

        # delete metadata box if it exists
        del self.metadata.value

        reg_app = Application(self.registry_app_id.value)
        self.pay(
            receiver=reg_app.address,
            amount=Global.current_application_address.balance,
        )

    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.ProposalTypedGlobalState:
        """Get the proposal state.

        Returns:
            typ.ProposalTypedGlobalState: The proposal state

        """
        return typ.ProposalTypedGlobalState(
            proposer=arc4.Address(self.proposer.value),
            registry_app_id=arc4.UInt64(self.registry_app_id.value),
            title=arc4.String(self.title.value),
            open_ts=arc4.UInt64(self.open_ts.value),
            submission_ts=arc4.UInt64(self.submission_ts.value),
            vote_open_ts=arc4.UInt64(self.vote_open_ts.value),
            status=arc4.UInt64(self.status.value),
            finalized=arc4.Bool(self.finalized.value),
            funding_category=arc4.UInt64(self.funding_category.value),
            focus=arc4.UInt8(self.focus.value),
            funding_type=arc4.UInt64(self.funding_type.value),
            requested_amount=arc4.UInt64(self.requested_amount.value),
            locked_amount=arc4.UInt64(self.locked_amount.value),
            committee_id=self.committee_id.value.copy(),
            committee_members=arc4.UInt64(self.committee_members.value),
            committee_votes=arc4.UInt64(self.committee_votes.value),
            voted_members=arc4.UInt64(self.voted_members.value),
            approvals=arc4.UInt64(self.approvals.value),
            rejections=arc4.UInt64(self.rejections.value),
            nulls=arc4.UInt64(self.nulls.value),
        )

    @arc4.abimethod()
    def op_up(self) -> None:
        return
