# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Global,
    StateTotals,
    String,
    Txn,
    UInt64,
    arc4,
    subroutine,
)

import smart_contracts.errors.std_errors as err

from . import config as cfg
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

    @arc4.abimethod(create="require")
    def create(self, proposer: arc4.Address) -> None:
        self.proposer = proposer

    @subroutine
    def is_creator(self) -> bool:
        return Txn.sender == Global.creator_address

    @subroutine
    def is_proposer(self) -> bool:
        return Txn.sender == self.proposer

    @subroutine
    def is_kyc_verified(self) -> bool:
        return True
