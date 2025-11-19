# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Global,
    GlobalState,
    String,
    UInt64,
    arc4,
    itxn,
)

import smart_contracts.errors.std_errors as err
from smart_contracts.proposal.contract import Proposal

from ..common.abi_types import Bytes32
from ..xgov_registry import config as reg_cfg


class XgovRegistryMock(ARC4Contract):
    def __init__(self) -> None:
        self.proposal_commitment_bps = GlobalState(
            UInt64(reg_cfg.PROPOSAL_COMMITMENT_BPS),
            key=reg_cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS,
        )
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
        self.daemon_ops_funding_bps = GlobalState(
            UInt64(reg_cfg.DAEMON_OPS_FUNDING_BPS),
            key=reg_cfg.GS_KEY_DAEMON_OPS_FUNDING_BPS,
        )
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
        self.xgov_daemon = GlobalState(
            arc4.Address(),
            key=reg_cfg.GS_KEY_XGOV_DAEMON,
        )
        self.open_proposal_fee = GlobalState(
            UInt64(reg_cfg.OPEN_PROPOSAL_FEE),
            key=reg_cfg.GS_KEY_OPEN_PROPOSAL_FEE,
        )
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
        self.xgov_council = GlobalState(
            arc4.Address(),
            key=reg_cfg.GS_KEY_XGOV_COUNCIL,
        )
        self.paused_registry = GlobalState(
            UInt64(0),
            key=reg_cfg.GS_KEY_PAUSED_REGISTRY,
        )
        self.paused_proposals = GlobalState(
            UInt64(0),
            key=reg_cfg.GS_KEY_PAUSED_PROPOSALS,
        )

    @arc4.abimethod()
    def pause_registry(self) -> None:
        """
        Pauses the xGov Registry non-administrative methods.
        """

        self.paused_registry.value = UInt64(1)

    @arc4.abimethod()
    def pause_proposals(self) -> None:
        """
        Pauses the creation of new Proposals.
        """

        self.paused_proposals.value = UInt64(1)

    @arc4.abimethod()
    def resume_registry(self) -> None:
        """
        Resumes the xGov Registry non-administrative methods.
        """

        self.paused_registry.value = UInt64(0)

    @arc4.abimethod()
    def resume_proposals(self) -> None:
        """
        Resumes the creation of new Proposals.
        """

        self.paused_proposals.value = UInt64(0)

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
    def set_daemon_ops_funding_bps(self, daemon_ops_funding_bps: UInt64) -> None:
        """
        Set the daemon operations funding in basis points

        Args:
            daemon_ops_funding_bps (UInt64): The daemon operations funding in basis points

        """
        self.daemon_ops_funding_bps.value = daemon_ops_funding_bps

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
    def set_xgov_daemon(self, xgov_daemon: arc4.Address) -> None:
        """
        Set the xGov Daemon

        Args:
            xgov_daemon (arc4.Address): The xGov Daemon

        """
        self.xgov_daemon.value = xgov_daemon

    @arc4.abimethod()
    def set_open_proposal_fee(self, open_proposal_fee: UInt64) -> None:
        """
        Set the fee to open a proposal

        Args:
            open_proposal_fee (UInt64): The proposal fee

        """
        self.open_proposal_fee.value = open_proposal_fee

    @arc4.abimethod()
    def set_committee_id(self, committee_id: Bytes32) -> None:
        """
        Set the committee ID

        Args:
            committee_id (Cid): The committee ID

        """
        self.committee_id.value = committee_id.copy()

    @arc4.abimethod()
    def clear_committee_id(self) -> None:
        """
        Clear the committee ID

        """
        self.committee_id.value = Bytes32.from_bytes(b"0" * 32)

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

    @arc4.abimethod()
    def set_voting_duration_small(self, voting_duration: UInt64) -> None:
        """
        Set the voting duration for small proposals

        Args:
            voting_duration (UInt64): The voting duration

        """
        self.voting_duration_small.value = voting_duration

    @arc4.abimethod()
    def set_voting_duration_medium(self, voting_duration: UInt64) -> None:
        """
        Set the voting duration for medium proposals

        Args:
            voting_duration (UInt64): The voting duration

        """
        self.voting_duration_medium.value = voting_duration

    @arc4.abimethod()
    def set_voting_duration_large(self, voting_duration: UInt64) -> None:
        """
        Set the voting duration for large proposals

        Args:
            voting_duration (UInt64): The voting duration

        """
        self.voting_duration_large.value = voting_duration

    @arc4.abimethod()
    def set_quorum_small(self, quorum: UInt64) -> None:
        """
        Set the quorum for small proposals

        Args:
            quorum (UInt64): The quorum

        """
        self.quorum_small.value = quorum

    @arc4.abimethod()
    def set_quorum_large(self, quorum: UInt64) -> None:
        """
        Set the quorum for large proposals

        Args:
            quorum (UInt64): The quorum

        """
        self.quorum_large.value = quorum

    @arc4.abimethod()
    def set_weighted_quorum_small(self, weighted_quorum: UInt64) -> None:
        """
        Set the weighted quorum for small proposals

        Args:
            weighted_quorum (UInt64): The weighted quorum

        """
        self.weighted_quorum_small.value = weighted_quorum

    @arc4.abimethod()
    def set_weighted_quorum_large(self, weighted_quorum: UInt64) -> None:
        """
        Set the weighted quorum for large proposals

        Args:
            weighted_quorum (UInt64): The weighted quorum

        """
        self.weighted_quorum_large.value = weighted_quorum

    @arc4.abimethod()
    def vote(
        self,
        proposal_app: arc4.UInt64,
        voter: arc4.Address,
        approvals: arc4.UInt64,
        rejections: arc4.UInt64,
    ) -> None:
        """
        Vote on a proposal

        Args:
            proposal_app (arc4.UInt64): The proposal app
            voter (arc4.Address): The voter
            approvals (arc4.UInt64): The number of approvals
            rejections (arc4.UInt64): The number of rejections

        Raises:
            err.UNAUTHORIZED: If the sender is not the registry contract
            err.VOTER_NOT_FOUND: If the voter is not assigned to the proposal
            err.VOTER_ALREADY_VOTED: If the voter has already voted
            err.VOTES_EXCEEDED: If the total votes exceed the assigned voting power
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_VOTING
            err.VOTING_PERIOD_EXPIRED: If the voting period has expired

        """
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
    def set_xgov_council(self, xgov_council: arc4.Address) -> None:
        """
        Set the XGov council

        Args:
            xgov_council (arc4.Address): The XGov council

        """
        self.xgov_council.value = xgov_council

    @arc4.abimethod()
    def fund(self, proposal_app: arc4.UInt64) -> None:
        """
        Fund a proposal

        Args:
            proposal_app (arc4.UInt64): The proposal app

        Raises:
            err.UNAUTHORIZED: If the sender is not the registry contract
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not STATUS_APPROVED
            err.MISSING_CONFIG: If one of the required configuration values is missing

        """
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
    def is_proposal(self, proposal_id: arc4.UInt64) -> None:
        return
