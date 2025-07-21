import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    SigningAccount,
    PaymentParams,
    AlgoAmount, AppClientCompilationParams, ALGORAND_MIN_TX_FEE)
from algokit_utils.config import config

from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
    OpenArgs,
    AssignVotersArgs, UnassignVotersArgs, ReviewArgs,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
    XGovRegistryConfig,
    XGovRegistryFactory,
    SetCommitteeManagerArgs,
    SetXgovCouncilArgs,
    SetXgovDaemonArgs,
    SetPayorArgs,
    SetKycProviderArgs,
    SetXgovSubscriberArgs,
    ConfigXgovRegistryArgs,
    DeclareCommitteeArgs,
    DepositFundsArgs,
    SubscribeXgovArgs,
    SubscribeProposerArgs,
    SetProposerKycArgs,
    OpenProposalArgs, VoteProposalArgs, PayGrantProposalArgs, RequestSubscribeXgovArgs,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockFactory,
    XGovSubscriberAppMockClient
)
from smart_contracts.proposal import enums as enm
from smart_contracts.xgov_registry import config as regcfg
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    INITIAL_FUNDS,
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
)


@pytest.fixture(scope="session")
def xgov_registry_config_dict() -> dict:
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
    config.configure(
        debug=False,
        populate_app_call_resources=True,
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
        params=CommonAppCallParams(sender=committee_manager.address)
    )
    return xgov_registry_client_committee_not_declared

@pytest.fixture(scope="function")
def funded_xgov_registry_client(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> XGovRegistryClient:
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
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )

    global_state = xgov_registry_client_committee_not_declared.state.global_state

    xgov_registry_client_committee_not_declared.send.subscribe_xgov(
        args=SubscribeXgovArgs(
            voting_address=account.address,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=account.address,
                    receiver=xgov_registry_client_committee_not_declared.app_address,
                    amount=global_state.xgov_fee,
                )
            )
        ),
        params=CommonAppCallParams(sender=account.address)
    )
    return account


@pytest.fixture(scope="function")
def proposer_no_kyc(
    algorand_client: AlgorandClient,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )

    global_state = xgov_registry_client_committee_not_declared.state.global_state
    xgov_registry_client_committee_not_declared.send.subscribe_proposer(
        args=SubscribeProposerArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                sender=account.address,
                receiver=xgov_registry_client_committee_not_declared.app_address,
                amount=AlgoAmount(micro_algo=global_state.proposer_fee),
            )
            )
        ),
        params=CommonAppCallParams(sender=account.address)
    )
    return account


@pytest.fixture(scope="function")
def proposer(
    proposer_no_kyc: SigningAccount,
    kyc_provider: SigningAccount,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> SigningAccount:
    xgov_registry_client_committee_not_declared.send.set_proposer_kyc(
        args=SetProposerKycArgs(
            proposer=proposer_no_kyc.address,
            kyc_status=True,
            kyc_expiring=UNLIMITED_KYC_EXPIRATION,
        ),
        params=CommonAppCallParams(sender=kyc_provider.address)
    )
    return proposer_no_kyc


@pytest.fixture(scope="function")
def proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> ProposalClient:
    global_state = xgov_registry_client.state.global_state

    proposal_app_id = xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                sender=proposer.address,
                receiver=xgov_registry_client.app_address,
                amount=AlgoAmount(micro_algo=global_state.open_proposal_fee),
            )
            )
        ),
        params=CommonAppCallParams(
            sender=proposer.address,
            static_fee=min_fee_times_3,
        )
    ).abi_return

    return ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id,
        default_sender=proposer.address
    )


@pytest.fixture(scope="function")
def draft_proposal_client(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> ProposalClient:
    proposal_client.send.open(
        args=OpenArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                sender=proposer.address,
                receiver=proposal_client.app_address,
                amount=get_locked_amount(REQUESTED_AMOUNT),
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
    committee_members: list[SigningAccount],
    xgov_registry_client: XGovRegistryClient,
    proposer: SigningAccount,
    draft_proposal_client: ProposalClient,
) -> ProposalClient:

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_client=xgov_registry_client,
        proposer=proposer,
    )

    for committee_member in committee_members:
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                    sender=committee_member.address,
                    receiver=xgov_registry_client.app_address,
                    amount=AlgoAmount(micro_algo=xgov_registry_client.state.global_state.xgov_fee),
                )
                ),
                voting_address=committee_member.address,
            ),
            params=CommonAppCallParams(sender=committee_member.address)
        )

        draft_proposal_client.send.assign_voters(
            args=AssignVotersArgs(
                voters=[(committee_member.address, 10)],
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )
    return draft_proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client_requested_too_much(
    algorand_client: AlgorandClient,
    xgov_daemon: SigningAccount,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
    committee_members: list[SigningAccount],
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_3

    global_state = xgov_registry_client.state.global_state

    requested_amount = AlgoAmount(micro_algo=TREASURY_AMOUNT.amount_in_micro_algo + 1)

    proposal_client.send.open(
        args=OpenArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                sender=proposer.address,
                receiver=proposal_client.app_address,
                amount=get_locked_amount(requested_amount),
            )
            ),
            title=PROPOSAL_TITLE,
            funding_type=enm.FUNDING_RETROACTIVE,
            requested_amount=requested_amount.amount_in_micro_algo,
            focus=DEFAULT_FOCUS,
        )
    )

    composer = proposal_client.new_group().composer()
    upload_metadata(composer, proposer, b"METADATA")
    composer.send()

    submit_proposal(
        proposal_client=proposal_client,
        xgov_registry_mock_client=xgov_registry_client,
        xgov_daemon=xgov_daemon,
    )

    for committee_member in committee_members:
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=committee_member.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.xgov_fee,
                    )
                ),
                voting_address=committee_member.address,
            ),
            params=CommonAppCallParams(sender=committee_member.address)
        )

        proposal_client.send.assign_voters(
            args=AssignVotersArgs(voters=[(committee_member.address, 10)]),
            params=CommonAppCallParams(sender=xgov_daemon.address)
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
    voting_proposal_client.send.scrutiny(params=CommonAppCallParams(static_fee=min_fee_times_2))
    return voting_proposal_client


@pytest.fixture(scope="function")
def rejected_unassigned_voters_proposal_client(
    xgov_daemon: SigningAccount,
    rejected_proposal_client: ProposalClient,
    committee_members: list[SigningAccount],
) -> ProposalClient:
    bulks = 6

    for i in range(1 + len(committee_members) // bulks):
        rejected_proposal_client.send.unassign_voters(
            args=UnassignVotersArgs(
                voters=[cm.address for cm in committee_members[i * bulks: (i + 1) * bulks]]
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )
    return rejected_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client(
    min_fee_times_2: AlgoAmount,
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
    committee_members: list[SigningAccount],
) -> ProposalClient:
    for committee_member in committee_members:
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client.app_id,
                xgov_address=committee_member.address,
                approval_votes=10,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(
                sender=committee_member.address,
                static_fee=min_fee_times_2,
                app_references=[voting_proposal_client.app_id]  # FIXME: This should have been autopopulated
            )
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
    approved_proposal_client: ProposalClient,
) -> ProposalClient:
    approved_proposal_client.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(sender=xgov_council.address)
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
        params=CommonAppCallParams(sender=xgov_council.address, static_fee=min_fee_times_2)
    )
    return approved_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client_requested_too_much(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    voting_proposal_client_requested_too_much: ProposalClient,
    committee_members: list[SigningAccount],
) -> ProposalClient:
    for committee_member in committee_members:
        xgov_registry_client.send.vote_proposal(
            args=VoteProposalArgs(
                proposal_id=voting_proposal_client_requested_too_much.app_id,
                xgov_address=committee_member.address,
                approval_votes=10,
                rejection_votes=0,
            ),
            params=CommonAppCallParams(sender=committee_member.address)
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
        params=CommonAppCallParams(sender=xgov_payor.address, static_fee=min_fee_times_4)
    )
    return reviewed_proposal_client


@pytest.fixture(scope="function")
def funded_unassigned_voters_proposal_client(
    xgov_daemon: SigningAccount,
    funded_proposal_client: ProposalClient,
    committee_members: list[SigningAccount],
) -> ProposalClient:
    bulks = 6
    for i in range(1 + len(committee_members) // bulks):
        funded_proposal_client.send.unassign_voters(
            args=UnassignVotersArgs(
                voters=[cm.address for cm in committee_members[i * bulks: (i + 1) * bulks]],
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address)
        )
    return funded_proposal_client


@pytest.fixture(scope="function")
def blocked_unassigned_voters_proposal_client(
    xgov_daemon: SigningAccount,
    blocked_proposal_client: ProposalClient,
    committee_members: list[SigningAccount],
) -> ProposalClient:
    bulks = 6
    for i in range(1 + len(committee_members) // bulks):
        blocked_proposal_client.send.unassign_voters(
            args=UnassignVotersArgs(
                voters=[cm.address for cm in committee_members[i * bulks: (i + 1) * bulks]],
            ),
            params=CommonAppCallParams(sender=xgov_daemon.address)
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
        XGovSubscriberAppMockFactory, default_sender=deployer.address, default_signer=deployer.signer
    )
    client, _ = factory.send.create.create()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return client


@pytest.fixture(scope="function")
def app_xgov_subscribe_requested(
    algorand_client: AlgorandClient,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    no_role_account: SigningAccount,
) -> XGovSubscriberAppMockClient:
    global_state = xgov_registry_client.state.global_state

    xgov_registry_client.send.request_subscribe_xgov(
        args=RequestSubscribeXgovArgs(
            xgov_address=xgov_subscriber_app.app_address,
            owner_address=no_role_account.address,
            relation_type=0,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_fee,
                )
            ),
        ),
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    return xgov_subscriber_app
