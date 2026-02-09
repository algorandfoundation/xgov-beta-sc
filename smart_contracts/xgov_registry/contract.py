from algopy import (
    Account,
    Application,
    Array,
    Box,
    BoxMap,
    Bytes,
    FixedArray,
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
)

import smart_contracts.common.abi_types as typ
import smart_contracts.errors.std_errors as err
from smart_contracts.interfaces.xgov_registry import XGovRegistryInterface

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
    PROPOSAL_APPROVAL_PAGES,
)


class XGovRegistry(
    XGovRegistryInterface,
    state_totals=StateTotals(
        global_bytes=cfg.GLOBAL_BYTES,
        global_uints=cfg.GLOBAL_UINTS,
        local_bytes=cfg.LOCAL_BYTES,
        local_uints=cfg.LOCAL_UINTS,
    ),
):
    """xGov Registry Contract"""

    def __init__(self) -> None:
        # Preconditions
        assert Txn.global_num_byte_slice == cfg.GLOBAL_BYTES, err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

        # Role-Based Access Control (RBAC)
        self.xgov_manager = GlobalState(Account(), key=cfg.GS_KEY_XGOV_MANAGER)
        self.xgov_subscriber = GlobalState(Account(), key=cfg.GS_KEY_XGOV_SUBSCRIBER)
        self.xgov_payor = GlobalState(Account(), key=cfg.GS_KEY_XGOV_PAYOR)
        self.xgov_council = GlobalState(Account(), key=cfg.GS_KEY_XGOV_COUNCIL)
        self.kyc_provider = GlobalState(Account(), key=cfg.GS_KEY_KYC_PROVIDER)
        self.committee_manager = GlobalState(
            Account(), key=cfg.GS_KEY_COMMITTEE_MANAGER
        )
        self.xgov_daemon = GlobalState(Account(), key=cfg.GS_KEY_XGOV_DAEMON)

        # Registry Control States
        self.paused_registry = GlobalState(
            False, key=cfg.GS_KEY_PAUSED_REGISTRY  # noqa: FBT003
        )
        self.paused_proposals = GlobalState(
            False, key=cfg.GS_KEY_PAUSED_PROPOSALS  # noqa: FBT003
        )

        # xGov Treasury
        self.outstanding_funds = GlobalState(UInt64(), key=cfg.GS_KEY_OUTSTANDING_FUNDS)

        # Fees
        self.xgov_fee = GlobalState(UInt64(), key=cfg.GS_KEY_XGOV_FEE)
        self.proposer_fee = GlobalState(UInt64(), key=cfg.GS_KEY_PROPOSER_FEE)
        self.open_proposal_fee = GlobalState(UInt64(), key=cfg.GS_KEY_OPEN_PROPOSAL_FEE)
        self.daemon_ops_funding_bps = GlobalState(
            UInt64(), key=cfg.GS_KEY_DAEMON_OPS_FUNDING_BPS
        )
        self.proposal_commitment_bps = GlobalState(
            UInt64(), key=cfg.GS_KEY_PROPOSAL_COMMITMENT_BPS
        )

        # Requested Amount Limits
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

        # Time Limits
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

        # Quorums
        self.quorum_small = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_SMALL)
        self.quorum_medium = GlobalState(
            UInt64(), key=cfg.GS_KEY_QUORUM_MEDIUM
        )  # No longer used
        self.quorum_large = GlobalState(UInt64(), key=cfg.GS_KEY_QUORUM_LARGE)

        # Weighted Quorums
        self.weighted_quorum_small = GlobalState(
            UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_SMALL
        )
        self.weighted_quorum_medium = GlobalState(
            UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_MEDIUM  # No longer used
        )
        self.weighted_quorum_large = GlobalState(
            UInt64(), key=cfg.GS_KEY_WEIGHTED_QUORUM_LARGE
        )

        # xGov Committee
        self.committee_id = GlobalState(typ.Bytes32, key=cfg.GS_KEY_COMMITTEE_ID)
        self.committee_members = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_MEMBERS)
        self.committee_votes = GlobalState(UInt64(), key=cfg.GS_KEY_COMMITTEE_VOTES)
        self.max_committee_size = GlobalState(
            UInt64(), key=cfg.GS_KEY_MAX_COMMITTEE_SIZE
        )

        # Counters
        self.xgovs = GlobalState(UInt64(), key=cfg.GS_KEY_XGOVS)
        self.pending_proposals = GlobalState(UInt64(), key=cfg.GS_KEY_PENDING_PROPOSALS)
        self.request_id = GlobalState(UInt64(), key=cfg.GS_KEY_REQUEST_ID)

        # Boxes
        self.proposal_approval_program = Box(
            Bytes, key=cfg.PROPOSAL_APPROVAL_PROGRAM_BOX
        )
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
        self.request_unsubscribe_box = BoxMap(
            UInt64,
            typ.XGovSubscribeRequestBoxValue,
            key_prefix=cfg.REQUEST_UNSUBSCRIBE_BOX_MAP_PREFIX,
        )
        self.proposer_box = BoxMap(
            Account,
            typ.ProposerBoxValue,
            key_prefix=cfg.PROPOSER_BOX_MAP_PREFIX,
        )
        # Declared here just for MBR calculation purposes, not to be used
        self.voters = BoxMap(
            Account,
            UInt64,
            key_prefix=pcfg.VOTER_BOX_KEY_PREFIX,
        )

        # New Variables (introduced after MainNet deployment)
        self.absence_tolerance = GlobalState(UInt64, key=cfg.GS_KEY_ABSENCE_TOLERANCE)
        self.governance_period = GlobalState(UInt64, key=cfg.GS_KEY_GOVERNANCE_PERIOD)
        self.committee_grace_period = GlobalState(
            UInt64, key=cfg.GS_KEY_COMMITTEE_GRACE_PERIOD
        )
        self.committee_last_anchor = GlobalState(
            UInt64, key=cfg.GS_KEY_COMMITTEE_LAST_ANCHOR
        )
        # ⚠️ No more Global UInt64 available in the State Schema, further additional
        # integers must be encoded as Global Bytes.

    def entropy(self) -> Bytes:
        return TemplateVar[Bytes]("entropy")  # trick to allow fresh deployment

    def is_xgov_manager(self) -> bool:
        return Txn.sender == self.xgov_manager.value

    def is_xgov_subscriber(self) -> bool:
        return Txn.sender == self.xgov_subscriber.value

    def is_xgov_committee_manager(self) -> bool:
        return Txn.sender == self.committee_manager.value

    def has_xgov_status(self, a: Account) -> bool:
        return a in self.xgov_box

    def is_active_xgov(self, a: Account) -> bool:
        return self.has_xgov_status(a) and self.xgov_box[a].unsubscribed_round == 0

    def caller_is_xgov_or_voting_address(self, xgov_address: Account) -> bool:
        return (
            Txn.sender == xgov_address
            or Txn.sender == self.xgov_box[xgov_address].voting_address
        )

    def _is_proposal(self, proposal: Application) -> bool:
        return proposal.creator == Global.current_application_address

    def get_proposal_status(self, proposal: Application) -> UInt64:
        status, status_exists = op.AppGlobal.get_ex_uint64(proposal, pcfg.GS_KEY_STATUS)
        assert status_exists, err.MISSING_KEY
        return status

    def get_proposal_proposer(self, proposal: Application) -> Account:
        proposer_bytes, proposer_exists = op.AppGlobal.get_ex_bytes(
            proposal, pcfg.GS_KEY_PROPOSER
        )
        assert proposer_exists, err.MISSING_KEY
        return Account(proposer_bytes)

    def get_proposal_requested_amount(self, proposal: Application) -> UInt64:
        requested_amount, requested_amount_exists = op.AppGlobal.get_ex_uint64(
            proposal, pcfg.GS_KEY_REQUESTED_AMOUNT
        )
        assert requested_amount_exists, err.MISSING_KEY
        return requested_amount

    def disburse_funds(self, recipient: Account, amount: UInt64) -> None:
        # Transfer the funds to the receiver
        itxn.Payment(receiver=recipient, amount=amount, fee=0).submit()

        # Update the outstanding funds
        self.outstanding_funds.value -= amount

    def valid_xgov_payment(self, payment: gtxn.PaymentTransaction) -> bool:
        return (
            payment.receiver == Global.current_application_address
            and payment.amount == self.xgov_fee.value
        )

    def valid_kyc(self, address: Account) -> bool:
        return (
            self.proposer_box[address].kyc_status
            and self.proposer_box[address].kyc_expiring > Global.latest_timestamp
        )

    def relative_to_absolute_amount(
        self, amount: UInt64, fraction_in_bps: UInt64
    ) -> UInt64:
        return amount * fraction_in_bps // BPS

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

    def get_committee_anchor(self) -> UInt64:
        r = Global.round
        return r - (r % self.governance_period.value)

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

    def increment_pending_proposals(self, proposer: Account) -> None:
        self.pending_proposals.value += 1
        self.proposer_box[proposer].active_proposal = True

    def decrement_pending_proposals(self, proposal: Application) -> None:
        self.pending_proposals.value -= 1
        proposer = self.get_proposal_proposer(proposal)
        self.proposer_box[proposer].active_proposal = False

    def make_xgov_box(self, voting_address: Account) -> typ.XGovBoxValue:
        """
        Creates a new xGov box with the given voting address.

        Args:
            voting_address (Account): The address of the voting account for the xGov

        Returns:
            typ.XGovBoxValue: The initialized xGov box value
        """
        return typ.XGovBoxValue(
            voting_address=voting_address,
            tolerated_absences=self.absence_tolerance.value,
            unsubscribed_round=UInt64(0),
            subscription_round=Global.round,
        )

    def subscribe_xgov_and_emit(
        self, *, xgov_address: Account, voting_address: Account
    ) -> None:
        # The following assertion may be redundant in some invocations.
        assert not self.is_active_xgov(xgov_address), err.ALREADY_XGOV
        del self.xgov_box[xgov_address]  # No effect if the xgov_box does not exist
        self.xgov_box[xgov_address] = self.make_xgov_box(voting_address)
        self.xgovs.value += 1
        arc4.emit(typ.XGovSubscribed(xgov=xgov_address, delegate=voting_address))

    def unsubscribe_xgov_and_emit(self, xgov_address: Account) -> None:
        # The following assertion may be redundant in some invocations.
        assert self.is_active_xgov(xgov_address), err.NOT_XGOV
        self.xgov_box[xgov_address].unsubscribed_round = Global.round
        self.xgovs.value -= 1
        arc4.emit(typ.XGovUnsubscribed(xgov=xgov_address))

    def make_proposer_box(
        self,
        *,
        active_proposal: bool,
        kyc_status: bool,
        kyc_expiring: UInt64,
    ) -> typ.ProposerBoxValue:
        """
        Creates a new proposer box with the given parameters.

        Args:
            active_proposal (bool): Whether the proposer has an active proposal
            kyc_status (bool): KYC status of the proposer
            kyc_expiring (UInt64): Timestamp when the KYC expires

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

        self.xgov_manager.value = Txn.sender
        assert self.entropy() == TemplateVar[Bytes]("entropy")

    @arc4.abimethod()
    def init_proposal_contract(self, *, size: UInt64) -> None:
        """
        Initializes the Proposal Approval Program contract.

        Args:
            size (UInt64): The size of the Proposal Approval Program contract

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

        if self.proposal_approval_program:
            self.proposal_approval_program.resize(size)
        else:
            # Initialize the Proposal Approval Program contract
            _created = self.proposal_approval_program.create(size=size)

    @arc4.abimethod()
    def load_proposal_contract(self, *, offset: UInt64, data: Bytes) -> None:
        """
        Loads the Proposal Approval Program contract.

        Args:
            offset (UInt64): The offset in the Proposal Approval Program contract
            data (Bytes): The data to load into the Proposal Approval Program contract

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

        # Load the Proposal Approval Program contract
        self.proposal_approval_program.replace(start_index=offset, value=data)

    @arc4.abimethod()
    def delete_proposal_contract_box(self) -> None:
        """
        Deletes the Proposal Approval Program contract box.

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

        # Delete the Proposal Approval Program contract box
        del self.proposal_approval_program.value

    @arc4.abimethod()
    def pause_registry(self) -> None:
        """
        Pauses the xGov Registry non-administrative methods.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_registry.value = True

    @arc4.abimethod()
    def pause_proposals(self) -> None:
        """
        Pauses the creation of new Proposals.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_proposals.value = True

    @arc4.abimethod()
    def resume_registry(self) -> None:
        """
        Resumes the xGov Registry non-administrative methods.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_registry.value = False

    @arc4.abimethod()
    def resume_proposals(self) -> None:
        """
        Resumes the creation of new Proposals.
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.paused_proposals.value = False

    @arc4.abimethod()
    def set_xgov_manager(self, *, manager: Account) -> None:
        """
        Sets the xGov Manager.

        Args:
            manager (Account): Address of the new xGov Manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_manager.value = manager

    @arc4.abimethod()
    def set_payor(self, *, payor: Account) -> None:
        """
        Sets the xGov Payor.

        Args:
            payor (Account): Address of the new xGov Payor

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_payor.value = payor

    @arc4.abimethod()
    def set_xgov_council(self, *, council: Account) -> None:
        """
        Sets the xGov Council.

        Args:
            council (Account): Address of the new xGov Council

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_council.value = council

    @arc4.abimethod()
    def set_xgov_subscriber(self, *, subscriber: Account) -> None:
        """
        Sets the xGov Subscriber.

        Args:
            subscriber (Account): Address of the new xGov Subscriber

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_subscriber.value = subscriber

    @arc4.abimethod()
    def set_kyc_provider(self, *, provider: Account) -> None:
        """
        Sets the KYC provider.

        Args:
            provider (Account): Address of the new KYC Provider

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.kyc_provider.value = provider

    @arc4.abimethod()
    def set_committee_manager(self, *, manager: Account) -> None:
        """
        Sets the Committee Manager.

        Args:
            manager (Account): Address of the new xGov Manager

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.committee_manager.value = manager

    @arc4.abimethod()
    def set_xgov_daemon(self, *, xgov_daemon: Account) -> None:
        """
        Sets the xGov Daemon.

        Args:
            xgov_daemon (Account): Address of the new xGov Daemon

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED
        self.xgov_daemon.value = xgov_daemon

    @arc4.abimethod()
    def config_xgov_registry(self, *, config: typ.XGovRegistryConfig) -> None:
        """
        Sets the configuration of the xGov Registry.

        Args:
            config (arc4.Struct): Configuration class containing the field data

        Raises:
            err.UNAUTHORIZED: If the sender is not the current xGov Manager
        """

        assert self.is_xgov_manager(), err.UNAUTHORIZED

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
            config.xgov_fee >= xgov_box_mbr and config.xgov_fee >= xgov_request_box_mbr
        ), err.INVALID_XGOV_FEE

        assert config.proposer_fee >= proposer_box_mbr, err.INVALID_PROPOSER_FEE

        assert (
            0
            < config.min_requested_amount
            < config.max_requested_amount[0]
            < config.max_requested_amount[1]
            < config.max_requested_amount[2]
        ), err.INCONSISTENT_REQUESTED_AMOUNT_CONFIG

        self.set_max_committee_size(
            config.open_proposal_fee,
            config.daemon_ops_funding_bps,
            voter_mbr,
        )

        assert (
            0
            < config.discussion_duration[0]
            <= config.discussion_duration[1]
            <= config.discussion_duration[2]
            <= config.discussion_duration[3]
        ), err.INCONSISTENT_DISCUSSION_DURATION_CONFIG

        assert (
            0
            < config.voting_duration[0]
            <= config.voting_duration[1]
            <= config.voting_duration[2]
            <= config.voting_duration[3]
        ), err.INCONSISTENT_VOTING_DURATION_CONFIG

        assert (
            0
            < config.quorum[0]
            # Quorum Medium no longer used
            < config.quorum[2]
        ), err.INCONSISTENT_QUORUM_CONFIG

        assert (
            0
            < config.weighted_quorum[0]
            # Weighted Quorum Medium no longer used
            < config.weighted_quorum[2]
        ), err.INCONSISTENT_WEIGHTED_QUORUM_CONFIG

        self.xgov_fee.value = config.xgov_fee
        self.proposer_fee.value = config.proposer_fee
        self.open_proposal_fee.value = config.open_proposal_fee
        self.daemon_ops_funding_bps.value = config.daemon_ops_funding_bps
        self.proposal_commitment_bps.value = config.proposal_commitment_bps

        self.min_requested_amount.value = config.min_requested_amount
        self.max_requested_amount_small.value = config.max_requested_amount[0]
        self.max_requested_amount_medium.value = config.max_requested_amount[1]
        self.max_requested_amount_large.value = config.max_requested_amount[2]

        self.discussion_duration_small.value = config.discussion_duration[0]
        self.discussion_duration_medium.value = config.discussion_duration[1]
        self.discussion_duration_large.value = config.discussion_duration[2]
        self.discussion_duration_xlarge.value = config.discussion_duration[3]

        self.voting_duration_small.value = config.voting_duration[0]
        self.voting_duration_medium.value = config.voting_duration[1]
        self.voting_duration_large.value = config.voting_duration[2]
        self.voting_duration_xlarge.value = config.voting_duration[3]

        self.quorum_small.value = config.quorum[0]
        self.quorum_medium.value = UInt64(0)  # No longer used
        self.quorum_large.value = config.quorum[2]

        self.weighted_quorum_small.value = config.weighted_quorum[0]
        self.weighted_quorum_medium.value = UInt64(0)  # No longer used
        self.weighted_quorum_large.value = config.weighted_quorum[2]

        self.absence_tolerance.value = config.absence_tolerance
        self.governance_period.value = config.governance_period
        self.committee_grace_period.value = config.committee_grace_period

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
        self, *, voting_address: Account, payment: gtxn.PaymentTransaction
    ) -> None:
        """
        Subscribes the sender to being an xGov.

        Args:
            voting_address (Account): The address of the voting account for the xGov
            payment (gtxn.PaymentTransaction): The payment transaction covering the xGov fee

        Raises:
            err.PAUSED_REGISTRY: If registry is paused
            err.ALREADY_XGOV: If the sender is already an active xGov
            err.INVALID_PAYMENT: If payment has wrong amount (not equal to xgov_fee global state key) or wrong receiver
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert not self.is_active_xgov(Txn.sender), err.ALREADY_XGOV
        assert self.valid_xgov_payment(payment), err.INVALID_PAYMENT

        self.subscribe_xgov_and_emit(
            xgov_address=Txn.sender, voting_address=voting_address
        )

    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        """
        Unsubscribes the sender from being an xGov.

        Raises:
            err.PAUSED_REGISTRY: If registry is paused
            err.NOT_XGOV: If the sender is not an active xGov
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert self.is_active_xgov(Txn.sender), err.NOT_XGOV

        self.unsubscribe_xgov_and_emit(Txn.sender)

    @arc4.abimethod()
    def unsubscribe_absentee(self, *, xgov_address: Account) -> None:
        """
        Unsubscribes an absentee xGov. This is a temporary method used only for the
        first absentees removal at the inception of the absenteeism penalty.

        Args:
            xgov_address: (Account): The address of the absentee xGov to unsubscribe

        Raises:
            err.PAUSED_REGISTRY: If registry is paused
            err.NOT_XGOV: If the address is not an active xGov
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert self.is_active_xgov(xgov_address), err.NOT_XGOV
        assert self.xgov_box[xgov_address].tolerated_absences == 0, err.UNAUTHORIZED

        self.unsubscribe_xgov_and_emit(xgov_address)

    @arc4.abimethod()
    def activate_xgov(self, xgov_address: Account) -> None:
        """
        Activate a revoked xGov status. This is a temporary method used only at the
        inception of the xGov status revocation.

        Args:
            xgov_address: The xGov address to activate.

        Raises:
            err.UNAUTHORIZED: If the caller is not the xGov Subscriber
            err.ALREADY_XGOV: If the address is already an active xGov
        """

        assert self.is_xgov_subscriber(), err.UNAUTHORIZED
        assert self.has_xgov_status(xgov_address) and not self.is_active_xgov(
            xgov_address
        ), err.ALREADY_XGOV

        self.xgov_box[xgov_address].unsubscribed_round = UInt64(0)

    @arc4.abimethod()
    def request_subscribe_xgov(
        self,
        *,
        xgov_address: Account,
        owner_address: Account,
        relation_type: UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> UInt64:
        """
        Requests to subscribe to the xGov.

        Args:
            xgov_address (Account): The address of the xGov
            owner_address (Account): The address of the xGov Address owner/controller (Voting Address)
            relation_type (UInt64): The type of relationship enum
            payment (gtxn.PaymentTransaction): The payment transaction covering the xGov fee

        Returns:
            Subscription request ID

        Raises:
            err.UNAUTHORIZED: If the sender is not the declared Application owner address
            err.PAUSED_REGISTRY: If registry is paused
            err.ALREADY_XGOV: If the requested address is already an active xGov
            err.INVALID_PAYMENT: If payment has wrong amount (not equal to xgov_fee global state key) or wrong receiver
        """

        assert Txn.sender == owner_address, err.UNAUTHORIZED
        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert not self.is_active_xgov(xgov_address), err.ALREADY_XGOV
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

        return rid

    @arc4.abimethod()
    def approve_subscribe_xgov(self, *, request_id: UInt64) -> None:
        """
        Approves a subscribe request to xGov.

        Args:
            request_id (UInt64): The ID of the request to approve

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Subscriber
            err.ALREADY_XGOV: If the requested address is already an xGov
        """

        assert self.is_xgov_subscriber(), err.UNAUTHORIZED

        xgov_address = self.request_box[request_id].xgov_addr
        voting_address = self.request_box[request_id].owner_addr
        assert not self.is_active_xgov(xgov_address), err.ALREADY_XGOV

        self.subscribe_xgov_and_emit(
            xgov_address=xgov_address, voting_address=voting_address
        )

        # delete the request
        del self.request_box[request_id]

    @arc4.abimethod()
    def reject_subscribe_xgov(self, *, request_id: UInt64) -> None:
        """
        Rejects a subscribe request to xGov.

        Args:
            request_id (UInt64): The ID of the request to reject

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
        """

        assert self.is_xgov_subscriber(), err.UNAUTHORIZED

        # delete the request
        del self.request_box[request_id]

    @arc4.abimethod()
    def request_unsubscribe_xgov(
        self,
        *,
        xgov_address: Account,
        owner_address: Account,
        relation_type: UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> UInt64:
        """
        Requests to unsubscribe from the xGov.

        Args:
            xgov_address (Account): The address of the xGov
            owner_address (Account): The address of the xGov Address owner/controller
            relation_type (UInt64): The type of relationship enum
            payment (gtxn.PaymentTransaction): The payment transaction covering the xGov (unsubscribe) fee

        Returns:
            Unsubscribe request ID

        Raises:
            err.UNAUTHORIZED: If the sender is not the declared Application owner address
            err.PAUSED_REGISTRY: If registry is paused
            err.NOT_XGOV: If the requested xGov address is not an active xGov
            err.INVALID_PAYMENT: If payment has wrong amount (not equal to xgov_fee global state key) or wrong receiver
        """

        assert Txn.sender == owner_address, err.UNAUTHORIZED
        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert self.is_active_xgov(xgov_address), err.NOT_XGOV
        assert self.valid_xgov_payment(payment), err.INVALID_PAYMENT

        # create unsubscribe request box
        ruid = self.request_id.value
        self.request_unsubscribe_box[ruid] = typ.XGovSubscribeRequestBoxValue(
            xgov_addr=xgov_address,
            owner_addr=owner_address,
            relation_type=relation_type,
        )

        # increment request id
        self.request_id.value += 1

        return ruid

    @arc4.abimethod()
    def approve_unsubscribe_xgov(self, *, request_id: UInt64) -> None:
        """
        Approves a request to unsubscribe from xGov.

        Args:
            request_id (UInt64): The ID of the unsubscribe request to approve

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Subscriber
            err.NOT_XGOV: If the requested xGov address is not an xGov
        """

        assert self.is_xgov_subscriber(), err.UNAUTHORIZED

        xgov_address = self.request_unsubscribe_box[request_id].xgov_addr
        assert self.is_active_xgov(xgov_address), err.NOT_XGOV

        self.unsubscribe_xgov_and_emit(xgov_address)

        # delete the request
        del self.request_unsubscribe_box[request_id]

    @arc4.abimethod()
    def reject_unsubscribe_xgov(self, *, request_id: UInt64) -> None:
        """
        Rejects a request to unsubscribe from xGov.

        Args:
            request_id (UInt64): The ID of the unsubscribe request to reject

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Subscriber
        """

        assert self.is_xgov_subscriber(), err.UNAUTHORIZED

        # delete the request
        del self.request_unsubscribe_box[request_id]

    @arc4.abimethod()
    def set_voting_account(
        self, *, xgov_address: Account, voting_address: Account
    ) -> None:
        """
        Sets the Voting Address for the xGov.

        Args:
            xgov_address (Account): The xGov address delegating voting power
            voting_address (Account): The voting account address to delegate voting power to

        Raises:
            err.PAUSED_REGISTRY: If registry is paused
            err.NOT_XGOV: If the xGov Address is not an active xGov
            err.UNAUTHORIZED: If the sender is not the xGov or the Voting Address
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert self.is_active_xgov(xgov_address), err.NOT_XGOV
        assert self.caller_is_xgov_or_voting_address(xgov_address), err.UNAUTHORIZED

        # Update the voting account in the xGov box
        self.xgov_box[xgov_address].voting_address = voting_address

    @arc4.abimethod()
    def subscribe_proposer(self, *, payment: gtxn.PaymentTransaction) -> None:
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
            active_proposal=False, kyc_status=False, kyc_expiring=UInt64(0)
        )

        arc4.emit(typ.ProposerSubscribed(proposer=Txn.sender))

    @arc4.abimethod()
    def set_proposer_kyc(
        self,
        *,
        proposer: Account,
        kyc_status: bool,
        kyc_expiring: UInt64,
    ) -> None:
        """
        Sets a proposer's KYC status.

        Args:
            proposer (Account): The address of the Proposer
            kyc_status (bool): The new status of the Proposer
            kyc_expiring (UInt64): The expiration date as a unix timestamp of the time the KYC expires

        Raises:
            err.UNAUTHORIZED: If the sender is not the KYC Provider
            err.PROPOSER_DOES_NOT_EXIST: If the referenced address is not a Proposer
        """

        # check if kyc provider
        assert Txn.sender == self.kyc_provider.value, err.UNAUTHORIZED
        assert proposer in self.proposer_box, err.PROPOSER_DOES_NOT_EXIST

        active_proposal = self.proposer_box[proposer].copy().active_proposal

        self.proposer_box[proposer] = self.make_proposer_box(
            active_proposal=active_proposal,
            kyc_status=kyc_status,
            kyc_expiring=kyc_expiring,
        )

        arc4.emit(
            typ.ProposerKYC(
                proposer=proposer,
                valid_kyc=bool(self.valid_kyc(proposer)),
            )
        )

    @arc4.abimethod()
    def declare_committee(
        self, *, committee_id: typ.Bytes32, size: UInt64, votes: UInt64
    ) -> None:
        """
        Sets the xGov Committee in charge.

        Args:
            committee_id (typ.Bytes32): The ID of the xGov Committee
            size (UInt64): The size of the xGov Committee
            votes (UInt64): The voting power of the xGov Committee

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Manager
            err.WRONG_CID_LENGTH: If the committee ID is not of the correct length
            err.WRONG_COMMITTEE_MEMBERS: If the committee is empty
            err.WRONG_COMMITTEE_VOTES: If the committee voting power is zero
            err.COMMITTEE_SIZE_TOO_LARGE: If the committee size exceeds the maximum allowed size
        """

        assert self.is_xgov_committee_manager(), err.UNAUTHORIZED
        assert committee_id.length == pcts.COMMITTEE_ID_LENGTH, err.WRONG_CID_LENGTH
        assert size > 0, err.WRONG_COMMITTEE_MEMBERS
        assert votes > 0, err.WRONG_COMMITTEE_VOTES
        assert size <= self.max_committee_size.value, err.COMMITTEE_SIZE_TOO_LARGE

        self.committee_id.value = committee_id.copy()
        self.committee_members.value = size
        self.committee_votes.value = votes
        self.committee_last_anchor.value = self.get_committee_anchor()

        arc4.emit(
            typ.NewCommittee(
                committee_id=committee_id,
                size=arc4.UInt32(size),
                votes=arc4.UInt32(votes),
            )
        )

    @arc4.abimethod
    def open_proposal(self, *, payment: gtxn.PaymentTransaction) -> UInt64:
        """
        Creates a new Proposal.

        Args:
            payment (gtxn.PaymentTransaction): payment for covering the proposal fee (includes child contract MBR)

        Raises:
            err.PAUSED_REGISTRY: If the xGov Registry is paused
            err.PAUSED_PROPOSALS: If new proposals are paused
            err.COMMITTEE_STALE: If the xGov Committee is stale (or not declared)
            err.UNAUTHORIZED: If the sender is not a Proposer
            err.ALREADY_ACTIVE_PROPOSAL: If the proposer already has an active proposal
            err.INVALID_KYC: If the Proposer does not have valid KYC
            err.INSUFFICIENT_FEE: If the fee for the current transaction doesn't cover the inner transaction fees
            err.WRONG_RECEIVER: If the payment receiver is not the xGov Registry address
            err.WRONG_PAYMENT_AMOUNT: If the payment amount is not equal to the open_proposal_fee global state key
            err.MISSING_PROPOSAL_APPROVAL_PROGRAM: If the Proposal Approval Program contract is not set
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY
        assert not self.paused_proposals.value, err.PAUSED_PROPOSALS

        committee_anchor = self.get_committee_anchor()
        committee_delay = Global.round - committee_anchor
        assert (
            committee_anchor == self.committee_last_anchor.value
            or committee_delay <= self.committee_grace_period.value
        ), err.COMMITTEE_STALE

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

        assert self.proposal_approval_program, err.MISSING_PROPOSAL_APPROVAL_PROGRAM

        # clear_state_program is a tuple of 2 Bytes elements where each is max 4096 bytes
        # we only use the first element here as we assume the clear state program is small enough
        compiled_clear_state_1, _compiled_clear_state_2 = compile_contract(
            proposal_contract.Proposal
        ).clear_state_program

        bytes_per_page = UInt64(BYTES_PER_APP_PAGE)
        total_size = (
            self.proposal_approval_program.length + compiled_clear_state_1.length
        )
        total_pages = total_size // bytes_per_page

        # The following assertion makes sure the loop-unrolling is consistent
        assert total_pages == UInt64(
            PROPOSAL_APPROVAL_PAGES
        ), err.INVALID_PROPOSAL_APPROVAL_PROGRAM_SIZE
        bytes_last_page = (
            self.proposal_approval_program.length - (total_pages - 1) * bytes_per_page
        )
        page_1 = self.proposal_approval_program.extract(
            0 * bytes_per_page, bytes_per_page
        )
        page_2 = self.proposal_approval_program.extract(
            1 * bytes_per_page, bytes_last_page
        )

        tx = arc4.abi_call(
            proposal_contract.Proposal.create,
            Txn.sender,
            approval_program=(page_1, page_2),
            clear_state_program=compiled_clear_state_1,
            global_num_uint=pcfg.GLOBAL_UINTS,
            global_num_bytes=pcfg.GLOBAL_BYTES,
            extra_program_pages=total_pages,
        )

        mbr_after = Global.current_application_address.balance

        # Transfer funds to the new Proposal App, excluding the MBR needed for the Proposal App
        itxn.Payment(
            receiver=tx.created_app.address,
            amount=self.open_proposal_fee.value - (mbr_after - mbr_before),
            fee=0,
        ).submit()

        self.increment_pending_proposals(Txn.sender)

        arc4.emit(
            typ.NewProposal(
                proposal_id=tx.created_app.id,
                proposer=Txn.sender,
            )
        )

        return tx.created_app.id

    @arc4.abimethod()
    def vote_proposal(
        self,
        *,
        proposal_id: Application,
        xgov_address: Account,
        approval_votes: UInt64,
        rejection_votes: UInt64,
    ) -> None:
        """
        Votes on a Proposal.

        Args:
            proposal_id (Application): The application ID of the Proposal app being voted on
            xgov_address: (Account): The address of the xGov being voted on behalf of
            approval_votes: (UInt64): The number of approvals votes allocated
            rejection_votes: (UInt64): The number of rejections votes allocated

        Raises:
            err.PAUSED_REGISTRY: If the xGov Registry is paused
            err.INVALID_PROPOSAL: If the Proposal ID is not a Proposal contract
            err.NOT_XGOV: If the xGov Address is not an active xGov
            err.MUST_BE_XGOV_OR_VOTING_ADDRESS: If the sender is not the xgov_address or the voting_address
            err.WRONG_PROPOSAL_STATUS: If the Proposal is not in the voting state
            err.VOTER_NOT_FOUND: If the xGov is not found in the Proposal's voting registry
            err.VOTER_ALREADY_VOTED: If the xGov has already voted on this Proposal
            err.VOTES_INVALID: If the votes are invalid
            err.VOTING_PERIOD_EXPIRED: If the voting period for the Proposal has expired
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # verify proposal_id id is genuine proposal
        assert self._is_proposal(proposal_id), err.INVALID_PROPOSAL
        assert self.is_active_xgov(xgov_address), err.NOT_XGOV
        assert self.caller_is_xgov_or_voting_address(
            xgov_address
        ), err.MUST_BE_XGOV_OR_VOTING_ADDRESS

        # Upon vote the absence tolerance is reset
        self.xgov_box[xgov_address].tolerated_absences = self.absence_tolerance.value

        # Call the Proposal App to register the vote
        error, _tx = arc4.abi_call(
            proposal_contract.Proposal.vote,
            xgov_address,
            approval_votes,
            rejection_votes,
            app_id=proposal_id,
        )

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    op.err(err.WRONG_PROPOSAL_STATUS)
                case err.VOTER_NOT_FOUND:
                    op.err(err.VOTER_NOT_FOUND)
                case err.VOTES_INVALID:
                    op.err(err.VOTES_INVALID)
                case err.VOTING_PERIOD_EXPIRED:
                    op.err(err.VOTING_PERIOD_EXPIRED)
                case _:
                    op.err("Unknown error")
        else:
            assert error == "", "Unknown error"

    @arc4.abimethod()
    def unassign_absentee_from_proposal(
        self, *, proposal_id: Application, absentees: Array[Account]
    ) -> None:
        """
        Unassign absentees from a scrutinized Proposal.

        Args:
            proposal_id (Application): The application ID of the scrutinized Proposal
            absentees (Array[Account]): List of absentees to be unassigned

        Raises:
            err.PAUSED_REGISTRY: If the xGov Registry is paused
            err.INVALID_PROPOSAL: If the Proposal ID is not a Proposal contract
            err.WRONG_PROPOSAL_STATUS: If the Proposal is not scrutinized
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # Verify proposal_id is a genuine proposal created by this registry
        assert self._is_proposal(proposal_id), err.INVALID_PROPOSAL

        # The `Proposal.unassign_absentees` call guarantees that:
        # - Any absentee in the array is really assigned to the Proposal;
        # - No absentee is duplicated in the array.
        error, _tx = arc4.abi_call(
            proposal_contract.Proposal.unassign_absentees,
            absentees,
            app_id=proposal_id,
        )

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    op.err(err.WRONG_PROPOSAL_STATUS)
                case err.VOTER_NOT_FOUND:
                    op.err(err.VOTER_NOT_FOUND)
                case _:
                    op.err("Unknown error")
        else:
            assert error == "", "Unknown error"

        # ⚠️ WARNING: The absentees array:
        # - MUST have only absentees really/still assigned to the Proposal
        # - MUST NOT have duplicates
        # which is guaranteed by the previous ABI call.
        for absentee in absentees:
            # The absentee might have already self-unsubscribed
            if (
                self.is_active_xgov(absentee)
                and self.xgov_box[absentee].tolerated_absences > 0
            ):
                self.xgov_box[absentee].tolerated_absences -= 1
                if self.xgov_box[absentee].tolerated_absences == 0:
                    self.unsubscribe_xgov_and_emit(absentee)

    @arc4.abimethod()
    def pay_grant_proposal(self, *, proposal_id: Application) -> None:
        """
        Disburses the funds for an approved Proposal.

        Args:
            proposal_id (Application): The application ID of the approved Proposal

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
        assert Txn.sender == self.xgov_payor.value, err.UNAUTHORIZED

        # Verify proposal_id is a genuine proposal created by this registry
        assert self._is_proposal(proposal_id), err.INVALID_PROPOSAL

        # Read proposal state directly from the Proposal App's global state
        proposer = self.get_proposal_proposer(proposal_id)
        requested_amount = self.get_proposal_requested_amount(proposal_id)

        assert proposer in self.proposer_box, err.WRONG_PROPOSER

        assert self.valid_kyc(proposer), err.INVALID_KYC

        # Verify sufficient funds are available
        assert (
            self.outstanding_funds.value >= requested_amount
        ), err.INSUFFICIENT_TREASURY_FUNDS

        self.disburse_funds(proposer, requested_amount)

        error, _tx = arc4.abi_call(proposal_contract.Proposal.fund, app_id=proposal_id)

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    op.err(err.WRONG_PROPOSAL_STATUS)
                case _:
                    op.err("Unknown error")
        else:
            assert error == "", "Unknown error"

    @arc4.abimethod()
    def finalize_proposal(self, *, proposal_id: Application) -> None:
        """
        Finalize a Proposal.

        Args:
            proposal_id (Application): The application ID of the Proposal app to finalize

        Raises:
            err.UNAUTHORIZED: If the sender is not the xGov Daemon
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not as expected
            err.VOTERS_ASSIGNED: If there are still assigned voters
        """

        proposal_status = self.get_proposal_status(proposal_id)
        if proposal_status == UInt64(penm.STATUS_EMPTY) or proposal_status == UInt64(
            penm.STATUS_DRAFT
        ):
            assert Txn.sender == self.xgov_daemon.value, err.UNAUTHORIZED

        # Verify proposal_id is a genuine proposal created by this registry
        assert self._is_proposal(proposal_id), err.INVALID_PROPOSAL

        error, _tx = arc4.abi_call(
            proposal_contract.Proposal.finalize, app_id=proposal_id
        )

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    op.err(err.WRONG_PROPOSAL_STATUS)
                case err.VOTERS_ASSIGNED:
                    op.err(err.VOTERS_ASSIGNED)
                case _:
                    op.err("Unknown error")
        else:
            assert error == "", "Unknown error"

        self.decrement_pending_proposals(proposal_id)

    @arc4.abimethod()
    def drop_proposal(self, *, proposal_id: Application) -> None:
        """
        Drops a Proposal.

        Args:
            proposal_id (Application): The application ID of the Proposal app to drop

        Raises:
            err.PAUSED_REGISTRY: If the registry is paused
            err.INVALID_PROPOSAL: If the proposal_id is not a proposal contract
            err.UNAUTHORIZED: If the sender is not the proposer
            err.WRONG_PROPOSAL_STATUS: If the proposal status is not as expected
        """

        assert not self.paused_registry.value, err.PAUSED_REGISTRY

        # Verify proposal_id is a genuine proposal created by this registry
        assert self._is_proposal(proposal_id), err.INVALID_PROPOSAL

        proposer = self.get_proposal_proposer(proposal_id)
        assert Txn.sender == proposer, err.UNAUTHORIZED

        error, _tx = arc4.abi_call(proposal_contract.Proposal.drop, app_id=proposal_id)

        if error.startswith(err.ARC_65_PREFIX):
            error_without_prefix = String.from_bytes(error.bytes[4:])
            match error_without_prefix:
                case err.WRONG_PROPOSAL_STATUS:
                    op.err(err.WRONG_PROPOSAL_STATUS)
                case _:
                    op.err("Unknown error")
        else:
            assert error == "", "Unknown error"

        self.decrement_pending_proposals(proposal_id)

    @arc4.abimethod()
    def deposit_funds(self, *, payment: gtxn.PaymentTransaction) -> None:
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
    def withdraw_funds(self, *, amount: UInt64) -> None:
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
        assert amount <= self.outstanding_funds.value, err.INSUFFICIENT_FUNDS
        assert Txn.fee >= (Global.min_txn_fee * 2), err.INSUFFICIENT_FEE
        self.outstanding_funds.value -= amount

        itxn.Payment(
            receiver=self.xgov_manager.value,
            amount=amount,
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
            receiver=self.xgov_manager.value,
            amount=amount,
            fee=0,
        ).submit()

    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.TypedGlobalState:
        """
        Returns the xGov Registry state.
        """

        return typ.TypedGlobalState(
            paused_registry=self.paused_registry.value,
            paused_proposals=self.paused_proposals.value,
            xgov_manager=self.xgov_manager.value,
            xgov_payor=self.xgov_payor.value,
            xgov_council=self.xgov_council.value,
            xgov_subscriber=self.xgov_subscriber.value,
            kyc_provider=self.kyc_provider.value,
            committee_manager=self.committee_manager.value,
            xgov_daemon=self.xgov_daemon.value,
            xgov_fee=self.xgov_fee.value,
            proposer_fee=self.proposer_fee.value,
            open_proposal_fee=self.open_proposal_fee.value,
            daemon_ops_funding_bps=self.daemon_ops_funding_bps.value,
            proposal_commitment_bps=self.proposal_commitment_bps.value,
            min_requested_amount=self.min_requested_amount.value,
            max_requested_amount=FixedArray(
                (
                    self.max_requested_amount_small.value,
                    self.max_requested_amount_medium.value,
                    self.max_requested_amount_large.value,
                )
            ),
            discussion_duration=FixedArray(
                (
                    self.discussion_duration_small.value,
                    self.discussion_duration_medium.value,
                    self.discussion_duration_large.value,
                    self.discussion_duration_xlarge.value,
                )
            ),
            voting_duration=FixedArray(
                (
                    self.voting_duration_small.value,
                    self.voting_duration_medium.value,
                    self.voting_duration_large.value,
                    self.voting_duration_xlarge.value,
                )
            ),
            quorum=FixedArray(
                (
                    self.quorum_small.value,
                    self.quorum_medium.value,  # No longer used
                    self.quorum_large.value,
                )
            ),
            weighted_quorum=FixedArray(
                (
                    self.weighted_quorum_small.value,
                    self.weighted_quorum_medium.value,  # No longer used
                    self.weighted_quorum_large.value,
                )
            ),
            outstanding_funds=self.outstanding_funds.value,
            pending_proposals=self.pending_proposals.value,
            committee_id=self.committee_id.value.copy(),
            committee_members=self.committee_members.value,
            committee_votes=self.committee_votes.value,
            absence_tolerance=self.absence_tolerance.value,
            governance_period=self.governance_period.value,
            committee_grace_period=self.committee_grace_period.value,
            committee_last_anchor=self.committee_last_anchor.value,
        )

    @arc4.abimethod(readonly=True)
    def get_xgov_box(self, *, xgov_address: Account) -> tuple[typ.XGovBoxValue, bool]:
        """
        Returns the xGov box for the given address.

        Args:
            xgov_address (Account): The address of the xGov

        Returns:
            typ.XGovBoxValue: The xGov box value
            bool: `True` if xGov box exists, else `False`
        """
        exists = self.has_xgov_status(xgov_address)
        if exists:
            val = self.xgov_box[xgov_address].copy()
        else:
            val = typ.XGovBoxValue(
                voting_address=Account(),
                tolerated_absences=UInt64(0),
                unsubscribed_round=UInt64(0),
                subscription_round=UInt64(0),
            )

        return val.copy(), exists

    @arc4.abimethod(readonly=True)
    def get_proposer_box(
        self,
        *,
        proposer_address: Account,
    ) -> tuple[typ.ProposerBoxValue, bool]:
        """
        Returns the Proposer box for the given address.

        Args:
            proposer_address (Account): The address of the Proposer

        Returns:
            typ.ProposerBoxValue: The Proposer box value
            bool: `True` if Proposer box exists, else `False`
        """
        exists = proposer_address in self.proposer_box
        if exists:
            val = self.proposer_box[proposer_address].copy()
        else:
            val = typ.ProposerBoxValue(
                active_proposal=False,
                kyc_status=False,
                kyc_expiring=UInt64(0),
            )

        return val.copy(), exists

    @arc4.abimethod(readonly=True)
    def get_request_box(
        self,
        *,
        request_id: UInt64,
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        """
        Returns the xGov subscribe request box for the given request ID.

        Args:
            request_id (UInt64): The ID of the subscribe request

        Returns:
            typ.XGovSubscribeRequestBoxValue: The subscribe request box value
            bool: `True` if xGov subscribe request box exists, else `False`
        """
        exists = request_id in self.request_box
        if exists:
            val = self.request_box[request_id].copy()
        else:
            val = typ.XGovSubscribeRequestBoxValue(
                xgov_addr=Account(),
                owner_addr=Account(),
                relation_type=UInt64(0),
            )

        return val.copy(), exists

    @arc4.abimethod(readonly=True)
    def get_request_unsubscribe_box(
        self, *, request_id: UInt64
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        """
        Returns the xGov unsubscribe request box for the given unsubscribe request ID.

        Args:
            request_id (UInt64): The ID of the unsubscribe request

        Returns:
            typ.XGovSubscribeRequestBoxValue: The unsubscribe request box value
            bool: `True` if xGov unsubscribe request box exists, else `False`
        """
        exists = request_id in self.request_unsubscribe_box
        if exists:
            val = self.request_unsubscribe_box[request_id].copy()
        else:
            val = typ.XGovSubscribeRequestBoxValue(
                xgov_addr=Account(),
                owner_addr=Account(),
                relation_type=UInt64(0),
            )

        return val.copy(), exists

    @arc4.abimethod()
    def is_proposal(self, *, proposal_id: Application) -> None:
        assert self._is_proposal(proposal_id), err.INVALID_PROPOSAL

    @arc4.abimethod()
    def op_up(self) -> None:
        return
