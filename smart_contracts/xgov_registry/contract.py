import typing as t

from algopy import (
    Account,
    Application,
    ARC4Contract,
    BoxMap,
    Global,
    GlobalState,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    compile_contract,
    gtxn,
    itxn,
    op,
    subroutine,
)

import smart_contracts.errors.std_errors as err

from ..common import types as ptyp
from ..proposal import config as pcfg
from ..proposal import enums as penm
from ..proposal_mock import contract as proposal_contract
from . import config as cfg
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

        # Initialize global state variables
        self.xgov_manager = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_MANAGER)
        self.xgov_payor = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_PAYOR)
        self.xgov_reviewer = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_REVIEWER)

        self.kyc_provider = GlobalState(arc4.Address(), key=cfg.GS_KEY_KYC_PROVIDER)
        self.committee_manager = GlobalState(
            arc4.Address(), key=cfg.GS_KEY_COMMITTEE_MANAGER
        )
        self.committee_publisher = GlobalState(
            arc4.Address(), key=cfg.GS_KEY_COMMITTEE_PUBLISHER
        )

        self.xgov_fee = GlobalState(UInt64(), key=cfg.GS_KEY_XGOV_FEE)
        self.xgovs = GlobalState(UInt64(), key=cfg.GS_KEY_XGOVS)
        self.proposer_fee = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSER_FEE)
        self.proposal_fee = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSAL_FEE)
        self.proposal_publishing_bps = GlobalState(
            UInt64(), key=cfg.GS_KEY_PROPOSAL_PUBLISHING_BPS
        )
        self.proposal_commitment_bps = GlobalState(
            UInt64(), key=cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS
        )

        self.min_requested_amount = GlobalState(
            UInt64(), key=cfg.GS_KEY_MIN_REQUESTED_AMOUNT
        )

        self.max_requested_amount_small = GlobalState(
            UInt64(), key=cfg.GS_KEY_MAX_REQUESTED_AMOUNT_SMALL
        )
        self.max_requested_amount_medium = GlobalState(
            UInt64(), key=cfg.GS_KEY_MAX_REQUESTED_AMOUNT_MEDIUM
        )
        self.max_requested_amount_large = GlobalState(
            UInt64(), key=cfg.GS_KEY_MAX_REQUESTED_AMOUNT_LARGE
        )

        self.discussion_duration_small = GlobalState(
            UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_SMALL
        )
        self.discussion_duration_medium = GlobalState(
            UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_MEDIUM
        )
        self.discussion_duration_large = GlobalState(
            UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_LARGE
        )
        self.discussion_duration_xlarge = GlobalState(
            UInt64(), key=cfg.GS_KEY_DISCUSSION_DURATION_XLARGE
        )

        self.voting_duration_small = GlobalState(
            UInt64(), key=cfg.GS_KEY_VOTING_DURATION_SMALL
        )
        self.voting_duration_medium = GlobalState(
            UInt64(), key=cfg.GS_KEY_VOTING_DURATION_MEDIUM
        )
        self.voting_duration_large = GlobalState(
            UInt64(), key=cfg.GS_KEY_VOTING_DURATION_LARGE
        )
        self.voting_duration_xlarge = GlobalState(
            UInt64(), key=cfg.GS_KEY_VOTING_DURATION_XLARGE
        )

        self.cool_down_duration = GlobalState(
            UInt64(), key=cfg.GS_KEY_COOL_DOWN_DURATION
        )
        self.stale_proposal_duration = GlobalState(
            UInt64(), key=cfg.GS_KEY_STALE_PROPOSAL_DURATION
        )

        self.quorum_small = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_SMALL)
        self.quorum_medium = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_MEDIUM)
        self.quorum_large = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_LARGE)

        self.weighted_quorum_small = GlobalState(
            UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_SMALL
        )
        self.weighted_quorum_medium = GlobalState(
            UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_MEDIUM
        )
        self.weighted_quorum_large = GlobalState(
            UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_LARGE
        )

        self.outstanding_funds = GlobalState(UInt64(), key=cfg.GS_KEY_OUTSTANDING_FUNDS)

        self.committee_id = GlobalState(ptyp.CommitteeId, key=cfg.GS_KEY_COMMITTEE_ID)
        self.committee_members = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_MEMBERS)
        self.committee_votes = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_VOTES)

        self.pending_proposals = GlobalState(UInt64(), key=cfg.GS_KEY_PENDING_PROPOSALS)

        # boxes
        self.xgov_box = BoxMap(
            Account, arc4.Address, key_prefix=cfg.XGOV_BOX_MAP_PREFIX
        )
        self.proposer_box = BoxMap(
            Account, typ.ProposerBoxValue, key_prefix=cfg.PROPOSER_BOX_MAP_PREFIX
        )

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
        return (
            Application(proposal_id.native).creator
            == Global.current_application_address
        )

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

    @subroutine
    def valid_kyc(self, address: Account) -> bool:
        return (
            self.proposer_box[address].kyc_status.native
            and self.proposer_box[address].kyc_expiring.native > Global.latest_timestamp
        )

    @arc4.abimethod(create="require")
    def create(self) -> None:
        """Create the xGov Registry.

        Args:
            manager (arc4.Address): Address of the xGov Manager
            payor (arc4.Address): Address of the xGov Payor
            committee_manager (arc4.Address): Address of the xGov Committee Manager
        """

        self.xgov_manager.value = arc4.Address(Txn.sender)

    @arc4.abimethod()
    def set_xgov_manager(self, manager: arc4.Address) -> None:
        """Sets the xGov Manager.

        Args:
            manager (arc4.Address): Address of the new xGov Manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_manager.value = manager

    @arc4.abimethod()
    def set_payor(self, payor: arc4.Address) -> None:
        """Sets the xGov Payor.

        Args:
            payor (arc4.Address): Address of the new xGov Payor

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_payor.value = payor

    @arc4.abimethod()
    def set_xgov_reviewer(self, reviewer: arc4.Address) -> None:
        """Sets the xGov Reviewer.

        Args:
            reviewer (arc4.Address): Address of the new xGov Reviewer

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_reviewer.value = reviewer

    @arc4.abimethod()
    def set_kyc_provider(self, provider: arc4.Address) -> None:
        """Sets the KYC provider.

        Args:
            provider (arc4.Address): Address of the new KYC Provider

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.kyc_provider.value = provider

    @arc4.abimethod()
    def set_committee_manager(self, manager: arc4.Address) -> None:
        """Sets the Committee Manager.

        Args:
            manager (arc4.Address): Address of the new xGov Manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.committee_manager.value = manager

    @arc4.abimethod()
    def set_committee_publisher(self, publisher: arc4.Address) -> None:
        """Sets the Committee Publisher.

        Args:
            publisher (arc4.Address): Address of the new Committee Publisher

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.committee_publisher.value = publisher

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
        """Sets the configuration of the xGov Registry.

        Args:
            config (arc4.Struct): Configuration class containing the field data

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
            err.NO_PENDING_PROPOSALS: If there are currently pending proposals
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert self.no_pending_proposals(), err.NO_PENDING_PROPOSALS

        self.xgov_fee.value = config.xgov_fee.native
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
        """Updates the xGov Registry contract

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
            err.NO_PENDING_PROPOSALS: If there are currently pending proposals
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

    @arc4.abimethod()
    def subscribe_xgov(self, payment: gtxn.PaymentTransaction) -> None:
        """Subscribes the sender to being an xGov

        Args:
            payment (gtxn.PaymentTransaction): The payment transaction covering the signup fee

        Raises:
            err.ALREADY_XGOV: If the sender is already an xGov
            err.WRONG_RECEIVER: If the recipient is not the xGov Registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment transaction is not equal to the xgov_fee global state key
        """

        assert Txn.sender not in self.xgov_box, err.ALREADY_XGOV
        # check payment
        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        assert payment.amount == self.xgov_fee.value, err.WRONG_PAYMENT_AMOUNT

        # create box
        self.xgov_box[Txn.sender] = arc4.Address(Txn.sender)
        self.xgovs.value += 1

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        """Unsubscribes the sender from being an xGov

        Raises:
            err.UNAUTHORIZED: If the sender is not currently an xGov
        """

        assert Txn.sender in self.xgov_box, err.UNAUTHORIZED

        # delete box
        del self.xgov_box[Txn.sender]
        self.xgovs.value -= 1

    @arc4.abimethod()
    def set_voting_account(
        self, xgov_address: arc4.Address, voting_address: arc4.Address
    ) -> None:
        """Sets the voting address for the xGov

        Args:
            voting_address (arc4.Address): The voting account address to delegate voting power to

        Raises:
            err.UNAUTHORIZED: If the sender is not currently an xGov
            err.VOTING_ADDRESS_MUST_BE_DIFFERENT: If the new voting account is the same as currently set
        """

        # Check if the sender is an xGov member
        old_voting_address, exists = self.xgov_box.maybe(xgov_address.native)
        assert exists, err.UNAUTHORIZED

        # Check that the sender is either the xgov or the voting address
        assert (
            Txn.sender == old_voting_address or Txn.sender == xgov_address
        ), err.UNAUTHORIZED

        # Update the voting account in the xGov box
        self.xgov_box[xgov_address.native] = voting_address

    @arc4.abimethod()
    def subscribe_proposer(self, payment: gtxn.PaymentTransaction) -> None:
        """Subscribes the sender to being a Proposer

        Args:
            payment (gtxn.PaymentTransaction): The payment transaction covering the proposer fee

        Raises:
            err.ALREADY_PROPOSER: If the sender is already a Proposer
            err.WRONG_RECEIVER: If the recipient is not the xGov Registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment transaction is not equal to the proposer_fee global state key
        """

        assert Txn.sender not in self.proposer_box, err.ALREADY_PROPOSER
        # check fee
        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        assert payment.amount == self.proposer_fee.value, err.WRONG_PAYMENT_AMOUNT

        self.proposer_box[Txn.sender] = typ.ProposerBoxValue(
            active_proposal=arc4.Bool(False),  # noqa: FBT003
            kyc_status=arc4.Bool(False),  # noqa: FBT003
            kyc_expiring=arc4.UInt64(0),
        )

    @arc4.abimethod()
    def set_proposer_kyc(
        self, proposer: arc4.Address, kyc_status: arc4.Bool, kyc_expiring: arc4.UInt64
    ) -> None:
        """Sets a proposer's KYC status

        Args:
            proposer (arc4.Address): The address of the Proposer
            kyc_status (arc4.Bool): The new status of the Proposer
            kyc_expiring (arc4.UInt64): The expiration date as a unix timestamp of the time the KYC expires

        Raises:
            err.UNAUTHORIZED: If the sender is not the KYC Provider
            err.PROPOSER_DOES_NOT_EXIST: If the referenced address is not a Proposer
        """

        # check if kyc provider
        assert Txn.sender == self.kyc_provider.value.native, err.UNAUTHORIZED
        assert proposer.native in self.proposer_box, err.PROPOSER_DOES_NOT_EXIST

        active_proposal = self.proposer_box[proposer.native].copy().active_proposal

        self.proposer_box[proposer.native] = typ.ProposerBoxValue(
            active_proposal=active_proposal,
            kyc_status=kyc_status,
            kyc_expiring=kyc_expiring,
        )

    @arc4.abimethod()
    def declare_committee(
        self, cid: ptyp.CommitteeId, size: arc4.UInt64, votes: arc4.UInt64
    ) -> None:
        """Sets the xGov Committee in charge

        Args:
            id (ptyp.CommitteeId): The ID of the xGov Committee
            size (arc4.UInt64): The size of the xGov Committee
            votes (arc4.UInt64): The voting power of the xGov Committee

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
        """

        assert self.is_xgov_committee_manager(), err.UNAUTHORIZED

        self.committee_id.value = cid.copy()
        self.committee_members.value = size.native
        self.committee_votes.value = votes.native

    @arc4.abimethod
    def open_proposal(self, payment: gtxn.PaymentTransaction) -> UInt64:
        """Creates a new Proposal

        Args:
            payment (gtxn.PaymentTransaction): payment for covering the proposal fee (includes child contract MBR)

        Raises:
            err.UNAUTHORIZED: If the sender is not a Proposer
            err.ALREADY_ACTIVE_PROPOSAL: If the proposer already has an active proposal
            err.INVALID_KYC: If the Proposer does not have valid KYC
            err.INSUFFICIENT_FEE: If the fee for the current transaction doesn't cover the inner transaction fees
            err.WRONG_RECEIVER: If the recipient is not the xGov Registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment amount doesn't match the proposal fee
        """

        # Check if the caller is a registered proposer
        assert Txn.sender in self.proposer_box, err.UNAUTHORIZED

        # Check if the proposer already has an active proposal
        assert not self.proposer_box[
            Txn.sender
        ].active_proposal, err.ALREADY_ACTIVE_PROPOSAL
        assert self.valid_kyc(Txn.sender), err.INVALID_KYC

        assert Txn.fee >= (Global.min_txn_fee * 3), err.INSUFFICIENT_FEE

        # Ensure the transaction has the correct payment
        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        assert payment.amount == self.proposal_fee.value, err.WRONG_PAYMENT_AMOUNT

        # Create the Proposal App
        # TODO: replace the proposal mock contract with the real one
        compiled = compile_contract(proposal_contract.ProposalMock)

        proposal_app = arc4.abi_call(
            proposal_contract.ProposalMock.create,
            Txn.sender,
            approval_program=compiled.approval_program,
            clear_state_program=compiled.clear_state_program,
            global_num_bytes=pcfg.GLOBAL_BYTES,
            global_num_uint=pcfg.GLOBAL_UINTS,
            local_num_bytes=pcfg.LOCAL_BYTES,
            local_num_uint=pcfg.LOCAL_UINTS,
            fee=0,
        ).created_app

        # Update proposer state
        self.proposer_box[Txn.sender].active_proposal = arc4.Bool(True)  # noqa: FBT003

        # Transfer funds to the new Proposal App
        itxn.Payment(
            receiver=proposal_app.address,
            amount=self.proposal_fee.value - pcfg.PROPOSAL_MBR,
            fee=0,
        ).submit()

        # Increment pending proposals
        self.pending_proposals.value += 1

        return proposal_app.id

    @arc4.abimethod()
    def pay_grant_proposal(self, proposal_id: arc4.UInt64) -> None:
        """Disburses the funds for an approved proposal

        Args:
            proposal_id (arc4.UInt64): The application ID of the approved proposal

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Payor
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.PROPOSAL_IS_NOT_APPROVED: If the proposal status is not approved
            err.WRONG_PROPOSER: If the Proposer on the proposal is not found
            err.INVALID_KYC: If the Proposer KYC is invalid or expired
            err.INSUFFICIENT_TREASURY_FUNDS: If the xGov Registry does not have enough funds for the disbursement
        """

        # Verify the caller is the xGov Payor
        assert arc4.Address(Txn.sender) == self.xgov_payor.value, err.UNAUTHORIZED

        # Verify proposal_id is a genuine proposal created by this registry
        assert self.is_proposal(proposal_id), err.INVALID_PROPOSAL

        # Read proposal state directly from the Proposal App's global state
        status, status_exists = op.AppGlobal.get_ex_uint64(
            proposal_id.native, pcfg.GS_KEY_STATUS
        )
        proposer_bytes, proposer_exists = op.AppGlobal.get_ex_bytes(
            proposal_id.native, pcfg.GS_KEY_PROPOSER
        )
        proposer = arc4.Address(proposer_bytes)
        requested_amount, requested_amount_exists = op.AppGlobal.get_ex_uint64(
            proposal_id.native, pcfg.GS_KEY_REQUESTED_AMOUNT
        )
        # Verify the proposal is in the approved state
        # TODO: Switch to STATUS_MILESTONE
        assert status == UInt64(penm.STATUS_APPROVED), err.PROPOSAL_IS_NOT_APPROVED

        assert proposer.native in self.proposer_box, err.WRONG_PROPOSER

        assert self.valid_kyc(proposer.native), err.INVALID_KYC

        # Verify sufficient funds are available
        assert (
            self.outstanding_funds.value >= requested_amount
        ), err.INSUFFICIENT_TREASURY_FUNDS

        self.disburse_funds(proposer, requested_amount)

        arc4.abi_call(
            proposal_contract.ProposalMock.release_funds, app_id=proposal_id.native
        )

        # Decrement pending proposals count
        # TODO: might happen on decommission as well
        self.pending_proposals.value -= 1

        # Update proposer's active proposal status
        self.proposer_box[proposer.native].active_proposal = arc4.Bool(
            False  # noqa: FBT003
        )

    @arc4.abimethod()
    def deposit_funds(self, payment: gtxn.PaymentTransaction) -> None:
        """Tracks deposits to the xGov Treasury (xGov Registry Account)

        Args:
            payment (gtxn.PaymentTransaction): the deposit transaction

        Raises:
            err.WRONG_RECEIVER: If the recipient is not the xGov Treasury (xGov Registry Account)
        """

        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        self.outstanding_funds.value += payment.amount

    @arc4.abimethod()
    def withdraw_funds(self, amount: UInt64) -> None:
        """Remove funds from the xGov Treasury (xGov Registry Account)

        Args:
            amount (UInt64): the amount to remove

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
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
        """Returns the xGov Registry state"""

        return typ.TypedGlobalState(
            xgov_manager=self.xgov_manager.value,
            xgov_payor=self.xgov_payor.value,
            kyc_provider=self.kyc_provider.value,
            committee_manager=self.committee_manager.value,
            committee_publisher=self.committee_publisher.value,
            xgov_fee=arc4.UInt64(self.xgov_fee.value),
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
            stale_proposal_duration=arc4.UInt64(self.stale_proposal_duration.value),
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
            committee_votes=arc4.UInt64(self.committee_votes.value),
        )
