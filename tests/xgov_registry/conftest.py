from __future__ import annotations

import threading
from collections.abc import Iterable, Sequence

import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AppClientCompilationParams,
    CommonAppCallParams,
    PaymentParams,
    SigningAccount,
)
from algokit_utils.config import config
from algosdk.transaction import Transaction

from smart_contracts.artifacts.proposal.proposal_client import (
    OpenArgs,
    ProposalClient,
    ProposalFactory,
    ReviewArgs,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ApproveSubscribeXgovArgs,
    ConfigXgovRegistryArgs,
    DeclareCommitteeArgs,
    DepositFundsArgs,
    OpenProposalArgs,
    PayGrantProposalArgs,
    RequestSubscribeXgovArgs,
    RequestUnsubscribeXgovArgs,
    SetCommitteeManagerArgs,
    SetKycProviderArgs,
    SetPayorArgs,
    SetProposerKycArgs,
    SetXgovCouncilArgs,
    SetXgovDaemonArgs,
    SetXgovSubscriberArgs,
    SubscribeProposerArgs,
    SubscribeXgovArgs,
    VoteProposalArgs,
    XGovRegistryClient,
    XGovRegistryConfig,
    XGovRegistryFactory,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
    XGovSubscriberAppMockFactory,
)
from smart_contracts.proposal import enums as enm
from smart_contracts.xgov_registry import config as regcfg
from smart_contracts.xgov_registry.helpers import (
    load_proposal_contract_data_size_per_transaction,
)
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    INITIAL_FUNDS,
    CommitteeMember,
)
from tests.proposal.common import (
    DEFAULT_FOCUS,
    PROPOSAL_TITLE,
    REQUESTED_AMOUNT,
    assign_voters,
    get_locked_amount,
    scrutinize_proposal,
    submit_proposal,
    unassign_absentees,
    upload_metadata,
)
from tests.xgov_registry.common import (
    LOW_ABSENCE_TOLERANCE,
    SHORT_COMMITTEE_GRACE_PERIOD,
    SHORT_GOVERNANCE_PERIOD,
    TREASURY_AMOUNT,
    UNLIMITED_KYC_EXPIRATION,
    get_open_proposal_fee,
    get_proposer_fee,
    get_xgov_fee,
)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

_METADATA = b"METADATA"

_DATA_SIZE_PER_TXN = load_proposal_contract_data_size_per_transaction()

# Global cache for compiled proposal approval program chunks (immutable bytes).
# This is safe to share across tests because it does NOT include any on-chain state.
_PROPOSAL_PROGRAM_CACHE_LOCK = threading.Lock()
_PROPOSAL_PROGRAM_LEN_AND_CHUNKS: tuple[int, tuple[tuple[int, bytes], ...]] | None = (
    None
)


def _configure_algokit() -> None:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )


def _ensure_funded(
    algorand_client: AlgorandClient,
    account_to_fund: SigningAccount | str,
    *,
    min_spending_balance: AlgoAmount,
    min_funding_increment: AlgoAmount | None = None,
) -> None:
    kwargs = {
        "account_to_fund": account_to_fund,
        "min_spending_balance": min_spending_balance,
    }
    if min_funding_increment is not None:
        kwargs["min_funding_increment"] = min_funding_increment
    algorand_client.account.ensure_funded_from_environment(**kwargs)


def _payment(
    algorand_client: AlgorandClient,
    *,
    sender: str,
    receiver: str,
    amount: AlgoAmount,
) -> Transaction:
    return algorand_client.create_transaction.payment(
        PaymentParams(sender=sender, receiver=receiver, amount=amount)
    )


def _compile_proposal_program_chunks(
    algorand_client: AlgorandClient,
) -> tuple[int, tuple[tuple[int, bytes], ...]]:
    """Compile once per process; reuse immutable bytes across tests."""
    global _PROPOSAL_PROGRAM_LEN_AND_CHUNKS
    if _PROPOSAL_PROGRAM_LEN_AND_CHUNKS is not None:
        return _PROPOSAL_PROGRAM_LEN_AND_CHUNKS

    with _PROPOSAL_PROGRAM_CACHE_LOCK:
        if _PROPOSAL_PROGRAM_LEN_AND_CHUNKS is not None:
            return _PROPOSAL_PROGRAM_LEN_AND_CHUNKS

        proposal_factory = algorand_client.client.get_typed_app_factory(
            typed_factory=ProposalFactory
        )
        compiled = proposal_factory.app_factory.compile()
        approval = compiled.approval_program
        program_len = len(approval)

        chunks = tuple(
            (offset, approval[offset : offset + _DATA_SIZE_PER_TXN])
            for offset in range(0, program_len, _DATA_SIZE_PER_TXN)
        )
        _PROPOSAL_PROGRAM_LEN_AND_CHUNKS = (program_len, chunks)
        return _PROPOSAL_PROGRAM_LEN_AND_CHUNKS


def _requested_amount_exceeding_treasury(
    xgov_registry_client: XGovRegistryClient,
) -> AlgoAmount:
    """Pick a requested amount that is both >= min_requested_amount and > treasury."""
    reg_gs = xgov_registry_client.state.global_state
    outstanding_funds = reg_gs.outstanding_funds
    min_requested_amount = reg_gs.min_requested_amount

    if outstanding_funds >= min_requested_amount:
        return AlgoAmount(micro_algo=outstanding_funds + min_requested_amount)
    return AlgoAmount(micro_algo=min_requested_amount * 2)


def _open_and_upload_draft(
    *,
    algorand_client: AlgorandClient,
    proposal_client: ProposalClient,
    proposer: SigningAccount,
    locked_amount: AlgoAmount,
    requested_amount_micro_algo: int,
    params: CommonAppCallParams | None = None,
) -> None:
    proposal_client.send.open(
        args=OpenArgs(
            payment=_payment(
                algorand_client,
                sender=proposer.address,
                receiver=proposal_client.app_address,
                amount=locked_amount,
            ),
            title=PROPOSAL_TITLE,
            funding_type=enm.FUNDING_RETROACTIVE,
            requested_amount=requested_amount_micro_algo,
            focus=DEFAULT_FOCUS,
        ),
        params=params,
    )

    composer = proposal_client.new_group()
    upload_metadata(composer, proposer, _METADATA)
    composer.send()


def _submit_and_assign(
    *,
    proposal_client: ProposalClient,
    xgov_registry_client: XGovRegistryClient,
    proposer: SigningAccount,
    committee: Sequence[CommitteeMember],
    xgov_daemon: SigningAccount,
) -> None:
    submit_proposal(
        proposal_client=proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=proposer,
    )
    composer = proposal_client.new_group()
    assign_voters(composer, committee, xgov_daemon)
    composer.send()


def _vote_all_approve(
    *,
    xgov_registry_client: XGovRegistryClient,
    committee: Iterable[CommitteeMember],
    proposal_id: int,
    static_fee: AlgoAmount,
) -> None:
    for cm in committee:
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=proposal_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(
                sender=cm.account.address,
                static_fee=static_fee,
            ),
        )


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture(scope="function")
def xgov_registry_config_dict() -> dict:
    # Keep this as a fresh dict each time to avoid cross-test mutation.
    return {
        "xgov_fee": regcfg.XGOV_FEE,
        "proposer_fee": regcfg.PROPOSER_FEE,
        "open_proposal_fee": regcfg.OPEN_PROPOSAL_FEE,
        "daemon_ops_funding_bps": regcfg.DAEMON_OPS_FUNDING_BPS,
        "proposal_commitment_bps": regcfg.PROPOSAL_COMMITMENT_BPS,
        "min_requested_amount": regcfg.MIN_REQUESTED_AMOUNT,
        "max_requested_amount": (
            regcfg.MAX_REQUESTED_AMOUNT_SMALL,
            regcfg.MAX_REQUESTED_AMOUNT_MEDIUM,
            regcfg.MAX_REQUESTED_AMOUNT_LARGE,
        ),
        "discussion_duration": (
            regcfg.DISCUSSION_DURATION_SMALL,
            regcfg.DISCUSSION_DURATION_MEDIUM,
            regcfg.DISCUSSION_DURATION_LARGE,
            regcfg.DISCUSSION_DURATION_XLARGE,
        ),
        "voting_duration": (
            regcfg.VOTING_DURATION_SMALL,
            regcfg.VOTING_DURATION_MEDIUM,
            regcfg.VOTING_DURATION_LARGE,
            regcfg.VOTING_DURATION_XLARGE,
        ),
        "quorum": (
            regcfg.QUORUM_SMALL,
            regcfg.QUORUM_MEDIUM,
            regcfg.QUORUM_LARGE,
        ),
        "weighted_quorum": (
            regcfg.WEIGHTED_QUORUM_SMALL,
            regcfg.WEIGHTED_QUORUM_MEDIUM,
            regcfg.WEIGHTED_QUORUM_LARGE,
        ),
        "absence_tolerance": LOW_ABSENCE_TOLERANCE,
        "governance_period": SHORT_GOVERNANCE_PERIOD,
        "committee_grace_period": SHORT_COMMITTEE_GRACE_PERIOD,
    }


@pytest.fixture(scope="function")
def xgov_registry_config(xgov_registry_config_dict: dict) -> XGovRegistryConfig:
    return XGovRegistryConfig(**xgov_registry_config_dict)


@pytest.fixture(scope="function")
def xgov_registry_client_committee_not_declared(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    committee_manager: SigningAccount,
    xgov_subscriber: SigningAccount,
    xgov_payor: SigningAccount,
    xgov_daemon: SigningAccount,
    xgov_council: SigningAccount,
    kyc_provider: SigningAccount,
    xgov_registry_config: XGovRegistryConfig,
) -> XGovRegistryClient:
    _configure_algokit()
    _ensure_funded(
        algorand_client,
        deployer,
        min_spending_balance=INITIAL_FUNDS,
    )

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=XGovRegistryFactory,
        default_sender=deployer.address,
        compilation_params=AppClientCompilationParams(
            deploy_time_params={"entropy": b""}
        ),
    )
    client, _ = factory.send.create.create()
    _ensure_funded(
        algorand_client,
        client.app_address,
        min_spending_balance=INITIAL_FUNDS,
    )

    # RBAC + config
    config_composer = client.new_group()
    config_composer.set_committee_manager(
        args=SetCommitteeManagerArgs(manager=committee_manager.address),
    )
    config_composer.set_xgov_subscriber(
        args=SetXgovSubscriberArgs(subscriber=xgov_subscriber.address),
    )
    config_composer.set_payor(
        args=SetPayorArgs(payor=xgov_payor.address),
    )
    config_composer.set_xgov_daemon(
        args=SetXgovDaemonArgs(xgov_daemon=xgov_daemon.address),
    )
    config_composer.set_xgov_council(
        args=SetXgovCouncilArgs(council=xgov_council.address),
    )
    config_composer.set_kyc_provider(
        args=SetKycProviderArgs(provider=kyc_provider.address),
    )
    config_composer.config_xgov_registry(
        args=ConfigXgovRegistryArgs(config=xgov_registry_config),
    )
    config_composer.send()

    # Load proposal contract once (program bytes are cached across tests)
    program_len, chunks = _compile_proposal_program_chunks(algorand_client)
    proposal_program_composer = client.new_group()
    proposal_program_composer.init_proposal_contract(args=(program_len,))
    for offset, chunk in chunks:
        proposal_program_composer.load_proposal_contract(args=(offset, chunk))
    proposal_program_composer.send()

    return client


@pytest.fixture(scope="function")
def xgov_registry_client(
    committee_manager: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> XGovRegistryClient:
    xgov_registry_client_committee_not_declared.send.declare_committee(
        args=DeclareCommitteeArgs(
            committee_id=DEFAULT_COMMITTEE_ID,
            size=DEFAULT_COMMITTEE_MEMBERS,
            votes=DEFAULT_COMMITTEE_VOTES,
        ),
        params=CommonAppCallParams(sender=committee_manager.address),
    )
    return xgov_registry_client_committee_not_declared


@pytest.fixture(scope="function")
def subscribed_committee(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
) -> list[CommitteeMember]:
    xgov_fee = get_xgov_fee(xgov_registry_client)
    min_balance = AlgoAmount(algo=xgov_fee.algo * 2)
    for cm in committee:
        _ensure_funded(
            algorand_client,
            cm.account,
            min_spending_balance=min_balance,
            min_funding_increment=xgov_fee,
        )
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                payment=_payment(
                    algorand_client,
                    sender=cm.account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=xgov_fee,
                ),
                voting_address=cm.account.address,
            ),
            params=CommonAppCallParams(sender=cm.account.address),
        )
    return committee


@pytest.fixture(scope="function")
def funded_xgov_registry_client(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> XGovRegistryClient:
    _ensure_funded(
        algorand_client,
        deployer,
        min_spending_balance=TREASURY_AMOUNT,
        min_funding_increment=TREASURY_AMOUNT,
    )
    xgov_registry_client.send.deposit_funds(
        args=DepositFundsArgs(
            payment=_payment(
                algorand_client,
                sender=deployer.address,
                receiver=xgov_registry_client.app_address,
                amount=TREASURY_AMOUNT,
            )
        )
    )
    return xgov_registry_client


@pytest.fixture(scope="function")
def xgov(
    algorand_client: AlgorandClient,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> SigningAccount:
    account = algorand_client.account.random()
    _ensure_funded(algorand_client, account, min_spending_balance=INITIAL_FUNDS)

    xgov_registry_client_committee_not_declared.send.subscribe_xgov(
        args=SubscribeXgovArgs(
            voting_address=account.address,
            payment=_payment(
                algorand_client,
                sender=account.address,
                receiver=xgov_registry_client_committee_not_declared.app_address,
                amount=get_xgov_fee(xgov_registry_client_committee_not_declared),
            ),
        ),
        params=CommonAppCallParams(sender=account.address),
    )
    return account


@pytest.fixture(scope="function")
def proposer_no_kyc(
    algorand_client: AlgorandClient,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> SigningAccount:
    account = algorand_client.account.random()
    _ensure_funded(algorand_client, account, min_spending_balance=INITIAL_FUNDS)

    xgov_registry_client_committee_not_declared.send.subscribe_proposer(
        args=SubscribeProposerArgs(
            payment=_payment(
                algorand_client,
                sender=account.address,
                receiver=xgov_registry_client_committee_not_declared.app_address,
                amount=get_proposer_fee(xgov_registry_client_committee_not_declared),
            )
        ),
        params=CommonAppCallParams(sender=account.address),
    )
    return account


@pytest.fixture(scope="function")
def proposer(
    kyc_provider: SigningAccount,
    proposer_no_kyc: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> SigningAccount:
    xgov_registry_client_committee_not_declared.send.set_proposer_kyc(
        args=SetProposerKycArgs(
            proposer=proposer_no_kyc.address,
            kyc_status=True,
            kyc_expiring=UNLIMITED_KYC_EXPIRATION,
        ),
        params=CommonAppCallParams(sender=kyc_provider.address),
    )
    return proposer_no_kyc


@pytest.fixture(scope="function")
def alternative_proposer(
    algorand_client: AlgorandClient,
    kyc_provider: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> SigningAccount:
    account = algorand_client.account.random()
    _ensure_funded(algorand_client, account, min_spending_balance=INITIAL_FUNDS)

    xgov_registry_client_committee_not_declared.send.subscribe_proposer(
        args=SubscribeProposerArgs(
            payment=_payment(
                algorand_client,
                sender=account.address,
                receiver=xgov_registry_client_committee_not_declared.app_address,
                amount=get_proposer_fee(xgov_registry_client_committee_not_declared),
            )
        ),
        params=CommonAppCallParams(sender=account.address),
    )

    xgov_registry_client_committee_not_declared.send.set_proposer_kyc(
        args=SetProposerKycArgs(
            proposer=account.address,
            kyc_status=True,
            kyc_expiring=UNLIMITED_KYC_EXPIRATION,
        ),
        params=CommonAppCallParams(sender=kyc_provider.address),
    )
    return account


@pytest.fixture(scope="function")
def proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> ProposalClient:
    open_proposal_fee = get_open_proposal_fee(xgov_registry_client)
    _ensure_funded(
        algorand_client,
        proposer,
        min_spending_balance=AlgoAmount(algo=2 * open_proposal_fee.algo),
        min_funding_increment=open_proposal_fee,
    )

    proposal_app_id = xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=_payment(
                algorand_client,
                sender=proposer.address,
                receiver=xgov_registry_client.app_address,
                amount=open_proposal_fee,
            )
        ),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3),
    ).abi_return

    return ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id,  # type: ignore
        default_sender=proposer.address,
    )


@pytest.fixture(scope="function")
def draft_proposal_client(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> ProposalClient:
    locked_amount = get_locked_amount(REQUESTED_AMOUNT)
    _ensure_funded(
        algorand_client,
        proposer,
        min_spending_balance=locked_amount,
        min_funding_increment=locked_amount,
    )

    _open_and_upload_draft(
        algorand_client=algorand_client,
        proposal_client=proposal_client,
        proposer=proposer,
        locked_amount=locked_amount,
        requested_amount_micro_algo=REQUESTED_AMOUNT.amount_in_micro_algo,
    )
    return proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client(
    xgov_daemon: SigningAccount,
    subscribed_committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
) -> ProposalClient:
    _submit_and_assign(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=proposer,
        committee=subscribed_committee,
        xgov_daemon=xgov_daemon,
    )
    return draft_proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client_requested_too_much(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    xgov_daemon: SigningAccount,
    proposer: SigningAccount,
    subscribed_committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
) -> ProposalClient:
    requested_amount = _requested_amount_exceeding_treasury(xgov_registry_client)
    locked_amount = get_locked_amount(requested_amount)

    _ensure_funded(
        algorand_client,
        proposer,
        min_spending_balance=AlgoAmount(algo=locked_amount.algo * 2),
        min_funding_increment=locked_amount,
    )

    _open_and_upload_draft(
        algorand_client=algorand_client,
        proposal_client=proposal_client,
        proposer=proposer,
        locked_amount=locked_amount,
        requested_amount_micro_algo=requested_amount.micro_algo,
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3),
    )

    _submit_and_assign(
        proposal_client=proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=proposer,
        committee=subscribed_committee,
        xgov_daemon=xgov_daemon,
    )
    return proposal_client


@pytest.fixture(scope="function")
def rejected_proposal_client(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    voting_proposal_client: ProposalClient,
) -> ProposalClient:
    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)
    return voting_proposal_client


@pytest.fixture(scope="function")
def rejected_unassigned_absentees_proposal_client(
    xgov_registry_client: XGovRegistryClient,
    rejected_proposal_client: ProposalClient,
) -> ProposalClient:
    absentees = rejected_proposal_client.state.box.voters.get_map()
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        rejected_proposal_client.app_id,
        absentees,
        op_up_count=3,
    )
    composer.send()
    return rejected_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> ProposalClient:
    _vote_all_approve(
        xgov_registry_client=xgov_registry_client,
        committee=committee,
        proposal_id=voting_proposal_client.app_id,
        static_fee=min_fee_times_2,
    )
    scrutinize_proposal(no_role_account, voting_proposal_client, min_fee_times_2)
    return voting_proposal_client


@pytest.fixture(scope="function")
def reviewed_proposal_client(
    xgov_council: SigningAccount,
    min_fee_times_2: AlgoAmount,
    approved_proposal_client: ProposalClient,
) -> ProposalClient:
    approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(
            sender=xgov_council.address, static_fee=min_fee_times_2
        ),
    )
    return approved_proposal_client


@pytest.fixture(scope="function")
def blocked_proposal_client(
    min_fee_times_2: AlgoAmount,
    xgov_council: SigningAccount,
    approved_proposal_client: ProposalClient,
) -> ProposalClient:
    approved_proposal_client.send.review(
        args=ReviewArgs(block=True),
        params=CommonAppCallParams(
            sender=xgov_council.address, static_fee=min_fee_times_2
        ),
    )
    return approved_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client_requested_too_much(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client_requested_too_much: ProposalClient,
) -> ProposalClient:
    _vote_all_approve(
        xgov_registry_client=xgov_registry_client,
        committee=committee,
        proposal_id=voting_proposal_client_requested_too_much.app_id,
        static_fee=min_fee_times_2,
    )
    scrutinize_proposal(
        no_role_account,
        voting_proposal_client_requested_too_much,
        min_fee_times_2,
    )
    return voting_proposal_client_requested_too_much


@pytest.fixture(scope="function")
def funded_proposal_client(
    min_fee_times_4: AlgoAmount,
    xgov_payor: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
    reviewed_proposal_client: ProposalClient,
) -> ProposalClient:
    funded_xgov_registry_client.send.pay_grant_proposal(
        args=PayGrantProposalArgs(proposal_id=reviewed_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_payor.address, static_fee=min_fee_times_4
        ),
    )
    return reviewed_proposal_client


@pytest.fixture(scope="function")
def xgov_subscriber_app(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
) -> XGovSubscriberAppMockClient:
    _configure_algokit()

    factory = algorand_client.client.get_typed_app_factory(
        XGovSubscriberAppMockFactory,
        default_sender=deployer.address,
        default_signer=deployer.signer,
    )
    client, _ = factory.send.create.bare()  # type: ignore
    _ensure_funded(
        algorand_client, client.app_address, min_spending_balance=INITIAL_FUNDS
    )
    return client


@pytest.fixture(scope="function")
def app_xgov_subscribe_requested(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
) -> XGovSubscriberAppMockClient:
    xgov_registry_client.send.request_subscribe_xgov(
        args=RequestSubscribeXgovArgs(
            xgov_address=xgov_subscriber_app.app_address,
            owner_address=no_role_account.address,
            relation_type=0,
            payment=_payment(
                algorand_client,
                sender=no_role_account.address,
                receiver=xgov_registry_client.app_address,
                amount=get_xgov_fee(xgov_registry_client),
            ),
        ),
        params=CommonAppCallParams(sender=no_role_account.address),
    )
    return xgov_subscriber_app


@pytest.fixture(scope="function")
def app_xgov_managed_subscription(
    xgov_registry_client: XGovRegistryClient,
    app_xgov_subscribe_requested: XGovSubscriberAppMockClient,
    xgov_subscriber: SigningAccount,
) -> XGovSubscriberAppMockClient:
    xgov_registry_client.send.approve_subscribe_xgov(
        args=ApproveSubscribeXgovArgs(
            request_id=xgov_registry_client.state.global_state.request_id - 1
        ),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )
    return app_xgov_subscribe_requested


@pytest.fixture(scope="function")
def app_xgov_unsubscribe_requested(
    algorand_client: AlgorandClient,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
    no_role_account: SigningAccount,
) -> XGovSubscriberAppMockClient:
    xgov_registry_client.send.request_unsubscribe_xgov(
        args=RequestUnsubscribeXgovArgs(
            xgov_address=app_xgov_managed_subscription.app_address,
            owner_address=no_role_account.address,
            relation_type=0,
            payment=_payment(
                algorand_client,
                sender=no_role_account.address,
                receiver=xgov_registry_client.app_address,
                amount=get_xgov_fee(xgov_registry_client),
            ),
        ),
        params=CommonAppCallParams(sender=no_role_account.address),
    )
    return app_xgov_managed_subscription


@pytest.fixture(scope="function")
def absentee_committee(
    subscribed_committee: list[CommitteeMember],
    rejected_unassigned_absentees_proposal_client: ProposalClient,
) -> list[CommitteeMember]:
    # Intentionally returns the subscribed committee, but depends on the rejection flow to
    # preserve the fixture hierarchy used by the tests.
    return subscribed_committee


@pytest.fixture(scope="function")
def alternative_voting_proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    xgov_daemon: SigningAccount,
    alternative_proposer: SigningAccount,
    absentee_committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
) -> ProposalClient:
    requested_amount = _requested_amount_exceeding_treasury(xgov_registry_client)
    locked_amount = get_locked_amount(requested_amount)

    _ensure_funded(
        algorand_client,
        alternative_proposer,
        min_spending_balance=AlgoAmount(algo=locked_amount.algo * 2),
        min_funding_increment=locked_amount,
    )

    open_proposal_fee = get_open_proposal_fee(xgov_registry_client)
    proposal_app_id = xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=_payment(
                algorand_client,
                sender=alternative_proposer.address,
                receiver=xgov_registry_client.app_address,
                amount=open_proposal_fee,
            )
        ),
        params=CommonAppCallParams(
            sender=alternative_proposer.address,
            static_fee=min_fee_times_3,
        ),
    ).abi_return

    proposal_client = ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id,  # type: ignore
        default_sender=alternative_proposer.address,
    )

    _open_and_upload_draft(
        algorand_client=algorand_client,
        proposal_client=proposal_client,
        proposer=alternative_proposer,
        locked_amount=locked_amount,
        requested_amount_micro_algo=requested_amount.micro_algo,
        params=CommonAppCallParams(
            sender=alternative_proposer.address,
            static_fee=min_fee_times_3,
        ),
    )

    _submit_and_assign(
        proposal_client=proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=alternative_proposer,
        committee=absentee_committee,
        xgov_daemon=xgov_daemon,
    )
    return proposal_client
