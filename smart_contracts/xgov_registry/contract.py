import typing as t

from algopy import (
    Account,
    Application,
    ARC4Contract,
    BoxMap,
    BoxRef,
    Bytes,
    Global,
    GlobalState,
    StateTotals,
    String,
    TemplateVar,
    Txn,
    UInt64,
    arc4,
    compile_contract,
    gtxn,
    itxn,
    op,
    size_of,
    subroutine,
)

import smart_contracts.common.abi_types as typ
import smart_contracts.errors.std_errors as err

from ..proposal import config as pcfg
from ..proposal import constants as pcts
from ..proposal import contract as proposal_contract
from ..proposal import enums as penm
from . import config as cfg
from .constants import (
    ACCOUNT_MBR,
    BPS,
    BYTES_PER_APP_PAGE,
    MAX_MBR_PER_APP,
    MAX_MBR_PER_BOX,
    PER_BOX_MBR,
    PER_BYTE_IN_BOX_MBR,
)


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
        self.paused_registry = GlobalState(UInt64(), key=cfg.GS_KEY_PAUSED_REGISTRY)
        self.paused_proposals = GlobalState(UInt64(), key=cfg.GS_KEY_PAUSED_PROPOSALS)

        self.xgov_manager = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_MANAGER)
        self.xgov_subscriber = GlobalState(
            arc4.Address(), key=cfg.GS_KEY_XGOV_SUBSCRIBER
        )
        self.xgov_payor = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_PAYOR)
        self.xgov_council = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_COUNCIL)

        self.kyc_provider = GlobalState(arc4.Address(), key=cfg.GS_KEY_KYC_PROVIDER)
        self.committee_manager = GlobalState(
            arc4.Address(), key=cfg.GS_KEY_COMMITTEE_MANAGER
        )
        self.xgov_daemon = GlobalState(arc4.Address(), key=cfg.GS_KEY_XGOV_DAEMON)

        self.xgov_fee = GlobalState(UInt64(), key=cfg.GS_KEY_XGOV_FEE)
        self.xgovs = GlobalState(UInt64(), key=cfg.GS_KEY_XGOVS)
        self.proposer_fee = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSER_FEE)
        self.open_proposal_fee = GlobalState(UInt64(), key=cfg.GS_KEY_OPEN_PROPOSAL_FEE)
        self.daemon_ops_funding_bps = GlobalState(
            UInt64(), key=cfg.GS_KEY_DAEMON_OPS_FUNDING_BPS
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

        self.committee_id = GlobalState(typ.Bytes32, key=cfg.GS_KEY_COMMITTEE_ID)
        self.committee_members = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_MEMBERS)
        self.committee_votes = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_VOTES)

        self.pending_proposals = GlobalState(UInt64(), key=cfg.GS_KEY_PENDING_PROPOSALS)

        self.request_id = GlobalState(UInt64(), key=cfg.GS_KEY_REQUEST_ID)

        self.max_committee_size = GlobalState(
            UInt64(), key=cfg.GS_KEY_MAX_COMMITTEE_SIZE
        )

        # boxes
        self.proposal_approval_program = BoxRef(key=cfg.PROPOSAL_APPROVAL_PROGRAM_BOX)
        self.xgov_box = BoxMap(
            Account,
            typ.XGovBoxValue,
            key_prefix=cfg.XGOV_BOX_MAP_PREFIX,
        )

        self.request_box = BoxMap(
            UInt64,
            typ.XGovSubscribeRequestBoxValue,
            key_prefix=cfg.REQUEST_BOX_MAP_PREFIX,
        )

        self.proposer_box = BoxMap(
            Account,
            typ.ProposerBoxValue,
            key_prefix=cfg.PROPOSER_BOX_MAP_PREFIX,
        )
        # declared here just for MBR calculation purposes, not to be used
        self.voters = BoxMap(
            Account,
            UInt64,
            key_prefix=pcfg.VOTER_BOX_KEY_PREFIX,
        )

    @subroutine
    def entropy(self) -> Bytes:
        return TemplateVar[Bytes]("entropy")  # trick to allow fresh deployment

    @subroutine
    def is_xgov_manager(self) -> bool:
        return Txn.sender == self.xgov_manager.value.native

    @subroutine
    def is_xgov_subscriber(self) -> bool:
        return Txn.sender == self.xgov_subscriber.value.native

    @subroutine
    def is_xgov_committee_manager(self) -> bool:
        return Txn.sender == self.committee_manager.value.native

    @subroutine
    def no_pending_proposals(self) -> bool:
        return self.pending_proposals.value == 0

    @subroutine
    def _is_proposal(self, proposal_id: UInt64) -> bool:
        return Application(proposal_id).creator == Global.current_application_address

    @subroutine
    def get_proposal_status(self, proposal_id: UInt64) -> UInt64:
        status, status_exists = op.AppGlobal.get_ex_uint64(
            proposal_id, pcfg.GS_KEY_STATUS
        )
        assert status_exists, err.MISSING_KEY
        return status

    @subroutine
    def get_proposal_proposer(self, proposal_id: UInt64) -> Account:
        proposer_bytes, proposer_exists = op.AppGlobal.get_ex_bytes(
            proposal_id, pcfg.GS_KEY_PROPOSER
        )
        assert proposer_exists, err.MISSING_KEY
        return Account(proposer_bytes)

    @subroutine
    def get_proposal_requested_amount(self, proposal_id: UInt64) -> UInt64:
        requested_amount, requested_amount_exists = op.AppGlobal.get_ex_uint64(
            proposal_id, pcfg.GS_KEY_REQUESTED_AMOUNT
        )
        assert requested_amount_exists, err.MISSING_KEY
        return requested_amount

    @subroutine
    def disburse_funds(self, recipient: Account, amount: UInt64) -> None:
        # Transfer the funds to the receiver
        itxn.Payment(receiver=recipient, amount=amount, fee=0).submit()

        # Update the outstanding funds
        self.outstanding_funds.value -= amount

    @subroutine
    def valid_xgov_payment(self, payment: gtxn.PaymentTransaction) -> bool:
        return (
            payment.receiver == Global.current_application_address
            and payment.amount == self.xgov_fee.value
        )

    @subroutine
    def valid_kyc(self, address: Account) -> bool:
        return (
            self.proposer_box[address].kyc_status.native
            and self.proposer_box[address].kyc_expiring.as_uint64()
            > Global.latest_timestamp
        )

    @subroutine
    def relative_to_absolute_amount(
        self, amount: UInt64, fraction_in_bps: UInt64
    ) -> UInt64:
        return amount * fraction_in_bps // BPS

    @subroutine
    def calc_box_map_mbr(
        self, key_prefix_length: UInt64, key_type_size: UInt64, value_type_size: UInt64
    ) -> UInt64:
        """
        Calculates the MBR (Minimum Box Requirement) for a BoxMap.

        Args:
            key_prefix_length (UInt64): The length of the key prefix in bytes
            key_type_size (UInt64): The size of the key type in bytes
            value_type_size (UInt64): The size of the value type in bytes

        Returns:
            UInt64: The calculated MBR for the BoxMap
        """
        return (
            key_prefix_length + key_type_size + value_type_size
        ) * PER_BYTE_IN_BOX_MBR + PER_BOX_MBR

    @subroutine
    def set_max_committee_size(
        self,
        open_proposal_fee: UInt64,
        daemon_ops_funding_bps: UInt64,
        voter_mbr: UInt64,
    ) -> None:
        """
        Sets the maximum committee size based on the open proposal fee.

        Args:
            open_proposal_fee (UInt64): The open proposal fee to calculate the maximum committee size
            daemon_ops_funding_bps (UInt64): The basis points for daemon operations funding
            voter_mbr (UInt64): Voter Box MBR
        """

        daemon_ops_funding = self.relative_to_absolute_amount(
            open_proposal_fee, daemon_ops_funding_bps
        )

        to_substract = (
            UInt64(MAX_MBR_PER_APP + MAX_MBR_PER_BOX + ACCOUNT_MBR) + daemon_ops_funding
        )

        assert open_proposal_fee > to_substract, err.INVALID_OPEN_PROPOSAL_FEE

        mbr_available_for_committee = open_proposal_fee - to_substract

        self.max_committee_size.value = mbr_available_for_committee // voter_mbr

    @subroutine
    def decrement_pending_proposals(self, proposal_id: UInt64) -> None:
        # Decrement pending proposals count
        self.pending_proposals.value -= 1

        # Update proposer's active proposal status
        proposer = self.get_proposal_proposer(proposal_id)
        self.proposer_box[proposer].active_proposal = arc4.Bool(False)  # noqa: FBT003

    @subroutine
    def make_xgov_box(self, voting_address: arc4.Address) -> typ.XGovBoxValue:
        """
        Creates a new xGov box with the given voting address.

        Args:
            voting_address (arc4.Address): The address of the voting account for the xGov

        Returns:
            typ.XGovBoxValue: The initialized xGov box value
        """
        return typ.XGovBoxValue(
            voting_address=voting_address,
            voted_proposals=arc4.UInt64(0),
            last_vote_timestamp=arc4.UInt64(0),
            subscription_round=arc4.UInt64(Global.round),
        )

    @subroutine
    def make_proposer_box(
        self,
        active_proposal: arc4.Bool,
        kyc_status: arc4.Bool,
        kyc_expiring: arc4.UInt64,
    ) -> typ.ProposerBoxValue:
        """
        Creates a new proposer box with the given parameters.

        Args:
            active_proposal (arc4.Bool): Whether the proposer has an active proposal
            kyc_status (arc4.Bool): KYC status of the proposer
            kyc_expiring (arc4.UInt64): Timestamp when the KYC expires

        Returns:
            typ.ProposerBoxValue: The initialized proposer box value
        """
        return typ.ProposerBoxValue(
            active_proposal=active_proposal,
            kyc_status=kyc_status,
            kyc_expiring=kyc_expiring,
        )

    @arc4.abimethod(create="require")
    def create(self) -> None:
        """
        Create the xGov Registry.
        """

        self.xgov_manager.value = arc4.Address(Txn.sender)
        assert self.entropy() == TemplateVar[Bytes]("entropy")

    @arc4.abimethod()
    def init_proposal_contract(self, size: arc4.UInt64) -> None:
        """
        Initializes the Proposal Approval Program contract.

        Args:
            size (arc4.UInt64): The size of the Proposal Approval Program contract

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

        _box, exist = self.proposal_approval_program.maybe()
        if exist:
            self.proposal_approval_program.resize(size.as_uint64())
        else:
            # Initialize the Proposal Approval Program contract
            self.proposal_approval_program.create(size=size.as_uint64())

    @arc4.abimethod()
    def load_proposal_contract(self, offset: arc4.UInt64, data: Bytes) -> None:
        """
        Loads the Proposal Approval Program contract.

        Args:
            offset (arc4.UInt64): The offset in the Proposal Approval Program contract
            data (Bytes): The data to load into the Proposal Approval Program contract

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

        # Load the Proposal Approval Program contract
        self.proposal_approval_program.replace(
            start_index=offset.as_uint64(), value=data
        )

    @arc4.abimethod()
    def delete_proposal_contract_box(self) -> None:
        """
        Deletes the Proposal Approval Program contract box.

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

        # Delete the Proposal Approval Program contract box
        self.proposal_approval_program.delete()

    @arc4.abimethod()
    def pause_registry(self) -> None:
        """
        Pauses the xGov Registry non-administrative methods.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_registry.value = UInt64(1)

    @arc4.abimethod()
    def pause_proposals(self) -> None:
        """
        Pauses the creation of new Proposals.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_proposals.value = UInt64(1)

    @arc4.abimethod()
    def resume_registry(self) -> None:
        """
        Resumes the xGov Registry non-administrative methods.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_registry.value = UInt64(0)

    @arc4.abimethod()
    def resume_proposals(self) -> None:
        """
        Resumes the creation of new Proposals.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_proposals.value = UInt64(0)

    @arc4.abimethod()
    def set_xgov_manager(self, manager: arc4.Address) -> None:
        """
        Sets the xGov Manager.

        Args:
            manager (arc4.Address): Address of the new xGov Manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_manager.value = manager

    @arc4.abimethod()
    def set_payor(self, payor: arc4.Address) -> None:
        """
        Sets the xGov Payor.

        Args:
            payor (arc4.Address): Address of the new xGov Payor

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_payor.value = payor

    @arc4.abimethod()
    def set_xgov_council(self, council: arc4.Address) -> None:
        """
        Sets the xGov Council.

        Args:
            council (arc4.Address): Address of the new xGov Council

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_council.value = council

    @arc4.abimethod()
    def set_xgov_subscriber(self, subscriber: arc4.Address) -> None:
        """
        Sets the xGov Subscriber.

        Args:
            subscriber (arc4.Address): Address of the new xGov Subscriber

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_subscriber.value = subscriber

    @arc4.abimethod()
    def set_kyc_provider(self, provider: arc4.Address) -> None:
        """
        Sets the KYC provider.

        Args:
            provider (arc4.Address): Address of the new KYC Provider

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.kyc_provider.value = provider

    @arc4.abimethod()
    def set_committee_manager(self, manager: arc4.Address) -> None:
        """
        Sets the Committee Manager.

        Args:
            manager (arc4.Address): Address of the new xGov Manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.committee_manager.value = manager

    @arc4.abimethod()
    def set_xgov_daemon(self, xgov_daemon: arc4.Address) -> None:
        """
        Sets the xGov Daemon.

        Args:
            xgov_daemon (arc4.Address): Address of the new xGov Daemon

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_daemon.value = xgov_daemon

    @arc4.abimethod()
    def config_xgov_registry(self, config: typ.XGovRegistryConfig) -> None:
        """
        Sets the configuration of the xGov Registry.

        Args:
            config (arc4.Struct): Configuration class containing the field data

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
            err.NO_PENDING_PROPOSALS: If there are currently pending proposals
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert self.no_pending_proposals(), err.NO_PENDING_PROPOSALS

        # ⚠️ WARNING: Any update that modifies Box MBRs must be followed by a
        # reconfiguration of the Registry to ensure consistency
        xgov_box_mbr = self.calc_box_map_mbr(
            self.xgov_box.key_prefix.length,
            size_of(Account),
            size_of(typ.XGovBoxValue),
        )

        xgov_request_box_mbr = self.calc_box_map_mbr(
            self.request_box.key_prefix.length,
            size_of(UInt64),
            size_of(typ.XGovSubscribeRequestBoxValue),
        )

        proposer_box_mbr = self.calc_box_map_mbr(
            self.proposer_box.key_prefix.length,
            size_of(Account),
            size_of(typ.ProposerBoxValue),
        )

        voter_mbr = self.calc_box_map_mbr(
            self.voters.key_prefix.length,
            size_of(Account),
            size_of(UInt64),
        )

        assert (
            config.xgov_fee.as_uint64() >= xgov_box_mbr
            and config.xgov_fee.as_uint64() >= xgov_request_box_mbr
        ), err.INVALID_XGOV_FEE

        assert (
            config.proposer_fee.as_uint64() >= proposer_box_mbr
        ), err.INVALID_PROPOSER_FEE

        assert (
            config.min_requested_amount.as_uint64()
            < config.max_requested_amount[0].as_uint64()
            < config.max_requested_amount[1].as_uint64()
            < config.max_requested_amount[2].as_uint64()
        ), err.INCOSISTENT_REQUESTED_AMOUNT_CONFIG

        self.set_max_committee_size(
            config.open_proposal_fee.as_uint64(),
            config.daemon_ops_funding_bps.as_uint64(),
            voter_mbr,
        )

        assert (
            config.discussion_duration[0].as_uint64()
            <= config.discussion_duration[1].as_uint64()
            <= config.discussion_duration[2].as_uint64()
            <= config.discussion_duration[3].as_uint64()
        ), err.INCOSISTENT_DISCUSSION_DURATION_CONFIG

        assert (
            config.voting_duration[0].as_uint64()
            <= config.voting_duration[1].as_uint64()
            <= config.voting_duration[2].as_uint64()
            <= config.voting_duration[3].as_uint64()
        ), err.INCOSISTENT_VOTING_DURATION_CONFIG

        assert (
            config.quorum[0].as_uint64()
            < config.quorum[1].as_uint64()
            < config.quorum[2].as_uint64()
        ), err.INCOSISTENT_QUORUM_CONFIG

        assert (
            config.weighted_quorum[0].as_uint64()
            < config.weighted_quorum[1].as_uint64()
            < config.weighted_quorum[2].as_uint64()
        ), err.INCOSISTENT_WEIGHTED_QUORUM_CONFIG

        self.xgov_fee.value = config.xgov_fee.as_uint64()
        self.proposer_fee.value = config.proposer_fee.as_uint64()
        self.open_proposal_fee.value = config.open_proposal_fee.as_uint64()
        self.daemon_ops_funding_bps.value = config.daemon_ops_funding_bps.as_uint64()
        self.proposal_commitment_bps.value = config.proposal_commitment_bps.as_uint64()

        self.min_requested_amount.value = config.min_requested_amount.as_uint64()
        self.max_requested_amount_small.value = config.max_requested_amount[
            0
        ].as_uint64()
        self.max_requested_amount_medium.value = config.max_requested_amount[
            1
        ].as_uint64()
        self.max_requested_amount_large.value = config.max_requested_amount[
            2
        ].as_uint64()

        self.discussion_duration_small.value = config.discussion_duration[0].as_uint64()
        self.discussion_duration_medium.value = config.discussion_duration[
            1
        ].as_uint64()
        self.discussion_duration_large.value = config.discussion_duration[2].as_uint64()
        self.discussion_duration_xlarge.value = config.discussion_duration[
            3
        ].as_uint64()

        self.voting_duration_small.value = config.voting_duration[0].as_uint64()
        self.voting_duration_medium.value = config.voting_duration[1].as_uint64()
        self.voting_duration_large.value = config.voting_duration[2].as_uint64()
        self.voting_duration_xlarge.value = config.voting_duration[3].as_uint64()

        self.quorum_small.value = config.quorum[0].as_uint64()
        self.quorum_medium.value = config.quorum[1].as_uint64()
        self.quorum_large.value = config.quorum[2].as_uint64()

        self.weighted_quorum_small.value = config.weighted_quorum[0].as_uint64()
        self.weighted_quorum_medium.value = config.weighted_quorum[1].as_uint64()
        self.weighted_quorum_large.value = config.weighted_quorum[2].as_uint64()

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_xgov_registry(self) -> None:
        """
        Updates the xGov Registry contract.

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

    @arc4.abimethod()
    def subscribe_xgov(
        self, voting_address: arc4.Address, payment: gtxn.PaymentTransaction
    ) -> None:
        """
        Subscribes the sender to being an xGov.

        Args:
            voting_address (arc4.Address): The address of the voting account for the xGov
            payment (gtxn.PaymentTransaction): The payment transaction covering the xGov fee

        Raises:
            err.ALREADY_XGOV: If the sender is already an xGov
            err.INVALID_PAYMENT: If payment has wrong amount (not equal to xgov_fee global state key) or wrong receiver
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        assert Txn.sender not in self.xgov_box, err.ALREADY_XGOV
        # check payment
        assert self.valid_xgov_payment(payment), err.INVALID_PAYMENT

        # create box
        self.xgov_box[Txn.sender] = self.make_xgov_box(voting_address)
        self.xgovs.value += 1

    @arc4.abimethod()
    def unsubscribe_xgov(self, xgov_address: arc4.Address) -> None:
        """
        Unsubscribes the designated address from being an xGov.

        Args:
            xgov_address (arc4.Address): The address of the xGov to unsubscribe

        Raises:
            err.UNAUTHORIZED: If the sender is not currently an xGov
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # ensure the provided address is an xGov
        assert xgov_address.native in self.xgov_box, err.UNAUTHORIZED
        # get the voting address
        voting_address = self.xgov_box[xgov_address.native].voting_address.native
        # ensure the sender is the xGov or the voting address
        assert (
            xgov_address.native == Txn.sender or voting_address == Txn.sender
        ), err.UNAUTHORIZED

        # delete box
        del self.xgov_box[xgov_address.native]
        self.xgovs.value -= 1

    @arc4.abimethod()
    def request_subscribe_xgov(
        self,
        xgov_address: arc4.Address,
        owner_address: arc4.Address,
        relation_type: arc4.UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> None:
        """
        Requests to subscribe to the xGov.

        Args:
            xgov_address (arc4.Address): The address of the xGov
            owner_address (arc4.Address): The address of the xGov Address owner/controller (Voting Address)
            relation_type (arc4.UInt64): The type of relationship enum
            payment (gtxn.PaymentTransaction): The payment transaction covering the xGov fee

        Raises:
            err.UNAUTHORIZED: If the sender is not the declared Application owner address
            err.ALREADY_XGOV: If the sender is already an xGov
            err.INVALID_PAYMENT: If payment has wrong amount (not equal to xgov_fee global state key) or wrong receiver
        """

        assert Txn.sender == owner_address.native, err.UNAUTHORIZED
        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # ensure the xgov_address is not already an xGov
        assert xgov_address.native not in self.xgov_box, err.ALREADY_XGOV

        # check payment
        assert self.valid_xgov_payment(payment), err.INVALID_PAYMENT

        # create request box
        rid = self.request_id.value
        self.request_box[rid] = typ.XGovSubscribeRequestBoxValue(
            xgov_addr=xgov_address,
            owner_addr=owner_address,
            relation_type=relation_type,
        )

        # increment request id
        self.request_id.value += 1

    @arc4.abimethod()
    def approve_subscribe_xgov(self, request_id: arc4.UInt64) -> None:
        """
        Approves a subscribe request to xGov.

        Args:
            request_id (arc4.UInt64): The ID of the request to approve

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
        """

        assert self.is_xgov_subscriber(), err.UNAUTHORIZED

        # get the request
        request = self.request_box[request_id.as_uint64()].copy()
        # create the xGov
        self.xgov_box[request.xgov_addr.native] = self.make_xgov_box(request.owner_addr)
        self.xgovs.value += 1
        # delete the request
        del self.request_box[request_id.as_uint64()]

    @arc4.abimethod()
    def reject_subscribe_xgov(self, request_id: arc4.UInt64) -> None:
        """
        Rejects a subscribe request to xGov.

        Args:
            request_id (arc4.UInt64): The ID of the request to reject

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
        """

        assert self.is_xgov_subscriber(), err.UNAUTHORIZED

        # delete the request
        del self.request_box[request_id.as_uint64()]

    @arc4.abimethod()
    def set_voting_account(
        self, xgov_address: arc4.Address, voting_address: arc4.Address
    ) -> None:
        """
        Sets the Voting Address for the xGov.

        Args:
            xgov_address (arc4.Address): The xGov address delegating voting power
            voting_address (arc4.Address): The voting account address to delegate voting power to

        Raises:
            err.UNAUTHORIZED: If the sender is not currently an xGov
            err.VOTING_ADDRESS_MUST_BE_DIFFERENT: If the new voting account is the same as currently set
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # Check if the sender is an xGov member
        exists = xgov_address.native in self.xgov_box
        assert exists, err.UNAUTHORIZED
        xgov_box = self.xgov_box[xgov_address.native].copy()

        # Check that the sender is either the xGov or the voting address
        assert (
            Txn.sender == xgov_box.voting_address.native
            or Txn.sender == xgov_address.native
        ), err.UNAUTHORIZED

        # Update the voting account in the xGov box
        self.xgov_box[xgov_address.native].voting_address = voting_address

    @arc4.abimethod()
    def subscribe_proposer(self, payment: gtxn.PaymentTransaction) -> None:
        """
        Subscribes the sender to being a Proposer.

        Args:
            payment (gtxn.PaymentTransaction): The payment transaction covering the Proposer fee

        Raises:
            err.ALREADY_PROPOSER: If the sender is already a Proposer
            err.WRONG_RECEIVER: If the payment receiver is not the xGov Registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment amount is not equal to the proposer_fee global state key
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        assert Txn.sender not in self.proposer_box, err.ALREADY_PROPOSER
        # check fee
        assert (
            payment.receiver == Global.current_application_address
        ), err.WRONG_RECEIVER
        assert payment.amount == self.proposer_fee.value, err.WRONG_PAYMENT_AMOUNT

        self.proposer_box[Txn.sender] = self.make_proposer_box(
            arc4.Bool(False), arc4.Bool(False), arc4.UInt64(0)  # noqa: FBT003
        )

    @arc4.abimethod()
    def set_proposer_kyc(
        self, proposer: arc4.Address, kyc_status: arc4.Bool, kyc_expiring: arc4.UInt64
    ) -> None:
        """
        Sets a proposer's KYC status.

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

        self.proposer_box[proposer.native] = self.make_proposer_box(
            active_proposal, kyc_status, kyc_expiring
        )

    @arc4.abimethod()
    def declare_committee(
        self, committee_id: typ.Bytes32, size: arc4.UInt64, votes: arc4.UInt64
    ) -> None:
        """
        Sets the xGov Committee in charge.

        Args:
            committee_id (typ.Bytes32): The ID of the xGov Committee
            size (arc4.UInt64): The size of the xGov Committee
            votes (arc4.UInt64): The voting power of the xGov Committee

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
            err.WRONG_CID_LENGTH: If the committee ID is not of the correct length
            err.COMMITTEE_SIZE_TOO_LARGE: If the committee size exceeds the maximum allowed size
        """

        assert self.is_xgov_committee_manager(), err.UNAUTHORIZED
        assert committee_id.length == pcts.COMMITTEE_ID_LENGTH, err.WRONG_CID_LENGTH
        assert (
            size.as_uint64() <= self.max_committee_size.value
        ), err.COMMITTEE_SIZE_TOO_LARGE

        self.committee_id.value = committee_id.copy()
        self.committee_members.value = size.as_uint64()
        self.committee_votes.value = votes.as_uint64()

    @arc4.abimethod
    def open_proposal(self, payment: gtxn.PaymentTransaction) -> UInt64:
        """
        Creates a new Proposal.

        Args:
            payment (gtxn.PaymentTransaction): payment for covering the proposal fee (includes child contract MBR)

        Raises:
            err.UNAUTHORIZED: If the sender is not a Proposer
            err.ALREADY_ACTIVE_PROPOSAL: If the proposer already has an active proposal
            err.INVALID_KYC: If the Proposer does not have valid KYC
            err.INSUFFICIENT_FEE: If the fee for the current transaction doesn't cover the inner transaction fees
            err.WRONG_RECEIVER: If the payment receiver is not the xGov Registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment amount is not equal to the open_proposal_fee global state key
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert not self.paused_proposals.value, err.PAUSED_PROPOSALS

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
        assert payment.amount == self.open_proposal_fee.value, err.WRONG_PAYMENT_AMOUNT

        mbr_before = Global.current_application_address.balance

        proposal_approval, exist = self.proposal_approval_program.maybe()
        assert exist, err.MISSING_PROPOSAL_APPROVAL_PROGRAM

        # clear_state_program is a tuple of 2 Bytes elements where each is max 4096 bytes
        # we only use the first element here as we assume the clear state program is small enough
        compiled_clear_state_1, _compiled_clear_state_2 = compile_contract(
            proposal_contract.Proposal
        ).clear_state_program

        bytes_per_page = UInt64(BYTES_PER_APP_PAGE)
        total_size = proposal_approval.length + compiled_clear_state_1.length
        extra_pages = total_size // bytes_per_page

        error, tx = arc4.abi_call(
            proposal_contract.Proposal.create,
            Txn.sender,
            approval_program=proposal_approval,
            clear_state_program=compiled_clear_state_1,
            global_num_uint=pcfg.GLOBAL_UINTS,
            global_num_bytes=pcfg.GLOBAL_BYTES,
            extra_program_pages=extra_pages,
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.MISSING_CONFIG:
                    assert False, err.MISSING_CONFIG  # noqa
                case err.EMPTY_COMMITTEE_ID:
                    assert False, err.EMPTY_COMMITTEE_ID  # noqa
                case err.WRONG_COMMITTEE_MEMBERS:
                    assert False, err.WRONG_COMMITTEE_MEMBERS  # noqa
                case err.WRONG_COMMITTEE_VOTES:
                    assert False, err.WRONG_COMMITTEE_VOTES  # noqa
                case _:
                    assert False, "Unknown error"  # noqa
        else:
            assert error.native == "", "Unknown error"

        mbr_after = Global.current_application_address.balance

        # Update proposer state
        self.proposer_box[Txn.sender].active_proposal = arc4.Bool(True)  # noqa: FBT003

        # Transfer funds to the new Proposal App, excluding the MBR needed for the Proposal App
        itxn.Payment(
            receiver=tx.created_app.address,
            amount=self.open_proposal_fee.value - (mbr_after - mbr_before),
            fee=0,
        ).submit()

        # Increment pending proposals
        self.pending_proposals.value += 1

        return tx.created_app.id

    @arc4.abimethod()
    def vote_proposal(
        self,
        proposal_id: arc4.UInt64,
        xgov_address: arc4.Address,
        approval_votes: arc4.UInt64,
        rejection_votes: arc4.UInt64,
    ) -> None:
        """
        Votes on a Proposal.

        Args:
            proposal_id (arc4.UInt64): The application ID of the Proposal app being voted on
            xgov_address: (arc4.Address): The address of the xGov being voted on behalf of
            approval_votes: (arc4.UInt64): The number of approvals votes allocated
            rejection_votes: (arc4.UInt64): The number of rejections votes allocated

        Raises:
            err.INVALID_PROPOSAL: If the Proposal ID is not a Proposal contract
            err.PROPOSAL_IS_NOT_VOTING: If the Proposal is not in a voting session
            err.UNAUTHORIZED: If the xGov_address is not an xGov
            err.MUST_BE_VOTING_ADDRESS: If the sender is not the voting_address
            err.PAUSED_REGISTRY: If the xGov Registry is paused
            err.WRONG_PROPOSAL_STATUS: If the Proposal is not in the voting state
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.VOTER_NOT_FOUND: If the xGov is not found in the Proposal's voting registry
            err.VOTER_ALREADY_VOTED: If the xGov has already voted on this Proposal
            err.VOTES_EXCEEDED: If the total votes exceed the maximum allowed
            err.VOTING_PERIOD_EXPIRED: If the voting period for the Proposal has expired
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # verify proposal id is genuine proposal
        assert self._is_proposal(proposal_id.as_uint64()), err.INVALID_PROPOSAL

        # make sure they're voting on behalf of an xGov
        exists = xgov_address.native in self.xgov_box
        assert exists, err.UNAUTHORIZED
        xgov_box = self.xgov_box[xgov_address.native].copy()
        self.xgov_box[xgov_address.native].voted_proposals = arc4.UInt64(
            xgov_box.voted_proposals.as_uint64() + UInt64(1)
        )
        self.xgov_box[xgov_address.native].last_vote_timestamp = arc4.UInt64(
            Global.latest_timestamp
        )

        # Verify the caller is using their voting address
        assert Txn.sender == xgov_box.voting_address.native, err.MUST_BE_VOTING_ADDRESS

        # Call the Proposal App to register the vote
        error, _tx = arc4.abi_call(
            proposal_contract.Proposal.vote,
            xgov_address,
            approval_votes,
            rejection_votes,
            app_id=proposal_id.as_uint64(),
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case err.MISSING_CONFIG:
                    assert False, err.MISSING_CONFIG  # noqa
                case err.VOTER_NOT_FOUND:
                    assert False, err.VOTER_NOT_FOUND  # noqa
                case err.VOTES_EXCEEDED:
                    assert False, err.VOTES_EXCEEDED  # noqa
                case err.VOTING_PERIOD_EXPIRED:
                    assert False, err.VOTING_PERIOD_EXPIRED  # noqa
                case _:
                    assert False, "Unknown error"  # noqa
        else:
            assert error.native == "", "Unknown error"

    @arc4.abimethod()
    def pay_grant_proposal(self, proposal_id: arc4.UInt64) -> None:
        """
        Disburses the funds for an approved Proposal.

        Args:
            proposal_id (arc4.UInt64): The application ID of the approved Proposal

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Payor
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.PROPOSAL_IS_NOT_APPROVED: If the proposal status is not approved
            err.WRONG_PROPOSER: If the Proposer on the proposal is not found
            err.INVALID_KYC: If the Proposer KYC is invalid or expired
            err.INSUFFICIENT_TREASURY_FUNDS: If the xGov Registry does not have enough funds for the disbursement
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not as expected
        """

        # Verify the caller is the xGov Payor
        assert arc4.Address(Txn.sender) == self.xgov_payor.value, err.UNAUTHORIZED

        # Verify proposal_id is a genuine proposal created by this registry
        assert self._is_proposal(proposal_id.as_uint64()), err.INVALID_PROPOSAL

        # Read proposal state directly from the Proposal App's global state
        proposer = self.get_proposal_proposer(proposal_id.as_uint64())
        requested_amount = self.get_proposal_requested_amount(proposal_id.as_uint64())

        assert proposer in self.proposer_box, err.WRONG_PROPOSER

        assert self.valid_kyc(proposer), err.INVALID_KYC

        # Verify sufficient funds are available
        assert (
            self.outstanding_funds.value >= requested_amount
        ), err.INSUFFICIENT_TREASURY_FUNDS

        self.disburse_funds(proposer, requested_amount)

        error, _tx = arc4.abi_call(
            proposal_contract.Proposal.fund, app_id=proposal_id.as_uint64()
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case _:
                    assert False, "Unknown error"  # noqa
        else:
            assert error.native == "", "Unknown error"

    @arc4.abimethod()
    def finalize_proposal(self, proposal_id: arc4.UInt64) -> None:
        """
        Finalize a Proposal.

        Args:
            proposal_id (arc4.UInt64): The application ID of the Proposal app to finalize

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Daemon
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not as expected
            err.MISSING_CONFIG: If one of the required configuration values is missing
            err.VOTERS_ASSIGNED: If there are still assigned voters
        """

        proposal_status = self.get_proposal_status(proposal_id.as_uint64())
        if proposal_status == UInt64(penm.STATUS_EMPTY) or proposal_status == UInt64(
            penm.STATUS_DRAFT
        ):
            assert arc4.Address(Txn.sender) == self.xgov_daemon.value, err.UNAUTHORIZED

        # Verify proposal_id is a genuine proposal created by this registry
        assert self._is_proposal(proposal_id.as_uint64()), err.INVALID_PROPOSAL

        error, _tx = arc4.abi_call(
            proposal_contract.Proposal.finalize, app_id=proposal_id.as_uint64()
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case err.MISSING_CONFIG:
                    assert False, err.MISSING_CONFIG  # noqa
                case err.VOTERS_ASSIGNED:
                    assert False, err.VOTERS_ASSIGNED  # noqa
                case _:
                    assert False, "Unknown error"  # noqa
        else:
            assert error.native == "", "Unknown error"

        self.decrement_pending_proposals(proposal_id.as_uint64())

    @arc4.abimethod()
    def drop_proposal(self, proposal_id: arc4.UInt64) -> None:
        """
        Drops a Proposal.

        Args:
            proposal_id (arc4.UInt64): The application ID of the Proposal app to drop

        Raises:
            err.PAUSED_REGISTRY: If the registry is paused
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not as expected
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # Verify proposal_id is a genuine proposal created by this registry
        assert self._is_proposal(proposal_id.as_uint64()), err.INVALID_PROPOSAL

        proposer = self.get_proposal_proposer(proposal_id.as_uint64())
        assert Txn.sender == proposer, err.UNAUTHORIZED

        error, _tx = arc4.abi_call(
            proposal_contract.Proposal.drop, app_id=proposal_id.as_uint64()
        )

        if error.native.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.native.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    assert False, err.WRONG_PROPOSAL_STATUS  # noqa
                case _:
                    assert False, "Unknown error"  # noqa
        else:
            assert error.native == "", "Unknown error"

        self.decrement_pending_proposals(proposal_id.as_uint64())

    @arc4.abimethod()
    def deposit_funds(self, payment: gtxn.PaymentTransaction) -> None:
        """
        Deposits xGov program funds into the xGov Treasury (xGov Registry Account).

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
    def withdraw_funds(self, amount: arc4.UInt64) -> None:
        """
        Remove xGov program funds from the xGov Treasury (xGov Registry Account).

        Args:
            amount (UInt64): the amount to remove

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
            err.INSUFFICIENT_FUNDS: If the requested amount is greater than the outstanding funds available
            err.INSUFFICIENT_FEE: If the fee is not enough to cover the inner transaction to send the funds back
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert (
            amount.as_uint64() <= self.outstanding_funds.value
        ), err.INSUFFICIENT_FUNDS
        assert Txn.fee >= (Global.min_txn_fee * 2), err.INSUFFICIENT_FEE
        self.outstanding_funds.value -= amount.as_uint64()

        itxn.Payment(
            receiver=self.xgov_manager.value.native,
            amount=amount.as_uint64(),
            fee=0,
        ).submit()

    @arc4.abimethod()
    def withdraw_balance(self) -> None:
        """
        Withdraw outstanding Algos, excluding MBR and outstanding funds, from the xGov Registry.

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
            err.INSUFFICIENT_FUNDS: If there are no funds to withdraw
            err.INSUFFICIENT_FEE: If the fee is not enough to cover the inner transaction to send the funds back

        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        assert Txn.fee >= (Global.min_txn_fee * 2), err.INSUFFICIENT_FEE

        # Calculate the amount to withdraw
        amount = (
            Global.current_application_address.balance
            - Global.current_application_address.min_balance
            - self.outstanding_funds.value
        )

        assert amount > 0, err.INSUFFICIENT_FUNDS
        itxn.Payment(
            receiver=self.xgov_manager.value.native,
            amount=amount,
            fee=0,
        ).submit()

    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.TypedGlobalState:
        """
        Returns the xGov Registry state.
        """

        return typ.TypedGlobalState(
            paused_registry=arc4.Bool(bool(self.paused_registry.value)),
            paused_proposals=arc4.Bool(bool(self.paused_proposals.value)),
            xgov_manager=self.xgov_manager.value,
            xgov_payor=self.xgov_payor.value,
            xgov_council=self.xgov_council.value,
            xgov_subscriber=self.xgov_subscriber.value,
            kyc_provider=self.kyc_provider.value,
            committee_manager=self.committee_manager.value,
            xgov_daemon=self.xgov_daemon.value,
            xgov_fee=arc4.UInt64(self.xgov_fee.value),
            proposer_fee=arc4.UInt64(self.proposer_fee.value),
            open_proposal_fee=arc4.UInt64(self.open_proposal_fee.value),
            daemon_ops_funding_bps=arc4.UInt64(self.daemon_ops_funding_bps.value),
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

    @arc4.abimethod(readonly=True)
    def get_xgov_box(self, xgov_address: arc4.Address) -> tuple[typ.XGovBoxValue, bool]:
        """
        Returns the xGov box for the given address.

        Args:
            xgov_address (arc4.Address): The address of the xGov

        Returns:
            typ.XGovBoxValue: The xGov box value
            bool: `True` if xGov box exists, else `False`
        """
        exists = xgov_address.native in self.xgov_box
        if exists:
            val = self.xgov_box[xgov_address.native].copy()
        else:
            val = typ.XGovBoxValue(
                voting_address=arc4.Address(),
                voted_proposals=arc4.UInt64(0),
                last_vote_timestamp=arc4.UInt64(0),
                subscription_round=arc4.UInt64(0),
            )

        return val.copy(), exists

    @arc4.abimethod(readonly=True)
    def get_proposer_box(
        self,
        proposer_address: arc4.Address,
    ) -> tuple[typ.ProposerBoxValue, bool]:
        """
        Returns the Proposer box for the given address.

        Args:
            proposer_address (arc4.Address): The address of the Proposer

        Returns:
            typ.ProposerBoxValue: The Proposer box value
            bool: `True` if Proposer box exists, else `False`
        """
        exists = proposer_address.native in self.proposer_box
        if exists:
            val = self.proposer_box[proposer_address.native].copy()
        else:
            val = typ.ProposerBoxValue(
                active_proposal=arc4.Bool(),
                kyc_status=arc4.Bool(),
                kyc_expiring=arc4.UInt64(0),
            )

        return val.copy(), exists

    @arc4.abimethod(readonly=True)
    def get_request_box(
        self,
        request_id: arc4.UInt64,
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        """
        Returns the xGov subscribe request box for the given request ID.

        Args:
            request_id (arc4.UInt64): The ID of the subscribe request

        Returns:
            typ.XGovSubscribeRequestBoxValue: The subscribe request box value
            bool: `True` if xGov subscribe request box exists, else `False`
        """
        exists = request_id.as_uint64() in self.request_box
        if exists:
            val = self.request_box[request_id.as_uint64()].copy()
        else:
            val = typ.XGovSubscribeRequestBoxValue(
                xgov_addr=arc4.Address(),
                owner_addr=arc4.Address(),
                relation_type=arc4.UInt64(0),
            )

        return val.copy(), exists

    @arc4.abimethod()
    def is_proposal(self, proposal_id: arc4.UInt64) -> None:
        assert self._is_proposal(proposal_id.as_uint64()), err.INVALID_PROPOSAL
