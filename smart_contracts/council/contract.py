# pyright: reportMissingModuleSource=false

from algopy import (
    Account,
    ARC4Contract,
    BoxMap,
    GlobalState,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    urange
)

import smart_contracts.errors.std_errors as err
from smart_contracts.common import abi_types as typ

from ..xgov_registry import contract as registry_contract

from ..proposal import contract as proposal_contract

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
        assert Txn.local_num_byte_slice == council_cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
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

    @arc4.abimethod()
    def add_member(self, address: arc4.Address) -> None:
        """
        Add a member to the council.

        Args:
            address: The address of the member to add.

        Raises:
            err.FORBIDDEN: If the sender is not the admin.
            err.ALREADY_MEMBER: If the address is already a member.
        """

        assert Txn.sender == self.admin.value, err.FORBIDDEN
        assert address.native not in self.members, err.ALREADY_MEMBER

        self.members[address.native] = typ.Empty()
        self.member_count.value += 1

    @arc4.abimethod()
    def remove_member(self, address: arc4.Address) -> None:
        """
        Remove a member from the council.

        Args:
            address: The address of the member to remove.

        Raises:
            err.FORBIDDEN: If the sender is not the admin.
            err.NOT_A_MEMBER: If the address is not a member.
        """

        assert Txn.sender == self.admin.value, err.FORBIDDEN
        assert address.native in self.members, err.NOT_A_MEMBER

        del self.members[address.native]
        self.member_count.value -= 1

    @arc4.abimethod()
    def vote(self, proposal_id: UInt64, approve: bool) -> None:
        """
        Cast a vote on a proposal.

        Args:
            proposal_id: The ID of the proposal to vote on.
            vote: The vote to cast (FOR, AGAINST, ABSTAIN).

        Raises:
            err.NOT_A_MEMBER: If the sender is not a member of the council.
            err.BAD_PROPOSAL_ID: If the proposal ID is invalid or does not exist.
            err.BAD_VOTE: If the vote is not one of the valid options (APPROVE, REJECT, ABSTAIN).
            err.VOTING_CLOSED: If the voting period for the proposal has ended.
            err.ALREADY_VOTED: If the sender has already voted on this proposal.
        """

        assert Txn.sender in self.members, err.NOT_A_MEMBER

        if proposal_id not in self.votes:
            # we dont need to any error handling here
            # if its invalid the transaction will fail
            arc4.abi_call(
                registry_contract.XGovRegistry.is_proposal,
                arc4.UInt64(proposal_id),
                app_id=self.registry_app_id.value,
            )

            self.votes[proposal_id] = typ.CouncilVotingBox(
                submitted=arc4.Bool(False),  # noqa: FBT003
                votes=arc4.DynamicArray(
                    typ.CouncilVote(
                        address=arc4.Address(Txn.sender),
                        approve=arc4.Bool(approve),  # noqa: FBT003
                    )
                )
            )
        else:
            assert not self.votes[proposal_id].submitted, err.VOTING_CLOSED

            for i in urange(self.votes[proposal_id].votes.length):
                assert Txn.sender != self.votes[proposal_id].votes[i].address, err.ALREADY_VOTED

            self.votes[proposal_id].votes.append(
                typ.CouncilVote(
                    address=arc4.Address(Txn.sender),
                    approve=arc4.Bool(approve),  # noqa: FBT003
                )
            )

    @arc4.abimethod()
    def submit(self, proposal_id: UInt64) -> None:
        """
        Submit the proposal review to the registry.

        Args:
            proposal_id: The ID of the proposal to submit.

        Raises:
            err.FORBIDDEN: If the sender is not a member of the council or admin.
            err.BAD_PROPOSAL_ID: If the proposal ID is invalid.
            err.ALREADY_SUBMITTED: If the proposal has already been submitted.
            err.FAILED_VOTE: If the proposal has not received enough votes to be submitted.
            
        """

        assert Txn.sender in self.members or Txn.sender == self.admin.value, err.FORBIDDEN
        assert proposal_id in self.votes, err.BAD_PROPOSAL_ID
        assert not self.votes[proposal_id].submitted, err.ALREADY_SUBMITTED

        approvals = UInt64(0)
        rejections = UInt64(0)

        for i in urange(self.votes[proposal_id].votes.length):
            if self.votes[proposal_id].votes[i].approve:
                approvals += 1
            else:
                rejections += 1

        halfPlusOne = (self.member_count.value // 2) + 1
        assert approvals >= halfPlusOne or rejections >= halfPlusOne, err.FAILED_VOTE
        block = (rejections >= halfPlusOne)

        arc4.abi_call(
            proposal_contract.Proposal.review,
            block,
            app_id=proposal_id
        )

        self.votes[proposal_id].submitted = arc4.Bool(True)