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
    op
)

import smart_contracts.errors.std_errors as err
from . import config as cfg
from . import constants as const
from . import enums as enm
from ..proposal import enums as penm
from . import types as typ

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

        self.xgov_admin = arc4.Address()
        self.kyc_provider = arc4.Address()
        self.committee_publisher = arc4.Address()
        self.xgov_min_balance = UInt64()
        self.proposer_fee = UInt64()
        self.proposal_fee = UInt64()
        self.proposal_publishing_perc = UInt64()
        self.proposal_commitment_perc = UInt64()
        self.min_req_amount = UInt64()
        self.max_req_amount_s = UInt64()
        self.max_req_amount_m = UInt64()
        self.max_req_amount_l = UInt64()
        self.discussion_duration_s = UInt64()
        self.discussion_duration_m = UInt64()
        self.discussion_duration_l = UInt64()
        self.discussion_duration_xl = UInt64()
        self.voting_duration_s = UInt64()
        self.voting_duration_m = UInt64()
        self.voting_duration_l = UInt64()
        self.voting_duration_xl = UInt64()
        self.cool_down_duration = UInt64()
        self.quorum_s = UInt64()
        self.quorum_m = UInt64()
        self.quorum_l = UInt64()
        self.weighted_quorum_s = UInt64()
        self.weighted_quorum_m = UInt64()
        self.weighted_quorum_l = UInt64()

        # boxes
        self.xgov_box = BoxMap(arc4.StaticArray[bytes, t.Literal[33]], typ.XgovBoxValue)
        self.proposer_box = BoxMap(arc4.StaticArray[bytes, t.Literal[33]], typ.ProposerBoxValue)

    @subroutine
    def is_xgov_admin(self) -> bool:
        return Txn.sender == self.xgov_admin

    @subroutine
    def no_pending_proposals(self) -> bool:
        return self.pending_proposals == UInt64(0)

    @arc4.abimethod()
    def set_xgov_manager(self, new_manager: arc4.Address) -> None:
        assert self.is_xgov_admin(), "Only xGov Manager can set new manager"
        self.xgov_admin = new_manager

    @arc4.abimethod()
    def set_kyc_provider(self, new_provider: arc4.Address) -> None:
        assert self.is_xgov_admin(), "Only xGov Manager can set KYC Provider"
        self.kyc_provider = new_provider

    @arc4.abimethod()
    def set_payor(self, new_payor: arc4.Address) -> None:
        assert self.is_xgov_admin(), "Only xGov Manager can set KYC Provider"
        self.payor = new_payor

    @arc4.abimethod()
    def set_publisher(self, new_publisher: arc4.Address) -> None:
        assert self.is_xgov_admin(), "Only xGov Manager can set Publisher"
        self.committee_publisher = new_publisher

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
        assert self.is_xgov_admin(), "Only xGov Manager can configure registry"
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
        assert self.is_xgov_admin(), "Only xGov Manager can update registry"
        assert self.no_pending_proposals(), "Cannot update with pending proposals"

    @arc4.abimethod()
    def subscribe_xgov(self, pmt: gtxn.PaymentTransaction) -> None:
        # check if already an xGov
        xgov_key = b'x' + Txn.sender.bytes
        
        _, exists = self.xgov_box.maybe(xgov_key)
        assert not exists, "Already an xGov"

        # check payment
        assert pmt.receiver == typ.XGOV_TREASURY_ADDRESS, "Payment must be to current application"
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
        assert pmt.receiver == const.XGOV_TREASURY_ADDRESS, "Payment must be to current application"
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
        itxn.ApplicationCall(
            app_id=proposal_id,
            app_args=[
                b'vote',
                UInt64(vote),
                vote_amount
            ],
            fee=0,
        ).submit()

@arc4.abimethod()
def pay_grant_proposal(self, proposal_id: Application) -> None:
    # Verify the caller is the xGov Payor
    assert Txn.sender == self.payor, "Only xGov Payor can pay grant proposals"

    # Verify proposal_id is a genuine proposal created by this registry
    assert Global.current_application_address == proposal_id.creator, "Invalid proposal"

    # Call the Proposal App to get the proposal state
    proposal_state = arc4.abi_call[typ.ProposalState](proposal_id, "get_state")

    # Verify the proposal is in the approved state
    assert proposal_state.status == penm.STATUS_APPROVED, "Proposal is not approved"

    # Verify the proposal is a grant (funded by Algorand Foundation)
    assert proposal_state.funding_type == penm.FUNDING_GRANT, "Not a grant proposal"

    # Verify the proposer's KYC is still valid
    proposer_key = b'p' + proposal_state.proposer
    proposer_box, exists = self.proposer_box.maybe(proposer_key)
    assert exists, "Proposer does not exist"
    assert proposer_box.kyc_status, "Proposer KYC is not valid"
    assert proposer_box.kyc_expiring > Global.latest_timestamp(), "Proposer KYC has expired"

    # Verify sufficient funds are available
    assert self.outstanding_funds >= proposal_state.requested_amount, "Insufficient funds in treasury"

    # Transfer the funds to the proposer
    itxn.Payment(
        receiver=proposal_state.proposer,
        amount=proposal_state.requested_amount,
        fee=0,
    ).submit()

    # Update the outstanding funds
    self.outstanding_funds -= proposal_state.requested_amount

    # Call the Proposal App to mark the proposal as funded
    itxn.ApplicationCall(
        application_id=proposal_id,
        on_completion=enm.NoOp,
        app_args=[b"mark_funded"],
        fee=0,
    ).submit()

    # Verify the inner transaction was successful
    assert itxn.LastLog == b"Proposal marked as funded", "Failed to mark proposal as funded"

    # Decrement pending proposals count
    self.pending_proposals -= UInt64(1)

    @arc4.abimethod()
    def deposit_funds(self, amount: UInt64) -> None:
        assert self.is_xgov_admin(), "Only xGov Manager can deposit funds"
        self.outstanding_funds += amount

    @arc4.abimethod()
    def withdraw_funds(self, amount: UInt64) -> None:
        assert self.is_xgov_admin(), "Only xGov Manager can withdraw funds"
        assert amount <= self.outstanding_funds, "Insufficient funds"
        self.outstanding_funds -= amount
        
        itxn.Payment(
            receiver=self.xgov_admin.native,
            amount=amount,
            fee=UInt64(0),
        ).submit()