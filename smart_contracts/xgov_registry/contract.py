import typing as t

from algopy import (
    ARC4Contract,
    Application,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    itxn,
    subroutine,
    BoxMap,
    gtxn,
    Global,
    op,
    GlobalState,
    compile_contract,
    Account,
)

import smart_contracts.errors.std_errors as err
from . import config as cfg
from . import types as typ

from ..proposal import enums as penm
from ..proposal_mock import contract as proposal_contract
from ..proposal import config as pcfg
from ..proposal import types as ptyp

class XGovRegistry(
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

        # Initialize global state variables
        self.xgov_manager = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_MANAGER)
        self.xgov_payor = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_PAYOR)
        self.kyc_provider = GlobalState(arc4.Address(), key=cfg.GS_KEY_KYC_PROVIDER)
        self.committee_manager = GlobalState(arc4.Address(), key=cfg.GS_KEY_COMMITTEE_MANAGER)
        self.committee_publisher = GlobalState(arc4.Address(), key=cfg.GS_KEY_COMMITTEE_PUBLISHER)
        
        self.xgov_min_balance = GlobalState(UInt64(), key=cfg.GS_KEY_XGOV_MIN_BALANCE)
        self.proposer_fee = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSER_FEE)
        self.proposal_fee = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSAL_FEE)
        self.proposal_publishing_bps = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSAL_PUBLISHING_BPS)
        self.proposal_commitment_bps = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS)
        
        self.min_requested_amount = GlobalState(UInt64(), key=cfg.GS_KEY_MIN_REQUESTED_AMOUNT)

        self.max_requested_amount_small = GlobalState(UInt64(), key=cfg.GS_KEY_MAX_REQUESTED_AMOUNT_SMALL)
        self.max_requested_amount_medium = GlobalState(UInt64(), key=cfg.GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM)
        self.max_requested_amount_large = GlobalState(UInt64(), key=cfg.GS_KEY_MAX_REQUESTED_AMOUNT_LARGE)
        
        self.discussion_duration_small = GlobalState(UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_SMALL)
        self.discussion_duration_medium = GlobalState(UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_MEDIUM)
        self.discussion_duration_large = GlobalState(UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_LARGE)
        self.discussion_duration_xlarge = GlobalState(UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_XLARGE)
        
        self.voting_duration_small = GlobalState(UInt64(), key=cfg.GS_KEY_VOTING_DURATION_SMALL)
        self.voting_duration_medium = GlobalState(UInt64(), key=cfg.GS_KEY_VOTING_DURATION_MEDIUM)
        self.voting_duration_large = GlobalState(UInt64(), key=cfg.GS_KEY_VOTING_DURATION_LARGE)
        self.voting_duration_xlarge = GlobalState(UInt64(), key=cfg.GS_KEY_VOTING_DURATION_XLARGE)
        
        self.cool_down_duration = GlobalState(UInt64(), key=cfg.GS_KEY_COOL_DOWN_DURATION)
        
        self.quorum_small = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_SMALL)
        self.quorum_medium = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_MEDIUM)
        self.quorum_large = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_LARGE)
        
        self.weighted_quorum_small = GlobalState(UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_SMALL)
        self.weighted_quorum_medium = GlobalState(UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_MEDIUM)
        self.weighted_quorum_large = GlobalState(UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_LARGE)
        
        self.outstanding_funds = GlobalState(UInt64(), key=cfg.GS_KEY_OUTSTANDING_FUNDS)
        
        self.committee_id = GlobalState(arc4.StaticArray[arc4.Byte, t.Literal[32]], key=cfg.GS_KEY_COMMITTEE_ID)
        self.committee_members = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_MEMBERS)
        self.committee_votes = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_VOTES)

        self.pending_proposals = GlobalState(UInt64(), key=cfg.GS_KEY_PENDING_PROPOSALS)

        # boxes
        self.xgov_box = BoxMap(Account, arc4.Address, key_prefix=b"x")
        self.proposer_box = BoxMap(Account, typ.ProposerBoxValue, key_prefix=b"p")

    @subroutine
    def is_xgov_manager(self) -> bool:
        return Txn.sender == self.xgov_manager.value.native
    
    @subroutine
    def is_xgov_committee_manager(self) -> bool:
        return Txn.sender == self.committee_manager.value.native

    @subroutine
    def no_pending_proposals(self) -> bool:
        return self.pending_proposals.value == 0
    
    @subroutine
    def is_proposal(self, proposal_id: arc4.UInt64) -> bool:
        return Application(proposal_id.native).creator == Global.current_application_address
    
    @subroutine
    def disburse_funds(self, recipient: arc4.Address, amount: UInt64) -> None:
        # Transfer the funds to the receiver
        itxn.Payment(
            receiver=Account(recipient.bytes),
            amount=amount,
            fee=0,
        ).submit()

        # Update the outstanding funds
        self.outstanding_funds.value -= amount

    @arc4.abimethod(create="require")
    def create(self) -> None:
        """Create the xgov registry.

        Args:
            manager (arc4.Address): Address of the manager
            payor (arc4.Address): Address of the payor
            committee_manager (arc4.Address): Address of the committee manager
        """

        self.xgov_manager.value = arc4.Address(Txn.sender)

    @arc4.abimethod()
    def set_xgov_manager(self, manager: arc4.Address) -> None:
        """Sets the XGov manager.

        Args:
            manager (arc4.Address): Address of the new manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current XGov manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_manager.value = manager

    @arc4.abimethod()
    def set_kyc_provider(self, provider: arc4.Address) -> None:
        """Sets the KYC provider.

        Args:
            provider (arc4.Address): Address of the new provider

        Raises:
            err.UNAUTHORIZED: If the sender is not the current XGov manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.kyc_provider.value = provider

    @arc4.abimethod()
    def set_payor(self, payor: arc4.Address) -> None:
        """Sets the XGov payor.

        Args:
            payor (arc4.Address): Address of the new payor

        Raises:
            err.UNAUTHORIZED: If the sender is not the current XGov manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_payor.value = payor

    @arc4.abimethod()
    def set_committee_manager(self, manager: arc4.Address) -> None:
        """Sets the committee manager.

        Args:
            manager (arc4.Address): Address of the new manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current XGov manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.committee_manager.value = manager

    @arc4.abimethod()
    def set_committee_publisher(self, publisher: arc4.Address) -> None:
        """Sets the committee publisher.

        Args:
            publisher (arc4.Address): Address of the new publisher

        Raises:
            err.UNAUTHORIZED: If the sender is not the current XGov manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.committee_publisher.value = publisher

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
        """Sets the configurable global state keys of the registry.

        Args:
            config (arc4.Struct): Configuration class containing the field data

        Raises:
            err.UNAUTHORIZED: If the sender is not the current XGov manager
            err.NO_PENDING_PROPOSALS: If there are currently pending proposals
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert self.no_pending_proposals(), err.NO_PENDING_PROPOSALS
        
        self.xgov_min_balance.value = config.xgov_min_balance.native
        self.proposer_fee.value = config.proposer_fee.native
        self.proposal_fee.value = config.proposal_fee.native
        self.proposal_publishing_bps.value = config.proposal_publishing_bps.native
        self.proposal_commitment_bps.value = config.proposal_commitment_bps.native

        self.max_requested_amount_small.value = config.max_requested_amount[0].native
        self.max_requested_amount_medium.value = config.max_requested_amount[1].native
        self.max_requested_amount_large.value = config.max_requested_amount[2].native
        
        self.discussion_duration_small.value = config.discussion_duration[0].native
        self.discussion_duration_medium.value = config.discussion_duration[1].native
        self.discussion_duration_large.value = config.discussion_duration[2].native
        self.discussion_duration_xlarge.value = config.discussion_duration[3].native

        self.voting_duration_small.value = config.voting_duration[0].native
        self.voting_duration_medium.value = config.voting_duration[1].native
        self.voting_duration_large.value = config.voting_duration[2].native
        self.voting_duration_xlarge.value = config.voting_duration[3].native
        
        self.cool_down_duration.value = config.cool_down_duration.native
        
        self.quorum_small.value = config.quorum[0].native
        self.quorum_medium.value = config.quorum[1].native
        self.quorum_large.value = config.quorum[2].native
        
        self.weighted_quorum_small.value = config.weighted_quorum[0].native
        self.weighted_quorum_medium.value = config.weighted_quorum[1].native
        self.weighted_quorum_large.value = config.weighted_quorum[2].native

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_xgov_registry(self) -> None:
        """Updates the registry contract

        Raises:
            err.UNAUTHORIZED: If the sender is not the current XGov manager
            err.NO_PENDING_PROPOSALS: If there are currently pending proposals
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert self.no_pending_proposals(), err.NO_PENDING_PROPOSALS

    @arc4.abimethod()
    def subscribe_xgov(self, payment: gtxn.PaymentTransaction) -> None:
        """Subscribes the sender to being an XGov

        Args:
            payment (gtxn.PaymentTransaction): The payment transaction covering the signup MBR

        Raises:
            err.ALREADY_XGOV: If the sender is already an XGov
            err.WRONG_RECEIVER: If the recipient is not the registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment transaction is not equal to the xgov_min_balance global state key
        """

        assert not Txn.sender in self.xgov_box, err.ALREADY_XGOV
        # check payment
        assert payment.receiver == Global.current_application_address, err.WRONG_RECEIVER
        assert payment.amount == self.xgov_min_balance.value, err.WRONG_PAYMENT_AMOUNT

        # create box
        self.xgov_box[Txn.sender] = arc4.Address(Txn.sender)

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        """Unsubscribes the sender from being an XGov

        Raises:
            err.INSUFFICIENT_FEE: If the fee wont cover the inner transaction MBR refund
            err.UNAUTHORIZED: If the sender is not currently an XGov
        """

        # ensure they covered the itxn fee
        assert Txn.fee >= (Global.min_txn_fee * 2), err.INSUFFICIENT_FEE
        assert Txn.sender in self.xgov_box, err.UNAUTHORIZED

        # delete box
        del self.xgov_box[Txn.sender]

        # refund
        itxn.Payment(
            receiver=Txn.sender,
            amount=self.xgov_min_balance.value,
            fee=0,
        ).submit()

    @arc4.abimethod()
    def set_voting_account(self, xgov_address: arc4.Address, voting_address: arc4.Address) -> None:
        """Sets the voting account for the XGov

        Args:
            voting_address (arc4.Address): The voting account address to delegate voting power to

        Raises:
            err.UNAUTHORIZED: If the sender is not currently an XGov
            err.VOTING_ADDRESS_MUST_BE_DIFFERENT: If the new voting account is the same as currently set
        """

        # Check if the sender is an xGov member
        old_voting_address, exists = self.xgov_box.maybe(xgov_address.native)
        assert exists, err.UNAUTHORIZED

        # Check that the sender is either the xgov or the voting address
        assert Txn.sender == old_voting_address or Txn.sender == xgov_address, err.UNAUTHORIZED

        # Update the voting account in the xGov box
        self.xgov_box[xgov_address.native] = voting_address

    @arc4.abimethod()
    def subscribe_proposer(self, payment: gtxn.PaymentTransaction) -> None:
        """Subscribes the sender to being an proposer

        Args:
            payment (gtxn.PaymentTransaction): The payment transaction covering the proposer fee

        Raises:
            err.ALREADY_PROPOSER: If the sender is already a proposer
            err.WRONG_RECEIVER: If the recipient is not the registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment transaction is not equal to the proposer_fee global state key
        """

        assert not Txn.sender in self.proposer_box, err.ALREADY_PROPOSER
        # check fee
        assert payment.receiver == Global.current_application_address, err.WRONG_RECEIVER
        assert payment.amount == self.proposer_fee.value, err.WRONG_PAYMENT_AMOUNT

        self.proposer_box[Txn.sender] = typ.ProposerBoxValue(
            active_proposal=arc4.Bool(False),
            kyc_status=arc4.Bool(False),
            kyc_expiring=arc4.UInt64(0),
        )

    @arc4.abimethod()
    def set_proposer_kyc(self, proposer: arc4.Address, kyc_status: arc4.Bool, kyc_expiring: arc4.UInt64) -> None:
        """Sets a proposer's KYC status

        Args:
            proposer (arc4.Address): The address of the proposer
            kyc_status (arc4.Bool): The new status of the proposer
            kyc_expiring (arc4.UInt64): The expiration date as a unix timestamp of the time the KYC expires

        Raises:
            err.UNAUTHORIZED: If the sender is not the KYC Provider
            err.PROPOSER_DOES_NOT_EXIST: If the referenced address is not a proposer
        """

        # check if kyc provider
        assert Txn.sender == self.kyc_provider.value.native, err.UNAUTHORIZED
        assert proposer.native in self.proposer_box, err.PROPOSER_DOES_NOT_EXIST

        active_proposal = self.proposer_box[proposer.native].copy().active_proposal

        self.proposer_box[proposer.native] = typ.ProposerBoxValue(
            active_proposal=active_proposal,
            kyc_status=kyc_status,
            kyc_expiring=kyc_expiring
        )

    @arc4.abimethod()
    def declare_committee(
        self,
        id: ptyp.CommitteeId,
        size: UInt64,
        votes: UInt64
    ) -> None:
        """Sets the committee details

        Args:
            id (ptyp.CommitteeId): The id of the commitee
            size (UInt64): The size of the committee
            votes (UInt64): The voting power of the committee

        Raises:
            err.UNAUTHORIZED: If the sender is not the XGov manager
        """

        assert self.is_xgov_committee_manager(), err.UNAUTHORIZED

        self.committee_id.value = id.copy()
        self.committee_members.value = size
        self.committee_votes.value = votes

    @arc4.abimethod
    def open_proposal(self, payment: gtxn.PaymentTransaction) -> UInt64:
        """Creates a new Proposal

        Args:
            payment (gtxn.PaymentTransaction): payment for covering the proposal fee & child contract MBR

        Raises:
            err.UNAUTHORIZED: If the sender is not a proposer
            err.ALREADY_ACTIVE_PROPOSAL: If the proposer already has an active proposal
            err.INVALID_KYC: If the proposer does not have valid KYC
            err.EXPIRED_KYC: If the proposers KYC is expired
            err.INSUFFICIENT_FEE: If the fee for the current transaction doesnt cover the inner transaction fees
            err.WRONG_RECEIVER: If the recipient is not the registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment amount doesnt match the proposal fee
        """

        # Check if the caller is a registered proposer
        assert Txn.sender in self.proposer_box, err.UNAUTHORIZED

        proposer_state = self.proposer_box[Txn.sender].copy()

        # Check if the proposer already has an active proposal
        assert not proposer_state.active_proposal, err.ALREADY_ACTIVE_PROPOSAL
        assert proposer_state.kyc_status, err.INVALID_KYC
        assert proposer_state.kyc_expiring, err.EXPIRED_KYC

        assert Txn.fee >= (Global.min_txn_fee * 3), err.INSUFFICIENT_FEE

        # Ensure the transaction has the correct payment
        assert payment.receiver == Global.current_application_address, err.WRONG_RECEIVER
        assert payment.amount == self.proposal_fee.value, err.WRONG_PAYMENT_AMOUNT

        # Create the Proposal App
        # TODO: replace the proposal mock contract with the real one
        compiled = compile_contract(proposal_contract.ProposalMock)
        proposal_app = (
            itxn.ApplicationCall(
                app_args=(arc4.arc4_signature("create(address)void"), Txn.sender),
                approval_program=compiled.approval_program,
                clear_state_program=compiled.clear_state_program,
                global_num_bytes=pcfg.GLOBAL_BYTES,
                global_num_uint=pcfg.GLOBAL_UINTS,
                local_num_bytes=pcfg.LOCAL_BYTES,
                local_num_uint=pcfg.LOCAL_UINTS,
                fee=0
            )
            .submit()
            .created_app
        )

        # Update proposer state
        self.proposer_box[Txn.sender].active_proposal = arc4.Bool(True)

        # Transfer funds to the new Proposal App
        itxn.Payment(
            receiver=proposal_app.address,
            amount=self.proposal_fee.value - cfg.PROPOSAL_MBR,
            fee=0,
        ).submit()

        # Increment pending proposals
        self.pending_proposals.value += 1

        return proposal_app.id

    @arc4.abimethod()
    def vote_proposal(self, proposal_id: arc4.UInt64, xgov_address: arc4.Address, approval_votes: UInt64, rejection_votes: UInt64, null_votes: UInt64) -> None:
        """Votes on a proposal

        Args:
            proposal_id (arc4.UInt64): The application id of the proposal app being voted on
            xgov_address: (arc4.Address): The address of the xgov being voted on behalf of
            approval_votes: (UInt64): The number of approvals from the xgov allocated
            down_votes: (UInt64): The number of rejections from the xgov allocated
            
        Raises:
            err.INVALID_VOTE: If the votes amount to more than the voting power of the committee
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.UNAUTHORIZED: If the xgov_address is not an XGov
            err.MUST_BE_VOTING_ADDRESS: If the sender is not the voting_address
        """

        # verify proposal id is genuine proposal
        assert self.is_proposal(proposal_id), err.INVALID_PROPOSAL
        
        # Verify the proposal is in the approved state
        status, status_exists = op.AppGlobal.get_ex_uint64(proposal_id.native, pcfg.GS_KEY_STATUS)
        assert status == UInt64(penm.STATUS_VOTING), err.PROPOSAL_IS_NOT_VOTING

        # verify their voting allocation is not more than allowed
        # and allocate any remaining votes to null
        vote_sum = (approval_votes + rejection_votes + null_votes)
        proposal_committee_votes, proposal_committee_votes_exists = op.AppGlobal.get_ex_uint64(proposal_id.native, pcfg.GS_KEY_COMMITTEE_VOTES)
        assert vote_sum <= proposal_committee_votes, err.INVALID_VOTE
        extra_null_votes = proposal_committee_votes - vote_sum
        null_votes += extra_null_votes

        # make sure they're voting on behalf of an xgov
        voting_address, exists = self.xgov_box.maybe(xgov_address.native)
        assert exists, err.UNAUTHORIZED

        # Verify the caller is using their voting address
        assert Txn.sender == voting_address.native, err.MUST_BE_VOTING_ADDRESS

        # Call the Proposal App to register the vote
        arc4.abi_call(
            proposal_contract.ProposalMock.vote,
            xgov_address,
            approval_votes,
            rejection_votes,
            null_votes,
            app_id=proposal_id.native
        )

    @arc4.abimethod()
    def pay_grant_proposal(self, proposal_id: arc4.UInt64) -> None:
        """Disburses the funds for an approved proposal

        Args:
            proposal_id (arc4.UInt64): The application id of the approved proposal
            
        Raises:
            err.UNAUTHORIZED: If the sender is not the xgov_payor
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.PROPOSAL_IS_NOT_APPROVED: If the proposals status is not Approved
            err.WRONG_PROPOSER: If the proposer on the proposal is not found
            err.INVALID_KYC: If the proposer is not KYC'd
            err.EXPIRED_KYC: If the proposers KYC is expired
            err.INSUFFICIENT_TREASURY_FUNDS: If the registry does not have enough funds for the disbursement
        """

        # Verify the caller is the xGov Payor
        assert arc4.Address(Txn.sender) == self.xgov_payor.value, err.UNAUTHORIZED

        # Verify proposal_id is a genuine proposal created by this registry
        assert self.is_proposal(proposal_id), err.INVALID_PROPOSAL

        # Read proposal state directly from the Proposal App's global state
        status, status_exists = op.AppGlobal.get_ex_uint64(proposal_id.native, pcfg.GS_KEY_STATUS)
        proposer_bytes, proposer_exists = op.AppGlobal.get_ex_bytes(proposal_id.native, pcfg.GS_KEY_PROPOSER)
        proposer = arc4.Address(proposer_bytes)
        requested_amount, requested_amount_exists = op.AppGlobal.get_ex_uint64(proposal_id.native, pcfg.GS_KEY_REQUESTED_AMOUNT)
        # Verify the proposal is in the approved state
        assert status == UInt64(penm.STATUS_APPROVED), err.PROPOSAL_IS_NOT_APPROVED

        assert proposer.native in self.proposer_box, err.WRONG_PROPOSER

        # Verify the proposer's KYC is still valid
        proposer_state = self.proposer_box[proposer.native].copy()
        
        assert proposer_state.kyc_status, err.INVALID_KYC
        assert proposer_state.kyc_expiring > Global.latest_timestamp, err.EXPIRED_KYC

        # Verify sufficient funds are available
        assert self.outstanding_funds.value >= requested_amount, err.INSUFFICIENT_TREASURY_FUNDS

        self.disburse_funds(proposer, requested_amount)
        
        arc4.abi_call(
            "release_funds",
            app_id=proposal_id.native
        )

        # Decrement pending proposals count
        self.pending_proposals.value -= 1

        # Update proposer's active proposal status
        self.proposer_box[proposer.native] = typ.ProposerBoxValue(
            active_proposal=arc4.Bool(False),
            kyc_status=proposer_state.kyc_status,
            kyc_expiring=proposer_state.kyc_expiring
        )

    @arc4.abimethod()
    def deposit_funds(self, payment: gtxn.PaymentTransaction) -> None:
        """Tracks deposits to the treasury

        Args:
            payment (gtxn.PaymentTransaction): the deposit transaction
            
        Raises:
            err.UNAUTHORIZED: If the sender is not the XGov manager
            err.WRONG_RECEIVER: If the recipient is not the treasury
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert payment.receiver == Global.current_application_address, err.WRONG_RECEIVER
        self.outstanding_funds.value += payment.amount

    @arc4.abimethod()
    def withdraw_funds(self, amount: UInt64) -> None:
        """Remove funds from the treasury

        Args:
            amount (UInt64): the amount to remove
            
        Raises:
            err.UNAUTHORIZED: If the sender is not the XGov manager
            err.INSUFFICIENT_FUNDS: If the requested amount is greater than the outstanding funds available
            err.INSUFFICIENT_FEE: If the fee is not enough to cover the inner transaction to send the funds back
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert amount <= self.outstanding_funds.value, err.INSUFFICIENT_FUNDS
        assert Txn.fee >= (Global.min_txn_fee * 2), err.INSUFFICIENT_FEE
        self.outstanding_funds.value -= amount
        
        itxn.Payment(
            receiver=self.xgov_manager.value.native,
            amount=amount,
            fee=0,
        ).submit()

    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.TypedGlobalState:
        """Returns the global state of the applicaton"""

        return typ.TypedGlobalState(
            xgov_manager=self.xgov_manager.value,
            xgov_payor=self.xgov_payor.value,
            kyc_provider=self.kyc_provider.value,
            committee_manager=self.committee_manager.value,
            committee_publisher=self.committee_publisher.value,
            xgov_min_balance=arc4.UInt64(self.xgov_min_balance.value),
            proposer_fee=arc4.UInt64(self.proposer_fee.value),
            proposal_fee=arc4.UInt64(self.proposal_fee.value),
            proposal_publishing_bps=arc4.UInt64(self.proposal_publishing_bps.value),
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
                arc4.UInt64(self.discussion_duration_xlarge.value),
            ),
            voting_duration=arc4.StaticArray[arc4.UInt64, t.Literal[4]](
                arc4.UInt64(self.voting_duration_small.value),
                arc4.UInt64(self.voting_duration_medium.value),
                arc4.UInt64(self.voting_duration_large.value),
                arc4.UInt64(self.voting_duration_xlarge.value),
            ),
            cool_down_duration=arc4.UInt64(self.cool_down_duration.value),
            quorum=arc4.StaticArray[arc4.UInt64, t.Literal[3]](
                arc4.UInt64(self.quorum_small.value),
                arc4.UInt64(self.quorum_medium.value),
                arc4.UInt64(self.quorum_large.value),
            ),
            weighted_quorum=arc4.StaticArray[arc4.UInt64, t.Literal[3]](
                arc4.UInt64(self.weighted_quorum_small.value),
                arc4.UInt64(self.weighted_quorum_medium.value),
                arc4.UInt64(self.weighted_quorum_large.value),
            ),
            outstanding_funds=arc4.UInt64(self.outstanding_funds.value),
            pending_proposals=arc4.UInt64(self.pending_proposals.value),
            committee_id=self.committee_id.value.copy(),
            committee_members=arc4.UInt64(self.committee_members.value),
            committee_votes=arc4.UInt64(self.committee_votes.value)
        )
