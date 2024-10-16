# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Global,
    GlobalState,
    StateTotals,
    String,
    Txn,
    UInt64,
    arc4,
)

import smart_contracts.errors.std_errors as err

from ..proposal import config as prop_cfg
from ..proposal import enums as enm
from ..proposal import types as typ

class ProposalMock(
    ARC4Contract,
    state_totals=StateTotals(
        global_bytes=prop_cfg.GLOBAL_BYTES,
        global_uints=prop_cfg.GLOBAL_UINTS,
        local_bytes=prop_cfg.LOCAL_BYTES,
        local_uints=prop_cfg.LOCAL_UINTS,
    ),
):

    def __init__(self) -> None:

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
    def set_status(self, status: UInt64) -> None:
        self.status.value = status

    @arc4.abimethod()
    def set_requested_amount(self, requested_amount: UInt64) -> None:
        self.requested_amount.value = requested_amount

    @arc4.abimethod()
    def set_committee_details(self, id: typ.CommitteeId, size: UInt64, votes: UInt64) -> None:
        self.committee_id.value = id.copy()
        self.committee_members.value = size
        self.committee_votes.value = votes

    @arc4.abimethod()
    def release_funds(self) -> None:
        pass

    @arc4.abimethod()
    def vote(
        self,
        xgov_address: arc4.Address,
        approval_votes: arc4.UInt64,
        rejection_votes: arc4.UInt64,
        null_votes: arc4.UInt64
    ) -> None:
        pass