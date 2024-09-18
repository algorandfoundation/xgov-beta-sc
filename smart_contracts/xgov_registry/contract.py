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
from . import constants as const
from . import enums as enm
from . import types as typ

from ..proposal import enums as proposal_enm
from ..proposal import contract as proposal_contract
from ..proposal import config as proposal_config

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
        self.xgov_box = BoxMap(arc4.Address, typ.XgovBoxValue, key_prefix="x")
        self.proposer_box = BoxMap(arc4.Address, typ.ProposerBoxValue, key_prefix="p")

    @subroutine
    def is_xgov_manager(self) -> bool:
        return Txn.sender == self.xgov_manager

    @subroutine
    def no_pending_proposals(self) -> bool:
        return self.pending_proposals == UInt64(0)
    
    @subroutine
    def disburse_funds(self, recipient: arc4.Address, amount: UInt64) -> None:
        # Transfer the funds to the receiver
        itxn.Payment(
            receiver=Account(recipient.bytes),
            amount=amount,
            fee=0,
        ).submit()

        # Update the outstanding funds
        self.outstanding_funds.value = (self.outstanding_funds.value - amount)

    @arc4.abimethod(create="require")
    def create(self, manager: arc4.Address, payor: arc4.Address, comittee_manager: arc4.Address) -> None:
        """Create the xgov registry.

        Args:
            manager (arc4.Address): Address of the manager
            payor (arc4.Address): Address of the payor
            committee_manager (arc4.Address): Address of the committee manager
        """
        assert (
            Global.caller_application_id != 0
        ), err.UNAUTHORIZED  # Only callable by another contract

        self.xgov_manager.value = manager
        self.xgov_payor.value = payor
        self.committee_manager.value = comittee_manager


    @arc4.abimethod()
    def set_xgov_manager(self, new_manager: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set new manager"
        self.xgov_manager.value = new_manager

    @arc4.abimethod()
    def set_kyc_provider(self, new_provider: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set KYC Provider"
        self.kyc_provider.value = new_provider

    @arc4.abimethod()
    def set_payor(self, new_payor: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set KYC Provider"
        self.xgov_payor.value = new_payor

    @arc4.abimethod()
    def set_publisher(self, new_publisher: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set Publisher"
        self.committee_publisher.value = new_publisher

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can configure registry"
        assert self.no_pending_proposals(), "Cannot configure with pending proposals"
        
        self.xgov_min_balance.value = config.xgov_min_balance
        self.proposer_fee.value = config.proposer_fee
        self.proposal_fee.value = config.proposal_fee

        self.max_requested_amount_small.value = config.max_req_amount[0]
        self.max_requested_amount_medium.value = config.max_req_amount[1]
        self.max_requested_amount_large.value = config.max_req_amount[2]
        
        self.discussion_duration_small.value = config.discussion_duration[0]
        self.discussion_duration_medium.value = config.discussion_duration[1]
        self.discussion_duration_large.value = config.discussion_duration[2]
        self.discussion_duration_xlarge.value = config.discussion_duration[3]

        self.voting_duration_small.value = config.voting_duration[0]
        self.voting_duration_medium.value = config.voting_duration[1]
        self.voting_duration_large.value = config.voting_duration[2]
        self.voting_duration_xlarge.value = config.voting_duration[3]
        
        self.cool_down_duration.value = config.cool_down_duration
        
        self.quorum_small.value = config.quorum[0]
        self.quorum_medium.value = config.quorum[1]
        self.quorum_large.value = config.quorum[2]
        
        self.weighted_quorum_small.value = config.weighted_quorum[0]
        self.weighted_quorum_medium.value = config.weighted_quorum[1]
        self.weighted_quorum_large.value = config.weighted_quorum[2]

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_xgov_registry(self) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can update registry"
        assert self.no_pending_proposals(), "Cannot update with pending proposals"

    @arc4.abimethod()
    def subscribe_xgov(self, pmt: gtxn.PaymentTransaction) -> None:
        # check if already an xGov
        xgov = arc4.Address(Txn.sender)
        _, exists = self.xgov_box.maybe(xgov)
        assert not exists, "Already an xGov"

        # check payment
        assert pmt.receiver == Global.current_application_address, "Payment must be to current application"
        assert pmt.amount == self.xgov_min_balance, "Incorrect payment amount"

        # create box
        self.xgov_box[xgov] = typ.XgovBoxValue(
            voting_addr=xgov
        )

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        # ensure they covered the itxn fee
        assert Txn.fee >= (Global.min_txn_fee * UInt64(2)), "Fee must cover refund payment"

        xgov = arc4.Address(Txn.sender)
        # check if xGov
        _, exists = self.xgov_box.maybe(xgov)
        assert exists, "Not an xGov"

        # delete box
        del self.xgov_box[xgov]

        # refund
        itxn.Payment(
            receiver=Txn.sender,
            amount=self.xgov_min_balance.value,
            fee=UInt64(0),
        ).submit()

    @arc4.abimethod()
    def set_voting_account(self, voting_account: arc4.Address) -> None:
        # Check if the sender is an xGov member
        xgov = arc4.Address(Txn.sender)
        xgov_value, is_xgov = self.xgov_box.maybe(xgov)
        assert is_xgov, "Only xGov members can set a voting account"

        # Check that the voting account is different from the current voting account
        assert xgov_value.voting_addr != voting_account, "Voting account must be different from the current voting account"

        # Update the voting account in the xGov box
        self.xgov_box[xgov] = typ.XgovBoxValue(
            voting_addr=voting_account
        )

    @arc4.abimethod()
    def subscribe_proposer(self, pmt: gtxn.PaymentTransaction) -> None:

        xgov = arc4.Address(Txn.sender)
        _, exists = self.proposer_box.maybe(xgov)
        assert not exists, "Already a proposer"

        # check fee
        assert pmt.receiver == Global.current_application_address, "Payment must be to current application"
        assert pmt.amount == self.proposer_fee, "Incorrect payment amount"

        self.proposer_box[xgov] = typ.ProposerBoxValue(
            active_proposal=arc4.Bool(False),
            kyc_status=arc4.Bool(False),
            kyc_expiring=UInt64(0),
        )

    @arc4.abimethod()
    def set_proposer_kyc(self, proposer: arc4.Address, kyc_status: arc4.Bool, kyc_expiring: UInt64) -> None:
        # check if kyc provider
        assert Txn.sender == self.kyc_provider, "Only KYC Provider can validate KYC"
        
        box_value, exists = self.proposer_box.maybe(proposer)
        assert exists, "Proposer does not exist"

        box_value.kyc_status = kyc_status
        box_value.kyc_expiring = kyc_expiring
        self.proposer_box[proposer] = box_value

    @arc4.abimethod
    def open_proposal(self, pmt: gtxn.PaymentTransaction) -> UInt64:
        # Check if the caller is a registered proposer
        proposer = arc4.Address(Txn.sender)
        proposer_state, exists = self.proposer_box.maybe(proposer)
        assert exists, "Not a proposer"

        # Check if the proposer already has an active proposal
        assert not proposer_state.active_proposal, "Proposer already has an active proposal"
        
        assert Txn.fee >= Global.min_txn_fee * UInt64(3), "Insufficient fee"

        # Ensure the transaction has the correct payment
        assert pmt.amount == self.proposal_fee, "Insufficient payment"
        assert pmt.receiver == Global.current_application_address, "Payment must be to current application"

        # Create the Proposal App
        compiled = compile_contract(proposal_contract.Proposal)
        proposal_app = (
            itxn.ApplicationCall(
                app_args=(arc4.arc4_signature("create(address)void"), Txn.sender),
                approval_program=compiled.approval_program,
                clear_state_program=compiled.clear_state_program,
                global_num_bytes=proposal_config.GLOBAL_BYTES,
                global_num_uint=proposal_config.GLOBAL_UINTS,
                local_num_bytes=proposal_config.LOCAL_BYTES,
                local_num_uint=proposal_config.LOCAL_UINTS,
                fee=0
            )
            .submit()
            .created_app
        )

        # Update proposer state
        proposer_state.active_proposal = arc4.Bool(True)
        self.proposer_box[proposer] = proposer_state

        # Transfer funds to the new Proposal App
        itxn.Payment(
            receiver=proposal_app.address,
            amount=self.proposal_fee.value,
            fee=0,
        ).submit()

        # Increment pending proposals
        self.pending_proposals.value += UInt64(1)

        return proposal_app.id

    @arc4.abimethod()
    def vote_proposal(self, proposal_id: Application, vote: UInt64, vote_amount: UInt64) -> None:

        # ensure a voting enum is being used
        assert vote < UInt64(3), "Vote must be of Null, Approve, or Reject"

        # Verify the caller is an xGov member
        xgov = arc4.Address(Txn.sender)
        xgov_box, exists = self.xgov_box.maybe(xgov)
        assert exists, "Caller is not an xGov member"

        # Verify the caller is using their voting address
        assert Txn.sender == xgov_box.voting_addr, "Must use xGov voting address"

        # verify proposal id is genuine proposal
        assert Global.current_application_address == proposal_id.creator

        # Call the Proposal App to register the vote
        # TODO: uncomment this
        # arc4.abi_call(
        #     proposal_contract.Proposal.vote_proposal,
        #     UInt64(vote),
        #     vote_amount,
        #     app_id=proposal_id
        # )

    @arc4.abimethod()
    def pay_grant_proposal(self, proposal_id: Application) -> None:
        # Verify the caller is the xGov Payor
        assert arc4.Address(Txn.sender) == self.xgov_payor.value, "Only xGov Payor can pay grant proposals"

        # Verify proposal_id is a genuine proposal created by this registry
        assert proposal_id.creator == Global.current_application_address, "Invalid proposal"

        # Read proposal state directly from the Proposal App's global state
        status_bytes, _ = op.AppGlobal.get_ex_bytes(proposal_id, b"status")
        status = op.btoi(status_bytes)
        proposer_bytes, _ = op.AppGlobal.get_ex_bytes(proposal_id, b"proposer")
        proposer = arc4.Address(proposer_bytes)
        requested_amount_bytes, _ = op.AppGlobal.get_ex_bytes(proposal_id, b"requested_amount")
        requested_amount = op.btoi(requested_amount_bytes)
        # Verify the proposal is in the approved state
        assert status == UInt64(proposal_enm.STATUS_APPROVED), "Proposal is not approved"

        # Verify the proposer's KYC is still valid
        proposer_box, exists = self.proposer_box.maybe(proposer)
        assert exists, "Proposer does not exist"
        assert proposer_box.kyc_status, "Proposer KYC is not valid"
        assert proposer_box.kyc_expiring > Global.latest_timestamp, "Proposer KYC has expired"

        # Verify sufficient funds are available
        assert self.outstanding_funds.value >= requested_amount, "Insufficient funds in treasury"

        self.disburse_funds(proposer, requested_amount)
        
        arc4.abi_call("release_funds", app_id=proposal_id)

        # Decrement pending proposals count
        self.pending_proposals.value = (self.pending_proposals.value - UInt64(1))

        # Update proposer's active proposal status
        proposer_box.active_proposal = arc4.Bool(False)
        self.proposer_box[proposer] = proposer_box

    @arc4.abimethod()
    def deposit_funds(self, pmt: gtxn.PaymentTransaction) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can deposit funds"
        assert pmt.receiver == Global.current_application_address
        self.outstanding_funds.value += pmt.amount

    @arc4.abimethod()
    def withdraw_funds(self, amount: UInt64) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can withdraw funds"
        assert amount <= self.outstanding_funds.value, "Insufficient funds"
        self.outstanding_funds.value = (self.outstanding_funds.value - amount)
        
        itxn.Payment(
            receiver=self.xgov_manager.value.native,
            amount=amount,
            fee=UInt64(0),
        ).submit()