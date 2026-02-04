from algopy import (
    Account,
    Application,
    Array,
    Bytes,
    FixedArray,
    Global,
    GlobalState,
    String,
    UInt64,
    arc4,
    gtxn,
    itxn,
)

import smart_contracts.common.abi_types as typ
import smart_contracts.errors.std_errors as err
from smart_contracts.interfaces.xgov_registry import XGovRegistryInterface
from smart_contracts.proposal.contract import Proposal

from ..xgov_registry import config as reg_cfg


class XgovRegistryMock(XGovRegistryInterface):
    def __init__(self) -> None:

        # Role-Based Access Control (RBAC)
        self.xgov_council = GlobalState(
            Account(),
            key=reg_cfg.GS_KEY_XGOV_COUNCIL,
        )
        self.xgov_daemon = GlobalState(
            Account(),
            key=reg_cfg.GS_KEY_XGOV_DAEMON,
        )

        # Registry Control States
        self.paused_registry = GlobalState(
            False,  # noqa: FBT003
            key=reg_cfg.GS_KEY_PAUSED_REGISTRY,
        )
        self.paused_proposals = GlobalState(
            False,  # noqa: FBT003
            key=reg_cfg.GS_KEY_PAUSED_PROPOSALS,
        )

        # Fees
        self.open_proposal_fee = GlobalState(
            UInt64(reg_cfg.OPEN_PROPOSAL_FEE),
            key=reg_cfg.GS_KEY_OPEN_PROPOSAL_FEE,
        )
        self.daemon_ops_funding_bps = GlobalState(
            UInt64(reg_cfg.DAEMON_OPS_FUNDING_BPS),
            key=reg_cfg.GS_KEY_DAEMON_OPS_FUNDING_BPS,
        )
        self.proposal_commitment_bps = GlobalState(
            UInt64(reg_cfg.PROPOSAL_COMMITMENT_BPS),
            key=reg_cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS,
        )

        # Requested Amount Limits
        self.min_requested_amount = GlobalState(
            UInt64(reg_cfg.MIN_REQUESTED_AMOUNT),
            key=reg_cfg.GS_KEY_MIN_REQUESTED_AMOUNT,
        )
        self.max_requested_amount_small = GlobalState(
            UInt64(reg_cfg.MAX_REQUESTED_AMOUNT_SMALL),
            key=reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_SMALL,
        )
        self.max_requested_amount_medium = GlobalState(
            UInt64(reg_cfg.MAX_REQUESTED_AMOUNT_MEDIUM),
            key=reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM,
        )
        self.max_requested_amount_large = GlobalState(
            UInt64(reg_cfg.MAX_REQUESTED_AMOUNT_LARGE),
            key=reg_cfg.GS_KEY_MAX_REQUESTED_AMOUNT_LARGE,
        )

        # Time Limits
        self.discussion_duration_small = GlobalState(
            UInt64(reg_cfg.DISCUSSION_DURATION_SMALL),
            key=reg_cfg.GS_KEY_DISCUSSION_DURATION_SMALL,
        )
        self.discussion_duration_medium = GlobalState(
            UInt64(reg_cfg.DISCUSSION_DURATION_MEDIUM),
            key=reg_cfg.GS_KEY_DISCUSSION_DURATION_MEDIUM,
        )
        self.discussion_duration_large = GlobalState(
            UInt64(reg_cfg.DISCUSSION_DURATION_LARGE),
            key=reg_cfg.GS_KEY_DISCUSSION_DURATION_LARGE,
        )
        self.discussion_duration_xlarge = GlobalState(
            UInt64(reg_cfg.DISCUSSION_DURATION_XLARGE),
            key=reg_cfg.GS_KEY_DISCUSSION_DURATION_XLARGE,
        )
        self.voting_duration_small = GlobalState(
            UInt64(reg_cfg.VOTING_DURATION_SMALL),
            key=reg_cfg.GS_KEY_VOTING_DURATION_SMALL,
        )
        self.voting_duration_medium = GlobalState(
            UInt64(reg_cfg.VOTING_DURATION_MEDIUM),
            key=reg_cfg.GS_KEY_VOTING_DURATION_MEDIUM,
        )
        self.voting_duration_large = GlobalState(
            UInt64(reg_cfg.VOTING_DURATION_LARGE),
            key=reg_cfg.GS_KEY_VOTING_DURATION_LARGE,
        )
        self.voting_duration_xlarge = GlobalState(
            UInt64(reg_cfg.VOTING_DURATION_XLARGE),
            key=reg_cfg.GS_KEY_VOTING_DURATION_XLARGE,
        )

        # xGov Committee
        self.committee_id = GlobalState(
            typ.Bytes32.from_bytes(b"0" * 32),
            key=reg_cfg.GS_KEY_COMMITTEE_ID,
        )
        self.committee_members = GlobalState(
            UInt64(),
            key=reg_cfg.GS_KEY_COMMITTEE_MEMBERS,
        )
        self.committee_votes = GlobalState(
            UInt64(),
            key=reg_cfg.GS_KEY_COMMITTEE_VOTES,
        )

        # Quorums
        self.quorum_small = GlobalState(
            UInt64(reg_cfg.QUORUM_SMALL),
            key=reg_cfg.GS_KEY_QUORUM_SMALL,
        )
        self.quorum_medium = GlobalState(
            UInt64(reg_cfg.QUORUM_MEDIUM),
            key=reg_cfg.GS_KEY_QUORUM_MEDIUM,
        )
        self.quorum_large = GlobalState(
            UInt64(reg_cfg.QUORUM_LARGE),
            key=reg_cfg.GS_KEY_QUORUM_LARGE,
        )

        # Weighted Quorums
        self.weighted_quorum_small = GlobalState(
            UInt64(reg_cfg.WEIGHTED_QUORUM_SMALL),
            key=reg_cfg.GS_KEY_WEIGHTED_QUORUM_SMALL,
        )
        self.weighted_quorum_medium = GlobalState(
            UInt64(reg_cfg.WEIGHTED_QUORUM_MEDIUM),
            key=reg_cfg.GS_KEY_WEIGHTED_QUORUM_MEDIUM,
        )
        self.weighted_quorum_large = GlobalState(
            UInt64(reg_cfg.WEIGHTED_QUORUM_LARGE),
            key=reg_cfg.GS_KEY_WEIGHTED_QUORUM_LARGE,
        )

        # New Variables (introduced after MainNet deployment)
        self.absence_tolerance = GlobalState(
            UInt64(reg_cfg.ABSENCE_TOLERANCE), key=reg_cfg.GS_KEY_ABSENCE_TOLERANCE
        )
        self.governance_period = GlobalState(
            UInt64(reg_cfg.GOVERNANCE_PERIOD), key=reg_cfg.GS_KEY_GOVERNANCE_PERIOD
        )
        self.committee_grace_period = GlobalState(
            UInt64(reg_cfg.COMMITTEE_GRACE_PERIOD),
            key=reg_cfg.GS_KEY_COMMITTEE_GRACE_PERIOD,
        )
        self.committee_last_anchor = GlobalState(
            UInt64(), key=reg_cfg.GS_KEY_COMMITTEE_LAST_ANCHOR
        )

    @arc4.abimethod(create="require")
    def create(self) -> None:
        pass

    @arc4.abimethod()
    def init_proposal_contract(self, *, size: UInt64) -> None:
        pass

    @arc4.abimethod()
    def load_proposal_contract(self, *, offset: UInt64, data: Bytes) -> None:
        pass

    @arc4.abimethod()
    def delete_proposal_contract_box(self) -> None:
        pass

    @arc4.abimethod()
    def pause_registry(self) -> None:
        self.paused_registry.value = True

    @arc4.abimethod()
    def pause_proposals(self) -> None:
        self.paused_proposals.value = True

    @arc4.abimethod()
    def resume_registry(self) -> None:
        self.paused_registry.value = False

    @arc4.abimethod()
    def resume_proposals(self) -> None:
        self.paused_proposals.value = False

    @arc4.abimethod()
    def set_xgov_manager(self, *, manager: Account) -> None:
        pass

    @arc4.abimethod()
    def set_payor(self, *, payor: Account) -> None:
        pass

    @arc4.abimethod()
    def set_xgov_council(self, *, council: Account) -> None:
        self.xgov_council.value = council

    @arc4.abimethod()
    def set_xgov_subscriber(self, *, subscriber: Account) -> None:
        pass

    @arc4.abimethod()
    def set_kyc_provider(self, *, provider: Account) -> None:
        pass

    @arc4.abimethod()
    def set_committee_manager(self, *, manager: Account) -> None:
        pass

    @arc4.abimethod()
    def set_xgov_daemon(self, *, xgov_daemon: Account) -> None:
        self.xgov_daemon.value = xgov_daemon

    @arc4.abimethod()
    def config_xgov_registry(self, *, config: typ.XGovRegistryConfig) -> None:
        pass

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_xgov_registry(self) -> None:
        pass

    @arc4.abimethod()
    def subscribe_xgov(
        self, *, voting_address: Account, payment: gtxn.PaymentTransaction
    ) -> None:
        pass

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        pass

    @arc4.abimethod()
    def unsubscribe_absentee(self, *, xgov_address: Account) -> None:
        pass

    @arc4.abimethod()
    def request_subscribe_xgov(
        self,
        *,
        xgov_address: Account,
        owner_address: Account,
        relation_type: UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> UInt64:
        return UInt64(0)

    @arc4.abimethod()
    def approve_subscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @arc4.abimethod()
    def reject_subscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @arc4.abimethod()
    def request_unsubscribe_xgov(
        self,
        *,
        xgov_address: Account,
        owner_address: Account,
        relation_type: UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> UInt64:
        return UInt64(0)

    @arc4.abimethod()
    def approve_unsubscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @arc4.abimethod()
    def reject_unsubscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @arc4.abimethod()
    def set_voting_account(
        self, *, xgov_address: Account, voting_address: Account
    ) -> None:
        pass

    @arc4.abimethod()
    def subscribe_proposer(self, *, payment: gtxn.PaymentTransaction) -> None:
        pass

    @arc4.abimethod()
    def set_proposer_kyc(
        self,
        *,
        proposer: Account,
        kyc_status: bool,
        kyc_expiring: UInt64,
    ) -> None:
        pass

    @arc4.abimethod()
    def declare_committee(
        self, *, committee_id: typ.Bytes32, size: UInt64, votes: UInt64
    ) -> None:
        self.committee_id.value = committee_id.copy()
        self.committee_members.value = size
        self.committee_votes.value = votes

    @arc4.abimethod()
    def open_proposal(self, *, payment: gtxn.PaymentTransaction) -> UInt64:
        return UInt64(0)

    @arc4.abimethod()
    def vote_proposal(
        self,
        *,
        proposal_id: Application,
        xgov_address: Account,
        approval_votes: UInt64,
        rejection_votes: UInt64,
    ) -> None:
        error, _tx = arc4.abi_call(
            Proposal.vote,
            xgov_address,
            approval_votes,
            rejection_votes,
            app_id=proposal_id,
        )

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.UNAUTHORIZED:
                    assert False, err.UNAUTHORIZED  # noqa
                case err.VOTER_NOT_FOUND:
                    assert False, err.VOTER_NOT_FOUND  # noqa
                case err.VOTER_ALREADY_VOTED:
                    assert False, err.VOTER_ALREADY_VOTED  # noqa
                case err.VOTES_INVALID:
                    assert False, err.VOTES_INVALID  # noqa
                case err.MISSING_CONFIG:
                    assert False, err.MISSING_CONFIG  # noqa
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case err.VOTING_PERIOD_EXPIRED:
                    assert False, err.VOTING_PERIOD_EXPIRED  # noqa
                case _:
                    assert False, "Unknown error"  # noqa

    @arc4.abimethod()
    def unassign_absentee_from_proposal(
        self, *, proposal_id: Application, absentees: Array[Account]
    ) -> None:
        error, _tx = arc4.abi_call(
            Proposal.unassign_absentees,
            absentees,
            app_id=proposal_id,
        )

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case err.VOTER_NOT_FOUND:
                    assert False, err.VOTER_NOT_FOUND  # noqa
                case _:
                    assert False, "Unknown error"  # noqa
        else:
            assert error == "", "Unknown error"

    @arc4.abimethod()
    def pay_grant_proposal(self, *, proposal_id: Application) -> None:
        error, _tx = arc4.abi_call(Proposal.fund, app_id=proposal_id)

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.UNAUTHORIZED:
                    assert False, err.UNAUTHORIZED  # noqa
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case _:
                    assert False, "Unknown error"  # noqa

    @arc4.abimethod()
    def finalize_proposal(self, *, proposal_id: Application) -> None:
        error, _tx = arc4.abi_call(Proposal.finalize, app_id=proposal_id)

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case err.MISSING_CONFIG:
                    assert False, err.MISSING_CONFIG  # noqa
                case err.VOTERS_ASSIGNED:
                    assert False, err.VOTERS_ASSIGNED  # noqa
                case _:
                    assert False, "Unknown error"  # noqa

    @arc4.abimethod()
    def drop_proposal(self, *, proposal_id: Application) -> None:
        error, _tx = arc4.abi_call(Proposal.drop, app_id=proposal_id)

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case _:
                    assert False, "Unknown error"  # noqa

    @arc4.abimethod()
    def deposit_funds(self, *, payment: gtxn.PaymentTransaction) -> None:
        pass

    @arc4.abimethod()
    def withdraw_funds(self, *, amount: UInt64) -> None:
        pass

    @arc4.abimethod()
    def withdraw_balance(self) -> None:
        pass

    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.TypedGlobalState:
        return typ.TypedGlobalState(
            paused_registry=self.paused_registry.value,
            paused_proposals=self.paused_proposals.value,
            xgov_manager=Global.zero_address,
            xgov_payor=Global.zero_address,
            xgov_council=self.xgov_council.value,
            xgov_subscriber=Global.zero_address,
            kyc_provider=Global.zero_address,
            committee_manager=Global.zero_address,
            xgov_daemon=self.xgov_daemon.value,
            xgov_fee=UInt64(0),
            proposer_fee=UInt64(0),
            open_proposal_fee=self.open_proposal_fee.value,
            daemon_ops_funding_bps=self.daemon_ops_funding_bps.value,
            proposal_commitment_bps=self.proposal_commitment_bps.value,
            min_requested_amount=self.min_requested_amount.value,
            max_requested_amount=FixedArray(
                (
                    self.max_requested_amount_small.value,
                    self.max_requested_amount_medium.value,
                    self.max_requested_amount_large.value,
                )
            ),
            discussion_duration=FixedArray(
                (
                    self.discussion_duration_small.value,
                    self.discussion_duration_medium.value,
                    self.discussion_duration_large.value,
                    self.discussion_duration_xlarge.value,
                )
            ),
            voting_duration=FixedArray(
                (
                    self.voting_duration_small.value,
                    self.voting_duration_medium.value,
                    self.voting_duration_large.value,
                    self.voting_duration_xlarge.value,
                )
            ),
            quorum=FixedArray(
                (
                    self.quorum_small.value,
                    self.quorum_medium.value,  # No longer used
                    self.quorum_large.value,
                )
            ),
            weighted_quorum=FixedArray(
                (
                    self.weighted_quorum_small.value,
                    self.weighted_quorum_medium.value,  # No longer used
                    self.weighted_quorum_large.value,
                )
            ),
            outstanding_funds=UInt64(0),
            pending_proposals=UInt64(0),
            committee_id=self.committee_id.value.copy(),
            committee_members=self.committee_members.value,
            committee_votes=self.committee_votes.value,
            absence_tolerance=self.absence_tolerance.value,
            governance_period=self.governance_period.value,
            committee_grace_period=self.committee_grace_period.value,
            committee_last_anchor=self.committee_last_anchor.value,
        )

    @arc4.abimethod(readonly=True)
    def get_xgov_box(self, *, xgov_address: Account) -> tuple[typ.XGovBoxValue, bool]:
        return (
            typ.XGovBoxValue(
                voting_address=Account(),
                tolerated_absences=UInt64(0),
                unsubscribed_round=UInt64(0),
                subscription_round=UInt64(0),
            ),
            False,
        )

    @arc4.abimethod(readonly=True)
    def get_proposer_box(
        self,
        *,
        proposer_address: Account,
    ) -> tuple[typ.ProposerBoxValue, bool]:
        return (
            typ.ProposerBoxValue(
                active_proposal=False,
                kyc_status=False,
                kyc_expiring=UInt64(0),
            ),
            False,
        )

    @arc4.abimethod(readonly=True)
    def get_request_box(
        self,
        *,
        request_id: UInt64,
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        return (
            typ.XGovSubscribeRequestBoxValue(
                xgov_addr=Account(),
                owner_addr=Account(),
                relation_type=UInt64(0),
            ),
            False,
        )

    @arc4.abimethod(readonly=True)
    def get_request_unsubscribe_box(
        self, *, request_id: UInt64
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        return (
            typ.XGovSubscribeRequestBoxValue(
                xgov_addr=Account(),
                owner_addr=Account(),
                relation_type=UInt64(0),
            ),
            False,
        )

    @arc4.abimethod()
    def is_proposal(self, *, proposal_id: Application) -> None:
        return

    @arc4.abimethod()
    def create_empty_proposal(
        self,
        *,
        proposer: Account,
    ) -> UInt64:
        mbr_before = Global.current_application_address.min_balance
        res = arc4.arc4_create(
            Proposal,
            proposer,
        )
        mbr_after = Global.current_application_address.min_balance

        itxn.Payment(
            receiver=res.created_app.address,
            amount=self.open_proposal_fee.value - (mbr_after - mbr_before),
            fee=0,
        ).submit()

        return res.created_app.id

    @arc4.abimethod()
    def op_up(self) -> None:
        pass
