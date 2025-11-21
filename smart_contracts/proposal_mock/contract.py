# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Global,
    GlobalState,
    String,
    UInt64,
    arc4,
)

from ..common import abi_types as typ
from ..proposal import config as prop_cfg
from ..proposal import enums as enm
from ..xgov_registry import config as reg_cfg


class ProposalMock(ARC4Contract):
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
        self.submission_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_OPEN_TS,
        )
        self.finalization_ts = GlobalState(
            UInt64(),
            key=prop_cfg.GS_KEY_SUBMISSION_TS,
        )
        self.status = GlobalState(
            UInt64(enm.STATUS_EMPTY),
            key=prop_cfg.GS_KEY_STATUS,
        )
        self.funding_category = GlobalState(
            UInt64(enm.FUNDING_CATEGORY_NULL),
            key=prop_cfg.GS_KEY_FUNDING_CATEGORY,
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
        self.proposer.value = proposer
        self.registry_app_id.value = Global.caller_application_id

    @arc4.abimethod()
    def set_status(self, status: UInt64) -> None:
        self.status.value = status

    @arc4.abimethod()
    def set_requested_amount(self, requested_amount: UInt64) -> None:
        self.requested_amount.value = requested_amount

    @arc4.abimethod()
    def set_committee_details(
        self, metadata_hash: typ.Bytes32, size: UInt64, votes: UInt64
    ) -> None:
        self.committee_id.value = metadata_hash.copy()
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
    ) -> None:
        pass
