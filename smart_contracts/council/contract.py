# pyright: reportMissingModuleSource=false

from algopy import (
    Account,
    ARC4Contract,
    BoxMap,
    Bytes,
    GlobalState,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    urange,
)
from algopy.op import AppGlobal

import smart_contracts.errors.std_errors as err
from smart_contracts.common import abi_types as typ

from ..proposal import config as proposal_cfg
from ..proposal import contract as proposal_contract
from ..proposal import enums as proposal_enm
from ..xgov_registry import contract as registry_contract
from . import config as council_cfg


class Council(
    ARC4Contract,
    state_totals=StateTotals(
        global_bytes=council_cfg.GLOBAL_BYTES,
        global_uints=council_cfg.GLOBAL_UINTS,
        local_bytes=council_cfg.LOCAL_BYTES,
        local_uints=council_cfg.LOCAL_UINTS,
    ),
):
    def __init__(self) -> None:
        assert (
            Txn.global_num_byte_slice == council_cfg.GLOBAL_BYTES
        ), err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == council_cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert (
            Txn.local_num_byte_slice == council_cfg.LOCAL_BYTES
        ), err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == council_cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

        self.admin = GlobalState(
            Account,
            key=council_cfg.GS_KEY_ADMIN,
        )

        self.registry_app_id = GlobalState(
            UInt64(),
            key=council_cfg.GS_KEY_REGISTRY_APP_ID,
        )

        self.member_count = GlobalState(
            UInt64(),
            key=council_cfg.GS_KEY_MEMBER_COUNT,
        )

        self.members = BoxMap(
            Account, typ.Empty, key_prefix=council_cfg.MEMBERS_KEY_PREFIX
        )

        self.votes = BoxMap(
            UInt64, typ.CouncilVotingBox, key_prefix=council_cfg.VOTES_KEY_PREFIX
        )

    @arc4.abimethod(create="require")
    def create(self, admin: Account, registry_id: UInt64) -> None:
        """
        Create a new council contract.

        Args:
            admin: The address of the admin who can manage the council.
            registry_id: The application ID of the XGovRegistry contract.

        Raises:
            err.INVALID_REGISTRY_ID: If the registry ID is not greater than 0.
        """

        assert registry_id > 0, err.INVALID_REGISTRY_ID

        self.admin.value = admin
        self.registry_app_id.value = registry_id
        self.member_count.value = UInt64(0)

    @arc4.abimethod()
    def add_member(self, address: arc4.Address) -> None:
        """
        Add a member to the council.

        Args:
            address: The address of the member to add.

        Raises:
            err.UNAUTHORIZED: If the sender is not the admin.
            err.VOTER_ALREADY_ASSIGNED: If the address is already a member.
        """

        assert Txn.sender == self.admin.value, err.UNAUTHORIZED
        assert address.native not in self.members, err.VOTER_ALREADY_ASSIGNED

        self.members[address.native] = typ.Empty()
        self.member_count.value += 1

    @arc4.abimethod()
    def remove_member(self, address: arc4.Address) -> None:
        """
        Remove a member from the council.

        Args:
            address: The address of the member to remove.

        Raises:
            err.UNAUTHORIZED: If the sender is not the admin.
            err.VOTER_NOT_FOUND: If the address is not a member.
        """

        assert Txn.sender == self.admin.value, err.UNAUTHORIZED
        assert address.native in self.members, err.VOTER_NOT_FOUND

        del self.members[address.native]
        self.member_count.value -= 1

    @arc4.abimethod()
    def vote(self, proposal_id: UInt64, block: bool) -> None:  # noqa: FBT001
        """
        Cast a vote on a proposal.

        Args:
            proposal_id: The ID of the proposal to vote on.
            block: Whether or not to block the proposal.

        Raises:
            err.VOTER_NOT_FOUND: If the sender is not a member of the council.
            err.INVALID_PROPOSAL: If the proposal ID is invalid or does not exist.
            err.WRONG_PROPOSAL_STATUS: If the proposal is not approved.
            err.ALREADY_VOTED: If the sender has already voted on this proposal.
        """

        assert Txn.sender in self.members, err.VOTER_NOT_FOUND

        if proposal_id not in self.votes:
            # we dont need any error handling here
            # if its invalid the transaction will fail
            arc4.abi_call(
                registry_contract.XGovRegistry.is_proposal,
                arc4.UInt64(proposal_id),
                app_id=self.registry_app_id.value,
            )

            status, exists = AppGlobal.get_ex_uint64(
                proposal_id, Bytes(proposal_cfg.GS_KEY_STATUS)
            )

            assert exists, err.INVALID_PROPOSAL
            assert status == proposal_enm.STATUS_APPROVED, err.WRONG_PROPOSAL_STATUS

            self.votes[proposal_id] = arc4.DynamicArray(
                typ.CouncilVote(
                    address=arc4.Address(Txn.sender),
                    block=arc4.Bool(block),
                )
            )

        else:
            half_plus_one = (self.member_count.value // 2) + 1
            approvals = UInt64(0) if block else UInt64(1)
            rejections = UInt64(0) if not block else UInt64(1)

            for i in urange(self.votes[proposal_id].length):
                assert (
                    Txn.sender != self.votes[proposal_id][i].address
                ), err.VOTER_ALREADY_VOTED

                if self.votes[proposal_id][i].block:
                    rejections += 1
                else:
                    approvals += 1

            self.votes[proposal_id].append(
                typ.CouncilVote(
                    address=arc4.Address(Txn.sender),
                    block=arc4.Bool(block),
                )
            )

            if approvals >= half_plus_one or rejections >= half_plus_one:
                # this will allow the proposal to be reviewed
                block = rejections >= half_plus_one

                arc4.abi_call(
                    proposal_contract.Proposal.review, block, app_id=proposal_id
                )

                del self.votes[proposal_id]

    @arc4.abimethod()
    def op_up(self) -> None:
        return
