# pyright: reportMissingModuleSource=false

from algopy import (
    Account,
    Application,
    ARC4Contract,
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
)
from algopy.op import AppGlobal

import smart_contracts.errors.std_errors as err
from smart_contracts.common import abi_types as typ

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
        self.vote_open_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_VOTE_OPEN_TS,
        )
        self.status = GlobalState(
            UInt64(enm.STATUS_EMPTY),
            key=prop_cfg.GS_KEY_STATUS,
        )
        self.funding_category = GlobalState(
            UInt64(enm.FUNDING_CATEGORY_NULL),
            key=prop_cfg.GS_KEY_FUNDING_CATEGORY,
        )
        self.focus = GlobalState(
            arc4.UInt8(0),
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
        self.nulls = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_NULLS,
        )
        self.cool_down_start_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_COOL_DOWN_START_TS,
        )

        self.voters = BoxMap(
            Account, typ.VoterBox, key_prefix=prop_cfg.VOTER_BOX_KEY_PREFIX
        )
        self.voters_count = UInt64(0)
        self.assigned_votes = UInt64(0)

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
        assert self.is_reviewer(), err.UNAUTHORIZED
        assert self.status.value == enm.STATUS_APPROVED, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def fund_check_authorization(self) -> typ.Error:
        assert self.is_registry_call(), err.UNAUTHORIZED
        if self.status.value != enm.STATUS_REVIEWED:
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_PROPOSAL_STATUS)

        return typ.Error("")

    @subroutine
    def decommission_check_authorization(self) -> None:
        assert self.is_committee_publisher(), err.UNAUTHORIZED
        assert (
            # TODO: Support STATUS_DRAFT here when we add stale proposal management
            self.status.value == enm.STATUS_FUNDED
            or self.status.value == enm.STATUS_BLOCKED
            or self.status.value == enm.STATUS_REJECTED
        ), err.WRONG_PROPOSAL_STATUS

        cooldown_duration, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_COOL_DOWN_DURATION)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG
        assert (
            self.cool_down_start_ts.value != 0
            and Global.latest_timestamp
            >= self.cool_down_start_ts.value + cooldown_duration
        ), err.TOO_EARLY

    @subroutine
    def delete_check_authorization(self) -> typ.Error:
        assert self.is_registry_call(), err.UNAUTHORIZED
        if self.status.value != enm.STATUS_DECOMMISSIONED:
            return typ.Error(err.ARC_65_PREFIX + err.WRONG_PROPOSAL_STATUS)

        return typ.Error("")

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
    def assign_voter_check_authorization(self) -> None:
        assert self.is_committee_publisher(), err.UNAUTHORIZED
        assert self.status.value == enm.STATUS_FINAL, err.WRONG_PROPOSAL_STATUS

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
    def verify_and_set_committee(self) -> None:

        committee_id = typ.CommitteeId.from_bytes(
            self.get_bytes_from_registry_config(Bytes(reg_cfg.GS_KEY_COMMITTEE_ID))
        )
        assert committee_id != typ.CommitteeId.from_bytes(b""), err.EMPTY_COMMITTEE_ID

        committee_members, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_COMMITTEE_MEMBERS)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG
        assert committee_members > UInt64(0), err.WRONG_COMMITTEE_MEMBERS

        committee_votes, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_COMMITTEE_VOTES)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG
        assert committee_votes > UInt64(0), err.WRONG_COMMITTEE_VOTES

        self.committee_id.value = committee_id.copy()
        self.committee_members.value = committee_members
        self.committee_votes.value = committee_votes

    @subroutine
    def finalize_check_authorization(self) -> None:

        assert self.is_proposer(), err.UNAUTHORIZED
        assert self.status.value == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS

        discussion_duration = Global.latest_timestamp - self.submission_ts.value
        minimum_discussion_duration = self.get_discussion_duration(
            self.funding_category.value
        )

        assert discussion_duration >= minimum_discussion_duration, err.TOO_EARLY

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
        assert self.status.value == enm.STATUS_DRAFT, err.WRONG_PROPOSAL_STATUS

    @subroutine
    def submit_check_authorization(self) -> None:
        assert self.is_proposer(), err.UNAUTHORIZED
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
    def is_creator(self) -> bool:
        return Txn.sender == Global.creator_address

    @subroutine
    def is_proposer(self) -> bool:
        return Txn.sender == self.proposer.value

    @subroutine
    def is_reviewer(self) -> bool:
        return Txn.sender == Account(
            self.get_bytes_from_registry_config(Bytes(reg_cfg.GS_KEY_XGOV_REVIEWER))
        )

    @subroutine
    def is_committee_publisher(self) -> bool:
        return Txn.sender == Account(
            self.get_bytes_from_registry_config(
                Bytes(reg_cfg.GS_KEY_COMMITTEE_PUBLISHER)
            )
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

    @arc4.abimethod(create="require")
    def create(self, proposer: arc4.Address) -> None:
        """Create a new proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.

        Args:
            proposer (arc4.Address): Address of the proposer
        """
        assert (
            Global.caller_application_id != 0
        ), err.UNAUTHORIZED  # Only callable by another contract

        self.proposer.value = proposer.native
        self.registry_app_id.value = Global.caller_application_id

    @arc4.abimethod()
    def submit(
        self,
        payment: gtxn.PaymentTransaction,
        title: arc4.String,
        cid: typ.Cid,
        funding_type: arc4.UInt64,
        requested_amount: arc4.UInt64,
        focus: arc4.UInt8,
    ) -> None:
        """Submit the first draft of the proposal.

        Args:
            payment (gtxn.PaymentTransaction): Commitment payment transaction from the proposer to the contract
            title (String): Proposal title, max TITLE_MAX_BYTES bytes
            cid (typ.Cid): IPFS V1 CID
            funding_type (UInt64): Funding type (Proactive / Retroactive)
            requested_amount (UInt64): Requested amount in microAlgos
            focus (UInt8): Proposal focus area

        Raises:
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.UNAUTHORIZED: If the sender is not the proposer
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

        self.submit_input_validation(
            title.native, cid, funding_type.native, requested_amount.native
        )
        self.submit_payment_validation(payment, requested_amount.native)

        self.title.value = title.native
        self.cid.value = cid.copy()
        self.set_category(requested_amount.native)
        self.funding_type.value = funding_type.native
        self.requested_amount.value = requested_amount.native
        self.focus.value = focus
        self.locked_amount.value = self.get_expected_locked_amount(
            requested_amount.native
        )
        self.submission_ts.value = Global.latest_timestamp
        self.status.value = UInt64(enm.STATUS_DRAFT)

    @arc4.abimethod()
    def update(self, title: arc4.String, cid: typ.Cid) -> None:
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

        self.updateable_input_validation(title.native, cid)

        self.title.value = title.native
        self.cid.value = cid.copy()

    @arc4.abimethod()
    def drop(self) -> None:
        """Drop the proposal.

        Raises:
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT

        """
        self.drop_check_authorization()

        self.transfer_locked_amount(
            receiver=self.proposer.value,
        )

        #  Clear the proposal data TODO: check if this can be in a struct and clear the struct
        self.title.value = String()
        self.cid.value = typ.Cid.from_bytes(b"")
        self.funding_category.value = UInt64(enm.FUNDING_CATEGORY_NULL)
        self.focus.value = arc4.UInt8(0)
        self.funding_type.value = UInt64(enm.FUNDING_NULL)
        self.requested_amount.value = UInt64(0)
        self.locked_amount.value = UInt64(0)
        self.submission_ts.value = UInt64(0)
        self.status.value = UInt64(enm.STATUS_EMPTY)

    @arc4.abimethod()
    def finalize(self) -> None:
        """Finalize the proposal.

        Raises:
            err.UNAUTHORIZED: If the sender is not the proposer
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DRAFT
            err.TOO_EARLY: If the proposal is finalized before the minimum time
            err.EMPTY_COMMITTEE_ID: If the committee ID is not available from the registry
            err.WRONG_COMMITTEE_MEMBERS: If the committee members do not match the required number
            err.WRONG_COMMITTEE_VOTES: If the committee votes do not match the required number

        """
        self.finalize_check_authorization()

        self.verify_and_set_committee()

        self.status.value = UInt64(enm.STATUS_FINAL)
        self.finalization_ts.value = Global.latest_timestamp

        proposal_fee, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_PROPOSAL_FEE)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

        publishing_fee_bps, error = self.get_uint_from_registry_config(
            Bytes(reg_cfg.GS_KEY_PROPOSAL_PUBLISHING_BPS)
        )
        assert error == typ.Error(""), err.MISSING_CONFIG

        self.pay(
            receiver=Account(
                self.get_bytes_from_registry_config(
                    Bytes(reg_cfg.GS_KEY_COMMITTEE_PUBLISHER)
                )
            ),
            amount=self.relative_to_absolute_amount(proposal_fee, publishing_fee_bps),
        )

    @arc4.abimethod()
    def assign_voter(self, voter: arc4.Address, voting_power: arc4.UInt64) -> None:
        """Assign a voter to the proposal.

        Args:
            voter (arc4.Address): Voter address
            voting_power (UInt64): Voting power

        Raises:
            err.UNAUTHORIZED: If the sender is not the committee publisher
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_FINAL
            err.VOTER_ALREADY_ASSIGNED: If the voter is already assigned
            err.INVALID_VOTING_POWER: If the voting power is not within the limits
            err.VOTING_POWER_MISMATCH: If the total voting power does not match the committee votes

        """
        self.assign_voter_check_authorization()

        self.assign_voter_input_validation(voter.native, voting_power.native)

        self.voters[voter.native] = typ.VoterBox(
            votes=voting_power,
            voted=arc4.Bool(False),  # noqa: FBT003
        )

        self.voters_count += 1
        self.assigned_votes += voting_power.native

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
            voter.native, approvals.native, rejections.native
        )
        if error != typ.Error(""):
            return error

        voter_box = self.voters[voter.native].copy()
        self.voters[voter.native] = typ.VoterBox(
            votes=voter_box.votes,
            voted=arc4.Bool(True),  # noqa: FBT003
        )

        self.voted_members.value += 1

        nulls = voter_box.votes.native - approvals.native - rejections.native

        self.approvals.value += approvals.native
        self.rejections.value += rejections.native
        self.nulls.value += nulls

        return typ.Error("")

    @arc4.abimethod()
    def scrutiny(self) -> None:
        """Scrutinize the proposal.

        Raises:
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_VOTING
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.VOTING_ONGOING: If the voting period is still ongoing

        """
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
            self.locked_amount.value = UInt64(0)
            self.cool_down_start_ts.value = Global.latest_timestamp

    @arc4.abimethod()
    def review(self, block: bool) -> None:  # noqa: FBT001
        """Review the proposal.

        Args:
            block (bool): Whether to block the proposal or not

        Raises:
            err.UNAUTHORIZED: If the sender is not the xgov reviewer
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

            self.locked_amount.value = UInt64(0)
            self.cool_down_start_ts.value = Global.latest_timestamp
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

        self.locked_amount.value = UInt64(0)
        self.cool_down_start_ts.value = Global.latest_timestamp

        return typ.Error("")

    @arc4.abimethod()
    def decommission(self, voters: arc4.DynamicArray[arc4.Address]) -> None:
        """Decommission the proposal.

        Args:
            voters: List of voters to be removed

        Raises:
            err.UNAUTHORIZED: If the sender is not the committee publisher
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_FUNDED, STATUS_BLOCKED or STATUS_REJECTED
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.TOO_EARLY: If the proposal is still in the cool down period

        """
        self.decommission_check_authorization()

        # remove voters
        for voter in voters:
            if voter.native in self.voters:
                del self.voters[voter.native]

        # if all voters are removed, refund the treasury and decommission the proposal
        if Global.current_application_address.total_boxes == UInt64(0):
            reg_app = Application(self.registry_app_id.value)
            self.pay(
                receiver=reg_app.address,
                amount=Global.current_application_address.balance,
            )
            self.status.value = UInt64(enm.STATUS_DECOMMISSIONED)

    @arc4.abimethod(allow_actions=("DeleteApplication",))
    def delete(self) -> typ.Error:
        """Delete the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.

        Raises:
            err.UNAUTHORIZED: If the sender is not the registry contract
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_DECOMMISSIONED

        """
        error = self.delete_check_authorization()
        if error != typ.Error(""):
            return error

        return typ.Error("")

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
            cid=self.cid.value.copy(),
            submission_ts=arc4.UInt64(self.submission_ts.value),
            finalization_ts=arc4.UInt64(self.finalization_ts.value),
            vote_open_ts=arc4.UInt64(self.vote_open_ts.value),
            status=arc4.UInt64(self.status.value),
            funding_category=arc4.UInt64(self.funding_category.value),
            focus=self.focus.value,
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
            cool_down_start_ts=arc4.UInt64(self.cool_down_start_ts.value),
        )
