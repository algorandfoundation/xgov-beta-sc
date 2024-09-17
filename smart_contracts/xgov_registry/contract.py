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
    GlobalState
)

import smart_contracts.errors.std_errors as err
from . import config as cfg
from . import constants as const
from . import enums as enm
from . import types as typ

from ..proposal import enums as penm
from ..proposal import contract as proposal_contract

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
        self.kyc_provider = GlobalState(arc4.Address(), key=cfg.GS_KEY_KYC_PROVIDER)
        self.xgov_payor = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_PAYOR)
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
        self.pending_proposals = GlobalState(UInt64(), key=cfg.GS_KEY_PENDING_PROPOSALS)
        
        self.committee_id = GlobalState(arc4.StaticArray[arc4.Byte, 32], key=cfg.GS_KEY_COMMITTEE_ID)
        self.committee_members = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_MEMBERS)
        self.committee_votes = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_VOTES)

        # boxes
        self.xgov_box = BoxMap(arc4.StaticArray[bytes, t.Literal[33]], typ.XgovBoxValue)
        self.proposer_box = BoxMap(arc4.StaticArray[bytes, t.Literal[33]], typ.ProposerBoxValue)

    @subroutine
    def is_xgov_manager(self) -> bool:
        return Txn.sender == self.xgov_manager

    @subroutine
    def no_pending_proposals(self) -> bool:
        return self.pending_proposals == UInt64(0)
    
    @subroutine
    def disburse_funds(self, receiver: arc4.Address, amount: arc4.UInt64) -> None:
        # Transfer the funds to the receiver
        itxn.Payment(
            receiver=receiver,
            amount=amount,
            fee=0,
        ).submit()

        # Update the outstanding funds
        self.outstanding_funds -= amount

    @arc4.abimethod()
    def set_xgov_manager(self, new_manager: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set new manager"
        self.xgov_manager = new_manager

    @arc4.abimethod()
    def set_kyc_provider(self, new_provider: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set KYC Provider"
        self.kyc_provider = new_provider

    @arc4.abimethod()
    def set_payor(self, new_payor: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set KYC Provider"
        self.xgov_payor = new_payor

    @arc4.abimethod()
    def set_publisher(self, new_publisher: arc4.Address) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can set Publisher"
        self.committee_publisher = new_publisher

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can configure registry"
        assert self.no_pending_proposals(), "Cannot configure with pending proposals"
        
        self.xgov_min_balance = config.xgov_min_balance
        self.proposer_fee = config.proposer_fee
        self.proposal_fee = config.proposal_fee
        self.proposal_publishing_perc = config.proposal_publishing_perc
        self.proposal_commitment_perc = config.proposal_commitment_perc
        self.min_req_amount = config.min_req_amount

        self.max_req_amount_s = config.max_req_amount[0]
        self.max_req_amount_m = config.max_req_amount[1]
        self.max_req_amount_l = config.max_req_amount[2]
        
        self.discussion_duration_s = config.discussion_duration[0]
        self.discussion_duration_m = config.discussion_duration[1]
        self.discussion_duration_l = config.discussion_duration[2]
        self.discussion_duration_xl = config.discussion_duration[3]

        self.voting_duration_s = config.voting_duration[0]
        self.voting_duration_m = config.voting_duration[1]
        self.voting_duration_l = config.voting_duration[2]
        self.voting_duration_xl = config.voting_duration[3]
        
        self.cool_down_duration = config.cool_down_duration
        
        self.quorum_s = config.quorum[0]
        self.quorum_m = config.quorum[1]
        self.quorum_l = config.quorum[2]
        
        self.weighted_quorum_s = config.weighted_quorum[0]
        self.weighted_quorum_m = config.weighted_quorum[1]
        self.weighted_quorum_l = config.weighted_quorum[2]

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_xgov_registry(self) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can update registry"
        assert self.no_pending_proposals(), "Cannot update with pending proposals"

    @arc4.abimethod()
    def subscribe_xgov(self, pmt: gtxn.PaymentTransaction) -> None:
        # check if already an xGov
        xgov_key = b'x' + Txn.sender.bytes
        
        _, exists = self.xgov_box.maybe(xgov_key)
        assert not exists, "Already an xGov"

        # check payment
        assert pmt.receiver == Global.current_application_address, "Payment must be to current application"
        assert pmt.amount == self.xgov_min_balance, "Incorrect payment amount"

        # create box
        self.xgov_box[xgov_key] = typ.XgovBoxValue(
            voting_addr=Txn.sender.bytes
        )

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        # ensure they covered the itxn fee
        assert Txn.fee >= Global.min_txn_fee() * 2, "Fee must cover mbr refund"

        xgov_key = b'x' + Txn.sender.bytes

        # check if xGov
        _, exists = self.xgov_box.maybe(xgov_key)
        assert exists, "Not an xGov"

        # delete box
        del self.xgov_box[xgov_key]

        # refund
        itxn.Payment(
            receiver=Txn.sender,
            amount=self.xgov_min_balance,
            fee=UInt64(0),
        ).submit()

    @arc4.abimethod()
    def set_voting_account(self, voting_account: arc4.Address) -> None:
        # Check if the sender is an xGov member
        xgov_key = b'x' + Txn.sender.bytes
        xgov_value, is_xgov = self.xgov_box.maybe(xgov_key)
        assert is_xgov, "Only xGov members can set a voting account"

        # Check that the voting account is different from the current voting account
        assert xgov_value.voting_addr != voting_account, "Voting account must be different from the current voting account"

        # Update the voting account in the xGov box
        self.xgov_box[xgov_key] = typ.XgovBoxValue(
            voting_addr=arc4.Address(voting_account)
        )

    @arc4.abimethod()
    def subscribe_proposer(self, pmt: gtxn.PaymentTransaction) -> None:

        proposer_key = b'p' + Txn.sender.bytes
        _, exists = self.proposer_box.maybe(proposer_key)
        assert not exists, "Already a proposer"

        # check fee
        assert pmt.receiver == Global.current_application_address, "Payment must be to current application"
        assert pmt.amount == self.proposer_fee, "Incorrect payment amount"

        self.proposer_box[proposer_key] = typ.ProposerBoxValue(
            active_proposal=arc4.Bool(False),
            kyc_status=arc4.Bool(False),
            kyc_expiring=arc4.UInt64(0),
        )

    @arc4.abimethod()
    def set_proposer_kyc(self, proposer: arc4.Account, kyc_status: arc4.Bool, kyc_expiring: arc4.UInt64) -> None:
        # check if kyc provider
        assert Txn.sender == self.kyc_provider, "Only KYC Provider can validate KYC"
        
        proposer_key = b'p' + proposer.bytes
        box_value, exists = self.proposer_box.maybe(proposer_key)
        assert exists, "Proposer does not exist"

        box_value.kyc_status = kyc_status
        box_value.kyc_expiring = kyc_expiring
        self.proposer_box[proposer_key] = box_value

    @arc4.abimethod
    def open_proposal(self, proposal_type: arc4.Uint8, requested_amount: arc4.Uint64) -> UInt64:
        # Check if the caller is a registered proposer
        proposer_key = b'p' + Txn.sender.bytes
        proposer_state, exists = self.proposer_box.maybe(proposer_key)
        assert exists, "Not a proposer"
        
        # Check if the proposer already has an active proposal
        assert not proposer_state.active_proposal, "Proposer already has an active proposal"

        # Ensure the transaction has the correct payment
        assert Txn.fee >= Global.min_txn_fee * UInt64(2), "Insufficient fee"
        assert Txn.amount == self.proposal_fee, "Insufficient payment"
        assert Txn.receiver == self.application_address, "Payment must be to current application"

        # Create the Proposal App
        application_txn = itxn.ApplicationCall(
            approval_program=const.PROPOSAL_APPROVAL,
            clear_state_program=const.PROPOSAL_CLEAR,
            global_num_uints=UInt64(15),
            global_num_byte_slices=UInt64(5),
            local_num_uints=UInt64(0),
            local_num_byte_slices=UInt64(0),
            fee=0,
        ).submit()

        proposal_app = application_txn.created_app

        # Update proposer state
        proposer_state.active_proposal = True
        self.proposer_box[proposer_key] = proposer_state

        # Transfer funds to the new Proposal App
        itxn.Payment(
            receiver=proposal_app.address,
            amount=self.proposal_fee,
            fee=Global.min_txn_fee,
        ).submit()

        # Increment pending proposals
        self.pending_proposals += UInt64(1)

        return UInt64(proposal_app)

    @arc4.abimethod()
    def vote_proposal(self, proposal_id: arc4.Application, vote: enm.Vote, vote_amount: arc4.Uint64) -> None:
        # Verify the caller is an xGov member
        xgov_key = b'x' + Txn.sender.bytes
        xgov_box, exists = self.xgov_box.maybe(xgov_key)
        assert exists, "Caller is not an xGov member"

        # Verify the caller is using their voting address
        assert Txn.sender == xgov_box.voting_addr, "Must use xGov voting address"

        # verify proposal id is genuine proposal
        assert Global.current_application_address == proposal_id.creator

        # Call the Proposal App to register the vote
        arc4.abi_call(
            proposal_contract.Proposal.vote_proposal,
            UInt64(vote),
            vote_amount,
            app_id=proposal_id
        )

    @arc4.abimethod()
    def pay_grant_proposal(self, proposal_id: Application) -> None:
        # Verify the caller is the xGov Payor
        assert Txn.sender == self.xgov_payor, "Only xGov Payor can pay grant proposals"

        # Verify proposal_id is a genuine proposal created by this registry
        assert proposal_id.creator == Global.current_application_address, "Invalid proposal"

        # Read proposal state directly from the Proposal App's global state
        status = op.AppGlobal.get_ex_bytes(proposal_id, b"status")
        proposer = op.AppGlobal.get_ex_bytes(proposal_id, b"proposer")
        requested_amount = op.AppGlobal.get_ex_bytes(proposal_id, b"requested_amount")

        # Verify the proposal is in the approved state
        assert status == penm.STATUS_APPROVED, "Proposal is not approved"

        # Verify the proposer's KYC is still valid
        proposer_key = b'p' + proposer
        proposer_box, exists = self.proposer_box.maybe(proposer_key)
        assert exists, "Proposer does not exist"
        assert proposer_box.kyc_status, "Proposer KYC is not valid"
        assert proposer_box.kyc_expiring > Global.latest_timestamp, "Proposer KYC has expired"

        # Verify sufficient funds are available
        assert self.outstanding_funds >= requested_amount, "Insufficient funds in treasury"

        self.disburse_funds(proposer, requested_amount)
        
        arc4.abi_call[None]("release_funds", app=proposal_id)

        # Decrement pending proposals count
        self.pending_proposals -= UInt64(1)

        # Update proposer's active proposal status
        proposer_box.active_proposal = False
        self.proposer_box[proposer_key] = proposer_box

    @arc4.abimethod()
    def deposit_funds(self, pmt: gtxn.PaymentTransaction) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can deposit funds"
        assert pmt.receiver == Global.current_application_address
        self.outstanding_funds += pmt.amount

    @arc4.abimethod()
    def withdraw_funds(self, amount: UInt64) -> None:
        assert self.is_xgov_manager(), "Only xGov Manager can withdraw funds"
        assert amount <= self.outstanding_funds, "Insufficient funds"
        self.outstanding_funds -= amount
        
        itxn.Payment(
            receiver=self.xgov_manager.native,
            amount=amount,
            fee=UInt64(0),
        ).submit()