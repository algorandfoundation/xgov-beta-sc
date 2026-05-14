# This file is auto-generated, do not modify
# flake8: noqa
# fmt: off
import typing

import algopy

class ProposalTypedGlobalState(algopy.arc4.Struct):
    proposer: algopy.arc4.Address
    registry_app_id: algopy.arc4.UIntN[typing.Literal[64]]
    title: algopy.arc4.String
    open_ts: algopy.arc4.UIntN[typing.Literal[64]]
    submission_ts: algopy.arc4.UIntN[typing.Literal[64]]
    vote_open_ts: algopy.arc4.UIntN[typing.Literal[64]]
    status: algopy.arc4.UIntN[typing.Literal[64]]
    finalized: algopy.arc4.Bool
    funding_category: algopy.arc4.UIntN[typing.Literal[64]]
    focus: algopy.arc4.UIntN[typing.Literal[8]]
    funding_type: algopy.arc4.UIntN[typing.Literal[64]]
    requested_amount: algopy.arc4.UIntN[typing.Literal[64]]
    locked_amount: algopy.arc4.UIntN[typing.Literal[64]]
    committee_id: algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]]
    committee_members: algopy.arc4.UIntN[typing.Literal[64]]
    committee_votes: algopy.arc4.UIntN[typing.Literal[64]]
    voted_members: algopy.arc4.UIntN[typing.Literal[64]]
    boycotted_members: algopy.arc4.UIntN[typing.Literal[64]]
    approvals: algopy.arc4.UIntN[typing.Literal[64]]
    rejections: algopy.arc4.UIntN[typing.Literal[64]]
    nulls: algopy.arc4.UIntN[typing.Literal[64]]

class VotingState(algopy.arc4.Struct):
    quorum_voters: algopy.arc4.UIntN[typing.Literal[32]]
    weighted_quorum_votes: algopy.arc4.UIntN[typing.Literal[32]]
    total_voters: algopy.arc4.UIntN[typing.Literal[32]]
    total_boycott: algopy.arc4.UIntN[typing.Literal[32]]
    total_approvals: algopy.arc4.UIntN[typing.Literal[32]]
    total_rejections: algopy.arc4.UIntN[typing.Literal[32]]
    total_nulls: algopy.arc4.UIntN[typing.Literal[32]]
    quorum_reached: algopy.arc4.Bool
    weighted_quorum_reached: algopy.arc4.Bool
    majority_approved: algopy.arc4.Bool
    plebiscite: algopy.arc4.Bool

class Proposal(algopy.arc4.ARC4Client, typing.Protocol):
    """
    Proposal Contract
    """
    @algopy.arc4.abimethod(create='require')
    def create(
        self,
        proposer: algopy.arc4.Address,
    ) -> None:
        """
        Create a new proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.
        """

    @algopy.arc4.abimethod
    def open(
        self,
        payment: algopy.gtxn.PaymentTransaction,
        title: algopy.arc4.String,
        funding_type: algopy.arc4.UIntN[typing.Literal[64]],
        requested_amount: algopy.arc4.UIntN[typing.Literal[64]],
        focus: algopy.arc4.UIntN[typing.Literal[8]],
    ) -> None:
        """
        Open the first draft of the proposal.
        """

    @algopy.arc4.abimethod
    def upload_metadata(
        self,
        payload: algopy.arc4.DynamicBytes,
        is_first_in_group: algopy.arc4.Bool,
    ) -> None:
        """
        Upload the proposal metadata.
        """

    @algopy.arc4.abimethod
    def drop(
        self,
    ) -> algopy.arc4.String:
        """
        Drop the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.
        """

    @algopy.arc4.abimethod
    def submit(
        self,
    ) -> None:
        """
        submit the proposal.
        """

    @algopy.arc4.abimethod
    def assign_voters(
        self,
        voters: algopy.arc4.DynamicArray[algopy.arc4.Tuple[algopy.arc4.Address, algopy.arc4.UIntN[typing.Literal[64]]]],
    ) -> None:
        """
        Assign multiple voters to the proposal.
        """

    @algopy.arc4.abimethod
    def vote(
        self,
        voter: algopy.arc4.Address,
        approvals: algopy.arc4.UIntN[typing.Literal[64]],
        rejections: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> algopy.arc4.String:
        """
        Vote on the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.
        """

    @algopy.arc4.abimethod
    def scrutiny(
        self,
    ) -> None:
        """
        Scrutinize the proposal.
        """

    @algopy.arc4.abimethod
    def unassign_absentees(
        self,
        absentees: algopy.arc4.DynamicArray[algopy.arc4.Address],
    ) -> algopy.arc4.String:
        """
        Unassign absentees from the scrutinized proposal.
        """

    @algopy.arc4.abimethod
    def review(
        self,
        block: algopy.arc4.Bool,
    ) -> None:
        """
        Review the proposal.
        """

    @algopy.arc4.abimethod
    def fund(
        self,
    ) -> algopy.arc4.String:
        """
        Fund the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.
        """

    @algopy.arc4.abimethod
    def unassign_voters(
        self,
        voters: algopy.arc4.DynamicArray[algopy.arc4.Address],
    ) -> None:
        """
        Unassign voters from the submitted proposal. This method is an admin method
        to rollback and fix wrong committee assignments.
        """

    @algopy.arc4.abimethod
    def finalize(
        self,
    ) -> algopy.arc4.String:
        """
        Finalize the proposal. MUST BE CALLED BY THE REGISTRY CONTRACT.
        """

    @algopy.arc4.abimethod(allow_actions=['DeleteApplication'])
    def delete(
        self,
    ) -> None:
        """
        Delete the proposal.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_state(
        self,
    ) -> ProposalTypedGlobalState:
        """
        Get the proposal state.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_voter_box(
        self,
        voter_address: algopy.arc4.Address,
    ) -> algopy.arc4.Tuple[algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.Bool]:
        """
        Returns the Voter box for the given address.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_voting_state(
        self,
    ) -> VotingState:
        """
        Returns the voting state of the Proposal.
        """

    @algopy.arc4.abimethod
    def op_up(
        self,
    ) -> None: ...
