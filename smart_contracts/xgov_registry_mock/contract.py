import typing as t

from algopy import (
    Bytes,
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

from ..common.abi_types import Bytes32
from ..xgov_registry import config as reg_cfg


class XgovRegistryMock(XGovRegistryInterface):
    def __init__(self) -> None:

        # Role-Based Access Control (RBAC)
        self.xgov_council = GlobalState(
            arc4.Address(),
            key=reg_cfg.GS_KEY_XGOV_COUNCIL,
        )
        self.xgov_daemon = GlobalState(
            arc4.Address(),
            key=reg_cfg.GS_KEY_XGOV_DAEMON,
        )

        # Registry Control States
        self.paused_registry = GlobalState(
            UInt64(0),
            key=reg_cfg.GS_KEY_PAUSED_REGISTRY,
        )
        self.paused_proposals = GlobalState(
            UInt64(0),
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

        # xGov Committee
        self.committee_id = GlobalState(
            Bytes32.from_bytes(b"0" * 32),
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

    @arc4.abimethod(create="require")
    def create(self) -> None:
        pass

    @arc4.abimethod()
    def init_proposal_contract(self, size: arc4.UInt64) -> None:
        pass

    @arc4.abimethod()
    def load_proposal_contract(self, offset: arc4.UInt64, data: Bytes) -> None:
        pass

    @arc4.abimethod()
    def delete_proposal_contract_box(self) -> None:
        pass

    @arc4.abimethod()
    def pause_registry(self) -> None:
        self.paused_registry.value = UInt64(1)

    @arc4.abimethod()
    def pause_proposals(self) -> None:
        self.paused_proposals.value = UInt64(1)

    @arc4.abimethod()
    def resume_registry(self) -> None:
        self.paused_registry.value = UInt64(0)

    @arc4.abimethod()
    def resume_proposals(self) -> None:
        self.paused_proposals.value = UInt64(0)

    @arc4.abimethod()
    def set_xgov_manager(self, manager: arc4.Address) -> None:
        pass

    @arc4.abimethod()
    def set_payor(self, payor: arc4.Address) -> None:
        pass

    @arc4.abimethod()
    def set_xgov_council(self, council: arc4.Address) -> None:
        self.xgov_council.value = council

    @arc4.abimethod()
    def set_xgov_subscriber(self, subscriber: arc4.Address) -> None:
        pass

    @arc4.abimethod()
    def set_kyc_provider(self, provider: arc4.Address) -> None:
        pass

    @arc4.abimethod()
    def set_committee_manager(self, manager: arc4.Address) -> None:
        pass

    @arc4.abimethod()
    def set_xgov_daemon(self, xgov_daemon: arc4.Address) -> None:
        self.xgov_daemon.value = xgov_daemon

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
        pass

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_xgov_registry(self) -> None:
        pass

    @arc4.abimethod()
    def subscribe_xgov(
        self, voting_address: arc4.Address, payment: gtxn.PaymentTransaction
    ) -> None:
        pass

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        pass

    @arc4.abimethod()
    def approve_subscribe_xgov(self, request_id: arc4.UInt64) -> None:
        pass

    @arc4.abimethod()
    def reject_subscribe_xgov(self, request_id: arc4.UInt64) -> None:
        pass

    @arc4.abimethod()
    def request_subscribe_xgov(
        self,
        xgov_address: arc4.Address,
        owner_address: arc4.Address,
        relation_type: arc4.UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> None:
        pass

    @arc4.abimethod()
    def request_unsubscribe_xgov(
        self,
        xgov_address: arc4.Address,
        owner_address: arc4.Address,
        relation_type: arc4.UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> None:
        pass

    @arc4.abimethod()
    def approve_unsubscribe_xgov(self, request_id: arc4.UInt64) -> None:
        pass

    @arc4.abimethod()
    def reject_unsubscribe_xgov(self, request_id: arc4.UInt64) -> None:
        pass

    @arc4.abimethod()
    def set_voting_account(
        self, xgov_address: arc4.Address, voting_address: arc4.Address
    ) -> None:
        pass

    @arc4.abimethod()
    def subscribe_proposer(self, payment: gtxn.PaymentTransaction) -> None:
        pass

    @arc4.abimethod()
    def set_proposer_kyc(
        self, proposer: arc4.Address, kyc_status: arc4.Bool, kyc_expiring: arc4.UInt64
    ) -> None:
        pass

    @arc4.abimethod()
    def declare_committee(
        self, committee_id: typ.Bytes32, size: arc4.UInt64, votes: arc4.UInt64
    ) -> None:
        self.committee_id.value = committee_id.copy()
        self.committee_members.value = size.as_uint64()
        self.committee_votes.value = votes.as_uint64()

    @arc4.abimethod()
    def open_proposal(self, payment: gtxn.PaymentTransaction) -> arc4.UInt64:
        return arc4.UInt64(0)

    @arc4.abimethod()
    def vote_proposal(
        self,
        proposal_app: arc4.UInt64,
        voter: arc4.Address,
        approvals: arc4.UInt64,
        rejections: arc4.UInt64,
    ) -> None:
        error, _tx = arc4.abi_call(
            Proposal.vote,
            voter,
            approvals,
            rejections,
            app_id=proposal_app.as_uint64(),
            fee=0,
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.UNAUTHORIZED:
                    assert False, err.UNAUTHORIZED  # noqa
                case err.VOTER_NOT_FOUND:
                    assert False, err.VOTER_NOT_FOUND  # noqa
                case err.VOTER_ALREADY_VOTED:
                    assert False, err.VOTER_ALREADY_VOTED  # noqa
                case err.VOTES_EXCEEDED:
                    assert False, err.VOTES_EXCEEDED  # noqa
                case err.MISSING_CONFIG:
                    assert False, err.MISSING_CONFIG  # noqa
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case err.VOTING_PERIOD_EXPIRED:
                    assert False, err.VOTING_PERIOD_EXPIRED  # noqa
                case _:
                    assert False, "Unknown error"  # noqa

    @arc4.abimethod()
    def pay_grant_proposal(self, proposal_app: arc4.UInt64) -> None:
        error, _tx = arc4.abi_call(
            Proposal.fund,
            app_id=proposal_app.as_uint64(),
            fee=0,
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.UNAUTHORIZED:
                    assert False, err.UNAUTHORIZED  # noqa
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case _:
                    assert False, "Unknown error"  # noqa

    @arc4.abimethod()
    def finalize_proposal(self, proposal_app: arc4.UInt64) -> None:
        error, _tx = arc4.abi_call(
            Proposal.finalize,
            app_id=proposal_app.as_uint64(),
            fee=0,
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
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
    def drop_proposal(self, proposal_app: arc4.UInt64) -> None:
        error, _tx = arc4.abi_call(
            Proposal.drop,
            app_id=proposal_app.as_uint64(),
            fee=0,
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case _:
                    assert False, "Unknown error"  # noqa

    @arc4.abimethod()
    def deposit_funds(self, payment: gtxn.PaymentTransaction) -> None:
        pass

    @arc4.abimethod()
    def withdraw_funds(self, amount: arc4.UInt64) -> None:
        pass

    @arc4.abimethod()
    def withdraw_balance(self) -> None:
        pass

    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.TypedGlobalState:
        return typ.TypedGlobalState(
            paused_registry=arc4.Bool(bool(self.paused_registry.value)),
            paused_proposals=arc4.Bool(bool(self.paused_proposals.value)),
            xgov_manager=arc4.Address(Global.zero_address),
            xgov_payor=arc4.Address(Global.zero_address),
            xgov_council=self.xgov_council.value,
            xgov_subscriber=arc4.Address(Global.zero_address),
            kyc_provider=arc4.Address(Global.zero_address),
            committee_manager=arc4.Address(Global.zero_address),
            xgov_daemon=self.xgov_daemon.value,
            xgov_fee=arc4.UInt64(0),
            proposer_fee=arc4.UInt64(0),
            open_proposal_fee=arc4.UInt64(self.open_proposal_fee.value),
            daemon_ops_funding_bps=arc4.UInt64(self.daemon_ops_funding_bps.value),
            proposal_commitment_bps=arc4.UInt64(self.proposal_commitment_bps.value),
            min_requested_amount=arc4.UInt64(self.min_requested_amount.value),
            max_requested_amount=arc4.StaticArray[arc4.UInt64, t.Literal[3]](
                arc4.UInt64(self.max_requested_amount_small.value),
                arc4.UInt64(self.max_requested_amount_medium.value),
                arc4.UInt64(self.max_requested_amount_large.value),
            ),
            discussion_duration=arc4.StaticArray[arc4.UInt64, t.Literal[4]](
                arc4.UInt64(self.discussion_duration_small.value),
                arc4.UInt64(self.discussion_duration_medium.value),
                arc4.UInt64(self.discussion_duration_large.value),
                arc4.UInt64(0),
            ),
            voting_duration=arc4.StaticArray[arc4.UInt64, t.Literal[4]](
                arc4.UInt64(self.voting_duration_small.value),
                arc4.UInt64(self.voting_duration_medium.value),
                arc4.UInt64(self.voting_duration_large.value),
                arc4.UInt64(0),
            ),
            quorum=arc4.StaticArray[arc4.UInt64, t.Literal[3]](
                arc4.UInt64(self.quorum_small.value),
                arc4.UInt64(self.quorum_medium.value),  # No longer used
                arc4.UInt64(self.quorum_large.value),
            ),
            weighted_quorum=arc4.StaticArray[arc4.UInt64, t.Literal[3]](
                arc4.UInt64(self.weighted_quorum_small.value),
                arc4.UInt64(self.weighted_quorum_medium.value),
                # No longer used
                arc4.UInt64(self.weighted_quorum_large.value),
            ),
            outstanding_funds=arc4.UInt64(0),
            pending_proposals=arc4.UInt64(0),
            committee_id=self.committee_id.value.copy(),
            committee_members=arc4.UInt64(self.committee_members.value),
            committee_votes=arc4.UInt64(self.committee_votes.value),
        )

    @arc4.abimethod(readonly=True)
    def get_xgov_box(self, xgov_address: arc4.Address) -> tuple[typ.XGovBoxValue, bool]:
        return (
            typ.XGovBoxValue(
                voting_address=arc4.Address(),
                voted_proposals=arc4.UInt64(0),
                last_vote_timestamp=arc4.UInt64(0),
                subscription_round=arc4.UInt64(0),
            ),
            False,
        )

    @arc4.abimethod(readonly=True)
    def get_proposer_box(
        self,
        proposer_address: arc4.Address,
    ) -> tuple[typ.ProposerBoxValue, bool]:
        return (
            typ.ProposerBoxValue(
                active_proposal=arc4.Bool(),
                kyc_status=arc4.Bool(),
                kyc_expiring=arc4.UInt64(0),
            ),
            False,
        )

    @arc4.abimethod(readonly=True)
    def get_request_box(
        self,
        request_id: arc4.UInt64,
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        return (
            typ.XGovSubscribeRequestBoxValue(
                xgov_addr=arc4.Address(),
                owner_addr=arc4.Address(),
                relation_type=arc4.UInt64(0),
            ),
            False,
        )

    @arc4.abimethod(readonly=True)
    def get_request_unsubscribe_box(
        self, request_id: arc4.UInt64
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        return (
            typ.XGovSubscribeRequestBoxValue(
                xgov_addr=arc4.Address(),
                owner_addr=arc4.Address(),
                relation_type=arc4.UInt64(0),
            ),
            False,
        )

    @arc4.abimethod()
    def is_proposal(self, proposal_id: arc4.UInt64) -> None:
        return

    @arc4.abimethod()
    def create_empty_proposal(
        self,
        proposer: arc4.Address,
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
