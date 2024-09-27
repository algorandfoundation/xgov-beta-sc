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

from ..proposal import enums as proposal_enm
from ..proposal_mock import contract as proposal_contract
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
        self.xgov_box = BoxMap(Account, arc4.Address, key_prefix=b"x")
        self.proposer_box = BoxMap(Account, typ.ProposerBoxValue, key_prefix=b"p")

    @subroutine
    def is_xgov_manager(self) -> bool:
        return Txn.sender == self.xgov_manager.value.native
    
    @subroutine
    def no_pending_proposals(self) -> bool:
        return self.pending_proposals.value == 0
    
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

        self.xgov_manager.value = manager
        self.xgov_payor.value = payor
        self.committee_manager.value = comittee_manager

    @arc4.abimethod()
    def set_xgov_manager(self, manager: arc4.Address) -> None:
        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_manager.value = manager

    @arc4.abimethod()
    def set_kyc_provider(self, provider: arc4.Address) -> None:
        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.kyc_provider.value = provider

    @arc4.abimethod()
    def set_payor(self, payor: arc4.Address) -> None:
        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_payor.value = payor

    @arc4.abimethod()
    def set_committee_publisher(self, publisher: arc4.Address) -> None:
        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.committee_publisher.value = publisher

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
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
        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert self.no_pending_proposals(), err.NO_PENDING_PROPOSALS

    @arc4.abimethod()
    def subscribe_xgov(self, payment: gtxn.PaymentTransaction) -> None:
        assert not Txn.sender in self.xgov_box, err.ALREADY_XGOV
        # check payment
        assert payment.receiver == Global.current_application_address, err.WRONG_RECEIVER
        assert payment.amount == self.xgov_min_balance.value, err.WRONG_PAYMENT_AMOUNT

        # create box
        self.xgov_box[Txn.sender] = arc4.Address(Txn.sender)

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        # ensure they covered the itxn fee
        assert Txn.fee >= (Global.min_txn_fee * UInt64(2)), err.INSUFFICIENT_FEE
        assert Txn.sender in self.xgov_box, err.UNAUTHORIZED

        # delete box
        del self.xgov_box[Txn.sender]

        # refund
        itxn.Payment(
            receiver=Txn.sender,
            amount=self.xgov_min_balance.value,
            fee=UInt64(0),
        ).submit()

    @arc4.abimethod()
    def set_voting_account(self, voting_address: arc4.Address) -> None:
        # Check if the sender is an xGov member
        old_voting_address, exists = self.xgov_box.maybe(Txn.sender)
        assert exists, err.UNAUTHORIZED

        # Check that the voting account is different from the current voting account
        assert old_voting_address != voting_address, err.VOTING_ADDRESS_MUST_BE_DIFFERENT

        # Update the voting account in the xGov box
        self.xgov_box[Txn.sender] = voting_address

    @arc4.abimethod()
    def subscribe_proposer(self, payment: gtxn.PaymentTransaction) -> None:
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
        id: arc4.StaticArray[arc4.Byte, t.Literal[32]],
        size: UInt64,
        votes: UInt64
    ) -> None:
        assert self.is_xgov_manager(), err.UNAUTHORIZED

        self.committee_id.value = id.copy()
        self.committee_members.value = size
        self.committee_votes.value = votes

    @arc4.abimethod
    def open_proposal(self, payment: gtxn.PaymentTransaction) -> UInt64:
        # Check if the caller is a registered proposer
        assert Txn.sender in self.proposer_box, err.UNAUTHORIZED

        proposer_state = self.proposer_box[Txn.sender].copy()

        # Check if the proposer already has an active proposal
        assert not proposer_state.active_proposal, err.ALREADY_ACTIVE_PROPOSAL

        assert Txn.fee >= Global.min_txn_fee * UInt64(3), err.INSUFFICIENT_FEE

        # Ensure the transaction has the correct payment
        assert payment.amount == self.proposal_fee.value, err.WRONG_PAYMENT
        assert payment.receiver == Global.current_application_address, err.WRONG_RECEIVER

        # Create the Proposal App
        compiled = compile_contract(proposal_contract.ProposalMock)
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
        self.proposer_box[Txn.sender] = typ.ProposerBoxValue(
            active_proposal=arc4.Bool(True),
            kyc_expiring=proposer_state.kyc_expiring,
            kyc_status=proposer_state.kyc_status
        )

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
    def vote_proposal(self, proposal_id: Application, xgov_address: arc4.Address, vote: UInt64, vote_amount: UInt64) -> None:
        # ensure a voting enum is being used
        assert vote < UInt64(3), err.INVALID_VOTE

        # verify proposal id is genuine proposal
        assert Global.current_application_address == proposal_id.creator, err.INVALID_PROPOSAL

        # make sure they're voting on behalf of an xgov
        voting_address, exists = self.xgov_box.maybe(xgov_address.native)
        assert exists, err.UNAUTHORIZED

        # Verify the caller is using their voting address
        assert Txn.sender == voting_address.native, err.MUST_BE_VOTING_ADDRESS

        # Call the Proposal App to register the vote
        arc4.abi_call(
            proposal_contract.ProposalMock.vote,
            xgov_address,
            vote,
            vote_amount,
            app_id=proposal_id
        )

    @arc4.abimethod()
    def pay_grant_proposal(self, proposal_id: Application) -> None:
        # Verify the caller is the xGov Payor
        assert arc4.Address(Txn.sender) == self.xgov_payor.value, err.UNAUTHORIZED

        # Verify proposal_id is a genuine proposal created by this registry
        assert proposal_id.creator == Global.current_application_address, err.INVALID_PROPOSAL

        # Read proposal state directly from the Proposal App's global state
        status, status_exists = op.AppGlobal.get_ex_uint64(proposal_id, b"status")
        proposer_bytes, proposer_exists = op.AppGlobal.get_ex_bytes(proposal_id, b"proposer")
        proposer = arc4.Address(proposer_bytes)
        requested_amount, requested_amount_exists = op.AppGlobal.get_ex_uint64(proposal_id, b"requested_amount")
        # Verify the proposal is in the approved state
        assert status == UInt64(proposal_enm.STATUS_APPROVED), err.PROPOSAL_IS_NOT_APPROVED

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
            app_id=proposal_id
        )

        # Decrement pending proposals count
        self.pending_proposals.value = (self.pending_proposals.value - UInt64(1))

        # Update proposer's active proposal status
        self.proposer_box[proposer.native] = typ.ProposerBoxValue(
            active_proposal=arc4.Bool(False),
            kyc_status=proposer_state.kyc_status,
            kyc_expiring=proposer_state.kyc_expiring
        )

    @arc4.abimethod()
    def deposit_funds(self, payment: gtxn.PaymentTransaction) -> None:
        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert (payment.receiver == Global.current_application_address), err.WRONG_RECEIVER
        self.outstanding_funds.value += payment.amount

    @arc4.abimethod()
    def withdraw_funds(self, amount: UInt64) -> None:
        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert amount <= self.outstanding_funds.value, err.INSUFFICIENT_FUNDS
        self.outstanding_funds.value = (self.outstanding_funds.value - amount)
        
        itxn.Payment(
            receiver=self.xgov_manager.value.native,
            amount=amount,
            fee=UInt64(0),
        ).submit()

    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.TypedGlobalState:
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
