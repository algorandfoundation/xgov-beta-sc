# This file is auto-generated, do not modify
# flake8: noqa
# fmt: off
import typing

import algopy

class XGovRegistryConfig(algopy.arc4.Struct):
    xgov_fee: algopy.arc4.UIntN[typing.Literal[64]]
    proposer_fee: algopy.arc4.UIntN[typing.Literal[64]]
    open_proposal_fee: algopy.arc4.UIntN[typing.Literal[64]]
    daemon_ops_funding_bps: algopy.arc4.UIntN[typing.Literal[64]]
    proposal_commitment_bps: algopy.arc4.UIntN[typing.Literal[64]]
    min_requested_amount: algopy.arc4.UIntN[typing.Literal[64]]
    max_requested_amount: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[3]]
    discussion_duration: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[4]]
    voting_duration: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[4]]
    quorum: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[3]]
    weighted_quorum: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[3]]
    absence_tolerance: algopy.arc4.UIntN[typing.Literal[64]]
    governance_period: algopy.arc4.UIntN[typing.Literal[64]]
    committee_grace_period: algopy.arc4.UIntN[typing.Literal[64]]

class TypedGlobalState(algopy.arc4.Struct):
    paused_registry: algopy.arc4.Bool
    paused_proposals: algopy.arc4.Bool
    xgov_manager: algopy.arc4.Address
    xgov_payor: algopy.arc4.Address
    xgov_council: algopy.arc4.Address
    xgov_subscriber: algopy.arc4.Address
    kyc_provider: algopy.arc4.Address
    committee_manager: algopy.arc4.Address
    xgov_daemon: algopy.arc4.Address
    xgov_fee: algopy.arc4.UIntN[typing.Literal[64]]
    proposer_fee: algopy.arc4.UIntN[typing.Literal[64]]
    open_proposal_fee: algopy.arc4.UIntN[typing.Literal[64]]
    daemon_ops_funding_bps: algopy.arc4.UIntN[typing.Literal[64]]
    proposal_commitment_bps: algopy.arc4.UIntN[typing.Literal[64]]
    min_requested_amount: algopy.arc4.UIntN[typing.Literal[64]]
    max_requested_amount: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[3]]
    discussion_duration: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[4]]
    voting_duration: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[4]]
    quorum: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[3]]
    weighted_quorum: algopy.arc4.StaticArray[algopy.arc4.UIntN[typing.Literal[64]], typing.Literal[3]]
    outstanding_funds: algopy.arc4.UIntN[typing.Literal[64]]
    pending_proposals: algopy.arc4.UIntN[typing.Literal[64]]
    committee_id: algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]]
    committee_members: algopy.arc4.UIntN[typing.Literal[64]]
    committee_votes: algopy.arc4.UIntN[typing.Literal[64]]
    absence_tolerance: algopy.arc4.UIntN[typing.Literal[64]]
    governance_period: algopy.arc4.UIntN[typing.Literal[64]]
    committee_grace_period: algopy.arc4.UIntN[typing.Literal[64]]
    committee_last_anchor: algopy.arc4.UIntN[typing.Literal[64]]

class XGovRegistry(algopy.arc4.ARC4Client, typing.Protocol):
    """
    xGov Registry Contract
    """
    @algopy.arc4.abimethod(create='require')
    def create(
        self,
    ) -> None:
        """
        Create the xGov Registry.
        """

    @algopy.arc4.abimethod
    def init_proposal_contract(
        self,
        size: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Initializes the Proposal Approval Program contract.
        """

    @algopy.arc4.abimethod
    def load_proposal_contract(
        self,
        offset: algopy.arc4.UIntN[typing.Literal[64]],
        data: algopy.arc4.DynamicBytes,
    ) -> None:
        """
        Loads the Proposal Approval Program contract.
        """

    @algopy.arc4.abimethod
    def delete_proposal_contract_box(
        self,
    ) -> None:
        """
        Deletes the Proposal Approval Program contract box.
        """

    @algopy.arc4.abimethod
    def pause_registry(
        self,
    ) -> None:
        """
        Pauses the xGov Registry non-administrative methods.
        """

    @algopy.arc4.abimethod
    def pause_proposals(
        self,
    ) -> None:
        """
        Pauses the creation of new Proposals.
        """

    @algopy.arc4.abimethod
    def resume_registry(
        self,
    ) -> None:
        """
        Resumes the xGov Registry non-administrative methods.
        """

    @algopy.arc4.abimethod
    def resume_proposals(
        self,
    ) -> None:
        """
        Resumes the creation of new Proposals.
        """

    @algopy.arc4.abimethod
    def set_xgov_manager(
        self,
        manager: algopy.arc4.Address,
    ) -> None:
        """
        Sets the xGov Manager.
        """

    @algopy.arc4.abimethod
    def set_payor(
        self,
        payor: algopy.arc4.Address,
    ) -> None:
        """
        Sets the xGov Payor.
        """

    @algopy.arc4.abimethod
    def set_xgov_council(
        self,
        council: algopy.arc4.Address,
    ) -> None:
        """
        Sets the xGov Council.
        """

    @algopy.arc4.abimethod
    def set_xgov_subscriber(
        self,
        subscriber: algopy.arc4.Address,
    ) -> None:
        """
        Sets the xGov Subscriber.
        """

    @algopy.arc4.abimethod
    def set_kyc_provider(
        self,
        provider: algopy.arc4.Address,
    ) -> None:
        """
        Sets the KYC provider.
        """

    @algopy.arc4.abimethod
    def set_committee_manager(
        self,
        manager: algopy.arc4.Address,
    ) -> None:
        """
        Sets the Committee Manager.
        """

    @algopy.arc4.abimethod
    def set_xgov_daemon(
        self,
        xgov_daemon: algopy.arc4.Address,
    ) -> None:
        """
        Sets the xGov Daemon.
        """

    @algopy.arc4.abimethod
    def config_xgov_registry(
        self,
        config: XGovRegistryConfig,
    ) -> None:
        """
        Sets the configuration of the xGov Registry.
        """

    @algopy.arc4.abimethod(allow_actions=['UpdateApplication'])
    def update_xgov_registry(
        self,
    ) -> None:
        """
        Updates the xGov Registry contract.
        """

    @algopy.arc4.abimethod
    def subscribe_xgov(
        self,
        voting_address: algopy.arc4.Address,
        payment: algopy.gtxn.PaymentTransaction,
    ) -> None:
        """
        Subscribes the sender to being an xGov.
        """

    @algopy.arc4.abimethod
    def unsubscribe_xgov(
        self,
    ) -> None:
        """
        Unsubscribes the sender from being an xGov.
        """

    @algopy.arc4.abimethod
    def unsubscribe_absentee(
        self,
        xgov_address: algopy.arc4.Address,
    ) -> None:
        """
        Unsubscribes an absentee xGov. This is a temporary method used only for the
        first absentees removal at the inception of the absenteeism penalty.
        """

    @algopy.arc4.abimethod
    def request_subscribe_xgov(
        self,
        xgov_address: algopy.arc4.Address,
        owner_address: algopy.arc4.Address,
        relation_type: algopy.arc4.UIntN[typing.Literal[64]],
        payment: algopy.gtxn.PaymentTransaction,
    ) -> None:
        """
        Requests to subscribe to the xGov.
        """

    @algopy.arc4.abimethod
    def approve_subscribe_xgov(
        self,
        request_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Approves a subscribe request to xGov.
        """

    @algopy.arc4.abimethod
    def reject_subscribe_xgov(
        self,
        request_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Rejects a subscribe request to xGov.
        """

    @algopy.arc4.abimethod
    def request_unsubscribe_xgov(
        self,
        xgov_address: algopy.arc4.Address,
        owner_address: algopy.arc4.Address,
        relation_type: algopy.arc4.UIntN[typing.Literal[64]],
        payment: algopy.gtxn.PaymentTransaction,
    ) -> None:
        """
        Requests to unsubscribe from the xGov.
        """

    @algopy.arc4.abimethod
    def approve_unsubscribe_xgov(
        self,
        request_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Approves a request to unsubscribe from xGov.
        """

    @algopy.arc4.abimethod
    def reject_unsubscribe_xgov(
        self,
        request_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Rejects a request to unsubscribe from xGov.
        """

    @algopy.arc4.abimethod
    def set_voting_account(
        self,
        xgov_address: algopy.arc4.Address,
        voting_address: algopy.arc4.Address,
    ) -> None:
        """
        Sets the Voting Address for the xGov.
        """

    @algopy.arc4.abimethod
    def subscribe_proposer(
        self,
        payment: algopy.gtxn.PaymentTransaction,
    ) -> None:
        """
        Subscribes the sender to being a Proposer.
        """

    @algopy.arc4.abimethod
    def set_proposer_kyc(
        self,
        proposer: algopy.arc4.Address,
        kyc_status: algopy.arc4.Bool,
        kyc_expiring: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Sets a proposer's KYC status.
        """

    @algopy.arc4.abimethod
    def declare_committee(
        self,
        committee_id: algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]],
        size: algopy.arc4.UIntN[typing.Literal[64]],
        votes: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Sets the xGov Committee in charge.
        """

    @algopy.arc4.abimethod
    def open_proposal(
        self,
        payment: algopy.gtxn.PaymentTransaction,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Creates a new Proposal.
        """

    @algopy.arc4.abimethod
    def vote_proposal(
        self,
        proposal_id: algopy.arc4.UIntN[typing.Literal[64]],
        xgov_address: algopy.arc4.Address,
        approval_votes: algopy.arc4.UIntN[typing.Literal[64]],
        rejection_votes: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Votes on a Proposal.
        """

    @algopy.arc4.abimethod
    def unassign_absentee_from_proposal(
        self,
        proposal_id: algopy.arc4.UIntN[typing.Literal[64]],
        absentees: algopy.arc4.DynamicArray[algopy.arc4.Address],
    ) -> None:
        """
        Unassign absentees from a scrutinized Proposal.
        """

    @algopy.arc4.abimethod
    def pay_grant_proposal(
        self,
        proposal_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Disburses the funds for an approved Proposal.
        """

    @algopy.arc4.abimethod
    def finalize_proposal(
        self,
        proposal_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Finalize a Proposal.
        """

    @algopy.arc4.abimethod
    def drop_proposal(
        self,
        proposal_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Drops a Proposal.
        """

    @algopy.arc4.abimethod
    def deposit_funds(
        self,
        payment: algopy.gtxn.PaymentTransaction,
    ) -> None:
        """
        Deposits xGov program funds into the xGov Treasury (xGov Registry Account).
        """

    @algopy.arc4.abimethod
    def withdraw_funds(
        self,
        amount: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Remove xGov program funds from the xGov Treasury (xGov Registry Account).
        """

    @algopy.arc4.abimethod
    def withdraw_available_funds(
        self,
        amount: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Withdraw the available balance (excluding MBR and Proposals funds) from the xGov Registry.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_available_funds(
        self,
    ) -> algopy.arc4.UIntN[typing.Literal[64]]:
        """
        Get the available funds (excluding MBR and Proposals funds)
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_state(
        self,
    ) -> TypedGlobalState:
        """
        Returns the xGov Registry state.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_xgov_box(
        self,
        xgov_address: algopy.arc4.Address,
    ) -> algopy.arc4.Tuple[algopy.arc4.Tuple[algopy.arc4.Address, algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]], algopy.arc4.UIntN[typing.Literal[64]]], algopy.arc4.Bool]:
        """
        Returns the xGov box for the given address.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_proposer_box(
        self,
        proposer_address: algopy.arc4.Address,
    ) -> algopy.arc4.Tuple[algopy.arc4.Tuple[algopy.arc4.Bool, algopy.arc4.Bool, algopy.arc4.UIntN[typing.Literal[64]]], algopy.arc4.Bool]:
        """
        Returns the Proposer box for the given address.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_request_box(
        self,
        request_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> algopy.arc4.Tuple[algopy.arc4.Tuple[algopy.arc4.Address, algopy.arc4.Address, algopy.arc4.UIntN[typing.Literal[64]]], algopy.arc4.Bool]:
        """
        Returns the xGov subscribe request box for the given request ID.
        """

    @algopy.arc4.abimethod(readonly=True)
    def get_request_unsubscribe_box(
        self,
        request_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> algopy.arc4.Tuple[algopy.arc4.Tuple[algopy.arc4.Address, algopy.arc4.Address, algopy.arc4.UIntN[typing.Literal[64]]], algopy.arc4.Bool]:
        """
        Returns the xGov unsubscribe request box for the given unsubscribe request ID.
        """

    @algopy.arc4.abimethod
    def is_proposal(
        self,
        proposal_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None: ...

    @algopy.arc4.abimethod
    def op_up(
        self,
    ) -> None: ...
