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

from smart_contracts.artifacts.proposal.proposal_client import (
    AssignVotersArgs,
    OpenArgs,
    ProposalClient,
    ProposalFactory,
    ReviewArgs,
    UnassignVotersArgs,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ConfigXgovRegistryArgs,
    DeclareCommitteeArgs,
    DepositFundsArgs,
    OpenProposalArgs,
    PayGrantProposalArgs,
    RequestSubscribeXgovArgs,
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
    get_locked_amount,
    submit_proposal,
    upload_metadata,
)
from tests.utils import time_warp
from tests.xgov_registry.common import (
    TREASURY_AMOUNT,
    UNLIMITED_KYC_EXPIRATION,
    get_open_proposal_fee,
    get_proposer_fee,
    get_xgov_fee,
)


@pytest.fixture(scope="session")  # type: ignore
def xgov_registry_config_dict() -> dict:  # type: ignore
    return {  # type: ignore
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
    }


@pytest.fixture(scope="session")  # type: ignore
def xgov_registry_config(xgov_registry_config_dict: dict) -> XGovRegistryConfig:  # type: ignore
    return XGovRegistryConfig(**xgov_registry_config_dict)  # type: ignore


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
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer,
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
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_FUNDS,
    )

    # Set xGov Registry Role-Based Access Control
    client.send.set_committee_manager(
        args=SetCommitteeManagerArgs(manager=committee_manager.address),
    )

    client.send.set_xgov_subscriber(
        args=SetXgovSubscriberArgs(subscriber=xgov_subscriber.address),
    )

    client.send.set_payor(
        args=SetPayorArgs(payor=xgov_payor.address),
    )

    client.send.set_xgov_daemon(
        args=SetXgovDaemonArgs(xgov_daemon=xgov_daemon.address),
    )

    client.send.set_xgov_council(
        args=SetXgovCouncilArgs(council=xgov_council.address),
    )

    client.send.set_kyc_provider(
        args=SetKycProviderArgs(provider=kyc_provider.address),
    )

    # Configure xGov Registry
    client.send.config_xgov_registry(
        args=ConfigXgovRegistryArgs(config=xgov_registry_config),
    )

    proposal_factory = algorand_client.client.get_typed_app_factory(
        typed_factory=ProposalFactory,
    )

    compiled_proposal = proposal_factory.app_factory.compile()
    client.send.init_proposal_contract(args=(len(compiled_proposal.approval_program),))
    data_size_per_transaction = load_proposal_contract_data_size_per_transaction()
    bulks = 1 + len(compiled_proposal.approval_program) // data_size_per_transaction
    for i in range(bulks):
        chunk = compiled_proposal.approval_program[
            i * data_size_per_transaction : (i + 1) * data_size_per_transaction
        ]
        client.send.load_proposal_contract(
            args=(i * data_size_per_transaction, chunk),
        )

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
def funded_xgov_registry_client(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> XGovRegistryClient:
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer,
        min_spending_balance=TREASURY_AMOUNT,
        min_funding_increment=TREASURY_AMOUNT,
    )
    xgov_registry_client.send.deposit_funds(
        args=DepositFundsArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=TREASURY_AMOUNT,
                )
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
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account,
        min_spending_balance=INITIAL_FUNDS,
    )

    xgov_registry_client_committee_not_declared.send.subscribe_xgov(
        args=SubscribeXgovArgs(
            voting_address=account.address,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=account.address,
                    receiver=xgov_registry_client_committee_not_declared.app_address,
                    amount=get_xgov_fee(xgov_registry_client_committee_not_declared),
                )
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
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account,
        min_spending_balance=INITIAL_FUNDS,
    )

    xgov_registry_client_committee_not_declared.send.subscribe_proposer(
        args=SubscribeProposerArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=account.address,
                    receiver=xgov_registry_client_committee_not_declared.app_address,
                    amount=get_proposer_fee(
                        xgov_registry_client_committee_not_declared
                    ),
                )
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
def proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> ProposalClient:
    open_proposal_fee = get_open_proposal_fee(xgov_registry_client)
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=proposer,
        min_spending_balance=AlgoAmount(algo=2 * open_proposal_fee.algo),
        min_funding_increment=open_proposal_fee,
    )
    proposal_app_id = xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=open_proposal_fee,
                )
            )
        ),
        params=CommonAppCallParams(
            sender=proposer.address,
            static_fee=min_fee_times_3,
        ),
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
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=proposer,
        min_spending_balance=locked_amount,
        min_funding_increment=locked_amount,
    )
    proposal_client.send.open(
        args=OpenArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                )
            ),
            title=PROPOSAL_TITLE,
            funding_type=enm.FUNDING_RETROACTIVE,
            requested_amount=REQUESTED_AMOUNT.amount_in_micro_algo,
            focus=DEFAULT_FOCUS,
        )
    )

    composer = proposal_client.new_group()
    upload_metadata(composer, proposer, b"METADATA")
    composer.send()

    return proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
) -> ProposalClient:

    xgov_fee = get_xgov_fee(xgov_registry_client)
    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=proposer,
    )
    for cm in committee:
        algorand_client.account.ensure_funded_from_environment(
            account_to_fund=cm.account,
            min_spending_balance=AlgoAmount(algo=xgov_fee.algo * 2),
            min_funding_increment=xgov_fee,
        )
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=cm.account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=xgov_fee,
                    )
                ),
                voting_address=cm.account.address,
            ),
            params=CommonAppCallParams(sender=cm.account.address),
        )

        draft_proposal_client.send.assign_voters(
            args=AssignVotersArgs(
                voters=[(cm.account.address, cm.votes)],
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address),
        )
    return draft_proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client_requested_too_much(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    xgov_daemon: SigningAccount,
    proposer: SigningAccount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
) -> ProposalClient:
    reg_gs = xgov_registry_client.state.global_state
    outstanding_funds = reg_gs.outstanding_funds
    min_requested_amount = reg_gs.min_requested_amount

    # Ensure requested amount exceeds treasury by a meaningful margin
    # AND is at least the minimum required amount
    if outstanding_funds >= min_requested_amount:
        # Treasury has enough to cover minimum, so request more than available
        requested_amount = AlgoAmount(
            micro_algo=outstanding_funds + min_requested_amount)
    else:
        # Treasury is below minimum, use minimum + a buffer
        requested_amount = AlgoAmount(micro_algo=min_requested_amount * 2)

    locked_amount = get_locked_amount(requested_amount)
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=proposer,
        min_spending_balance=AlgoAmount(algo=locked_amount.algo * 2),
        min_funding_increment=locked_amount,
    )

    proposal_client.send.open(
        args=OpenArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=locked_amount,
                ),
            ),
            title=PROPOSAL_TITLE,
            funding_type=enm.FUNDING_RETROACTIVE,
            requested_amount=requested_amount.micro_algo,
            focus=DEFAULT_FOCUS,
        ),
        params=CommonAppCallParams(sender=proposer.address,
                                   static_fee=min_fee_times_3),
    )

    composer = proposal_client.new_group()
    upload_metadata(composer, proposer, b"METADATA")
    composer.send()

    submit_proposal(
        proposal_client=proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=proposer,
    )

    xgov_fee = get_xgov_fee(xgov_registry_client)
    for cm in committee:
        algorand_client.account.ensure_funded_from_environment(
            account_to_fund=cm.account,
            min_spending_balance=AlgoAmount(algo=xgov_fee.algo * 2),
            min_funding_increment=xgov_fee,
        )
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=cm.account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=xgov_fee,
                    )
                ),
                voting_address=cm.account.address,
            ),
            params=CommonAppCallParams(sender=cm.account.address),
        )

        proposal_client.send.assign_voters(
            args=AssignVotersArgs(voters=[(cm.account.address, cm.votes)]),
            params=CommonAppCallParams(sender=xgov_daemon.address),
        )
    return proposal_client


@pytest.fixture(scope="function")
def rejected_proposal_client(
    min_fee_times_2: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> ProposalClient:
    reg_gs = xgov_registry_client.state.global_state
    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = voting_proposal_client.state.global_state.vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)
    voting_proposal_client.send.scrutiny(
        params=CommonAppCallParams(static_fee=min_fee_times_2)
    )
    return voting_proposal_client


@pytest.fixture(scope="function")
def rejected_unassigned_voters_proposal_client(
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
    rejected_proposal_client: ProposalClient,
) -> ProposalClient:
    bulks = 6

    for i in range(1 + len(committee) // bulks):
        rejected_proposal_client.send.unassign_voters(
            args=UnassignVotersArgs(
                voters=[
                    cm.account.address for cm in committee[i * bulks : (i + 1) * bulks]
                ]
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address),
        )
    return rejected_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client(
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> ProposalClient:
    for cm in committee:
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(
                sender=cm.account.address,
                static_fee=min_fee_times_2,
                app_references=[
                    voting_proposal_client.app_id
                ],  # FIXME: This should have been autopopulated
            ),
        )

    reg_gs = xgov_registry_client.state.global_state
    voting_duration = reg_gs.voting_duration_small
    open_ts = voting_proposal_client.state.global_state.open_ts
    time_warp(open_ts + voting_duration)
    voting_proposal_client.send.scrutiny()
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
    algorand_client: AlgorandClient,
    min_fee_times_2: AlgoAmount,
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client_requested_too_much: ProposalClient,
) -> ProposalClient:
    for cm in committee:
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client_requested_too_much.app_id,
                xgov_address=cm.account.address,
                approval_votes=cm.votes,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(
                sender=cm.account.address,
                static_fee=min_fee_times_2,
                app_references=[
                    voting_proposal_client_requested_too_much.app_id
                ],  # FIXME: This should have been autopopulated
            ),
        )

    reg_gs = xgov_registry_client.state.global_state
    voting_duration = reg_gs.voting_duration_xlarge
    open_ts = voting_proposal_client_requested_too_much.state.global_state.open_ts
    time_warp(open_ts + voting_duration)
    voting_proposal_client_requested_too_much.send.scrutiny()
    return voting_proposal_client_requested_too_much


@pytest.fixture(scope="function")
def funded_proposal_client(
    min_fee_times_4: AlgoAmount,
    xgov_payor: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
    reviewed_proposal_client: ProposalClient,
) -> ProposalClient:
    funded_xgov_registry_client.send.pay_grant_proposal(
        args=PayGrantProposalArgs(
            proposal_id=reviewed_proposal_client.app_id,
        ),
        params=CommonAppCallParams(
            sender=xgov_payor.address, static_fee=min_fee_times_4
        ),
    )
    return reviewed_proposal_client


@pytest.fixture(scope="function")
def funded_unassigned_voters_proposal_client(
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
    funded_proposal_client: ProposalClient,
) -> ProposalClient:
    bulks = 6
    for i in range(1 + len(committee) // bulks):
        funded_proposal_client.send.unassign_voters(
            args=UnassignVotersArgs(
                voters=[
                    cm.account.address for cm in committee[i * bulks : (i + 1) * bulks]
                ],
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address),
        )
    return funded_proposal_client


@pytest.fixture(scope="function")
def blocked_unassigned_voters_proposal_client(
    xgov_daemon: SigningAccount,
    committee: list[CommitteeMember],
    blocked_proposal_client: ProposalClient,
) -> ProposalClient:
    bulks = 6
    for i in range(1 + len(committee) // bulks):
        blocked_proposal_client.send.unassign_voters(
            args=UnassignVotersArgs(
                voters=[
                    cm.account.address for cm in committee[i * bulks : (i + 1) * bulks]
                ],
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address),
        )
    return blocked_proposal_client


@pytest.fixture(scope="function")
def xgov_subscriber_app(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
) -> XGovSubscriberAppMockClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )

    factory = algorand_client.client.get_typed_app_factory(
        XGovSubscriberAppMockFactory,
        default_sender=deployer.address,
        default_signer=deployer.signer,
    )
    client, _ = factory.send.create.bare()  # type: ignore
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_FUNDS,
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
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=get_xgov_fee(xgov_registry_client),
                )
            ),
        ),
        params=CommonAppCallParams(sender=no_role_account.address),
    )

    return xgov_subscriber_app
