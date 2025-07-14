import pytest
from algokit_utils import (
    CreateTransactionParameters,
    EnsureBalanceParameters,
    TransactionParameters,
    ensure_funded,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.config import config
from algokit_utils.models import Account
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.encoding import encode_address
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
    XGovRegistryConfig,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
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
    finalize_proposal,
    get_locked_amount,
    upload_metadata,
)
from tests.utils import time_warp
from tests.xgov_registry.common import (
    TREASURY_AMOUNT,
    UNLIMITED_KYC_EXPIRATION,
    get_voter_box_key,
    proposer_box_name,
    request_box_name,
    xgov_box_name,
)


@pytest.fixture(scope="function")
def xgov_registry_config() -> XGovRegistryConfig:
    return XGovRegistryConfig(
        xgov_fee=regcfg.XGOV_FEE,
        proposer_fee=regcfg.PROPOSER_FEE,
        open_proposal_fee=regcfg.OPEN_PROPOSAL_FEE,
        daemon_ops_funding_bps=regcfg.DAEMON_OPS_FUNDING_BPS,
        proposal_commitment_bps=regcfg.PROPOSAL_COMMITMENT_BPS,
        min_requested_amount=regcfg.MIN_REQUESTED_AMOUNT,
        max_requested_amount=[
            regcfg.MAX_REQUESTED_AMOUNT_SMALL,
            regcfg.MAX_REQUESTED_AMOUNT_MEDIUM,
            regcfg.MAX_REQUESTED_AMOUNT_LARGE,
        ],
        discussion_duration=[
            regcfg.DISCUSSION_DURATION_SMALL,
            regcfg.DISCUSSION_DURATION_MEDIUM,
            regcfg.DISCUSSION_DURATION_LARGE,
            regcfg.DISCUSSION_DURATION_XLARGE,
        ],
        voting_duration=[
            regcfg.VOTING_DURATION_SMALL,
            regcfg.VOTING_DURATION_MEDIUM,
            regcfg.VOTING_DURATION_LARGE,
            regcfg.VOTING_DURATION_XLARGE,
        ],
        quorum=[
            regcfg.QUORUM_SMALL,
            regcfg.QUORUM_MEDIUM,
            regcfg.QUORUM_LARGE,
        ],
        weighted_quorum=[
            regcfg.WEIGHTED_QUORUM_SMALL,
            regcfg.WEIGHTED_QUORUM_MEDIUM,
            regcfg.WEIGHTED_QUORUM_LARGE,
        ],
    )


@pytest.fixture(scope="function")
def xgov_registry_client_committee_not_declared(
    algorand_client: AlgorandClient,
    deployer: Account,
    committee_manager: AddressAndSigner,
    xgov_subscriber: AddressAndSigner,
    xgov_payor: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    xgov_council: AddressAndSigner,
    kyc_provider: AddressAndSigner,
    xgov_registry_config: XGovRegistryConfig,
    sp_min_fee_times_2: SuggestedParams,
) -> XGovRegistryClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_2

    client = XGovRegistryClient(
        algorand_client.client.algod,
        sender=deployer.address,
        creator=deployer,
        indexer_client=algorand_client.client.indexer,
        template_values={"entropy": b""},
    )

    client.create_create(
        transaction_parameters=CreateTransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    # Set xGov Registry Role-Based Access Control
    client.set_committee_manager(
        manager=committee_manager.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_xgov_subscriber(
        subscriber=xgov_subscriber.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_payor(
        payor=xgov_payor.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_xgov_daemon(
        xgov_daemon=xgov_daemon.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_xgov_council(
        council=xgov_council.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_kyc_provider(
        provider=kyc_provider.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    # Configure xGov Registry
    client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )
    return client


@pytest.fixture(scope="function")
def xgov_registry_client(
    algorand_client: AlgorandClient,
    committee_manager: Account,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> XGovRegistryClient:
    xgov_registry_client_committee_not_declared.declare_committee(
        committee_id=DEFAULT_COMMITTEE_ID,
        size=DEFAULT_COMMITTEE_MEMBERS,
        votes=DEFAULT_COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=committee_manager.address,
            signer=committee_manager.signer,
            suggested_params=sp_min_fee_times_2,
        ),
    )
    return xgov_registry_client_committee_not_declared


@pytest.fixture(scope="function")
def funded_xgov_registry_client(
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> XGovRegistryClient:
    sp = sp_min_fee_times_2
    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=TREASURY_AMOUNT,
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )
    return xgov_registry_client


@pytest.fixture(scope="function")
def xgov(
    algorand_client: AlgorandClient,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    global_state = xgov_registry_client_committee_not_declared.get_global_state()

    xgov_registry_client_committee_not_declared.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=account.address,
                    receiver=xgov_registry_client_committee_not_declared.app_address,
                    amount=global_state.xgov_fee,
                ),
            ),
            signer=account.signer,
        ),
        voting_address=account.address,
        transaction_parameters=TransactionParameters(
            sender=account.address,
            signer=account.signer,
            boxes=[(0, xgov_box_name(account.address))],
        ),
    )

    return account


@pytest.fixture(scope="function")
def proposer(
    algorand_client: AlgorandClient,
    kyc_provider: AddressAndSigner,
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=regcfg.MAX_REQUESTED_AMOUNT_LARGE,
        ),
    )

    global_state = xgov_registry_client_committee_not_declared.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client_committee_not_declared.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=account.address,
                    receiver=xgov_registry_client_committee_not_declared.app_address,
                    amount=global_state.proposer_fee,
                ),
            ),
            signer=account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=account.address,
            signer=account.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(account.address))],
        ),
    )

    xgov_registry_client_committee_not_declared.set_proposer_kyc(
        proposer=account.address,
        kyc_status=True,
        kyc_expiring=UNLIMITED_KYC_EXPIRATION,
        transaction_parameters=TransactionParameters(
            sender=kyc_provider.address,
            signer=kyc_provider.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(account.address))],
        ),
    )

    return account


@pytest.fixture(scope="function")
def proposal_client(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_3

    global_state = xgov_registry_client.get_global_state()

    open_proposal_response = xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    proposal_app_id = open_proposal_response.return_value

    proposal_client = ProposalClient(
        algorand_client.client.algod,
        app_id=proposal_app_id,
    )

    return proposal_client


@pytest.fixture(scope="function")
def draft_proposal_client(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    proposal_client: ProposalClient,
) -> ProposalClient:
    registry_id = proposal_client.get_global_state().registry_app_id

    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=get_locked_amount(REQUESTED_AMOUNT),
                ),
            ),
            signer=proposer.signer,
        ),
        title=PROPOSAL_TITLE,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=REQUESTED_AMOUNT,
        focus=DEFAULT_FOCUS,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[registry_id],
        ),
    )

    composer = proposal_client.compose()
    upload_metadata(composer, proposer, registry_id, b"METADATA")
    composer.execute()

    return proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client(
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    draft_proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_3

    global_state = xgov_registry_client.get_global_state()

    finalize_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_mock_client=xgov_registry_client,
        proposer=proposer,
        xgov_daemon=xgov_daemon,
        sp_min_fee_times_2=sp,
    )

    for committee_member in committee_members:
        xgov_registry_client.subscribe_xgov(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=committee_member.address,
                        signer=committee_member.signer,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.xgov_fee,
                    ),
                ),
                signer=committee_member.signer,
            ),
            voting_address=committee_member.address,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                boxes=[(0, xgov_box_name(committee_member.address))],
            ),
        )

        draft_proposal_client.assign_voters(
            voters=[(committee_member.address, 10)],
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[xgov_registry_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    return draft_proposal_client


@pytest.fixture(scope="function")
def voting_proposal_client_requested_too_much(
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    proposer: AddressAndSigner,
    xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_3

    global_state = xgov_registry_client.get_global_state()

    requested_amount = TREASURY_AMOUNT + 1

    proposal_client.submit(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=proposal_client.app_address,
                    amount=get_locked_amount(requested_amount),
                ),
            ),
            signer=proposer.signer,
        ),
        title=PROPOSAL_TITLE,
        funding_type=enm.FUNDING_RETROACTIVE,
        requested_amount=requested_amount,
        focus=DEFAULT_FOCUS,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[xgov_registry_client.app_id],
        ),
    )

    composer = proposal_client.compose()
    upload_metadata(composer, proposer, xgov_registry_client.app_id, b"METADATA")
    composer.execute()

    finalize_proposal(
        proposal_client=proposal_client,
        xgov_registry_mock_client=xgov_registry_client,
        proposer=proposer,
        xgov_daemon=xgov_daemon,
        sp_min_fee_times_2=sp,
    )

    for committee_member in committee_members:
        xgov_registry_client.subscribe_xgov(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=committee_member.address,
                        signer=committee_member.signer,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.xgov_fee,
                    ),
                ),
                signer=committee_member.signer,
            ),
            voting_address=committee_member.address,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                boxes=[(0, xgov_box_name(committee_member.address))],
            ),
        )

        proposal_client.assign_voters(
            voters=[(committee_member.address, 10)],
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[xgov_registry_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    return proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client(
    algorand_client: AlgorandClient,
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_3

    for committee_member in committee_members:
        xgov_registry_client.vote_proposal(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee_member.address,
            approval_votes=10,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[
                    xgov_registry_client.app_id,
                    voting_proposal_client.app_id,
                ],
                boxes=[
                    (0, xgov_box_name(committee_member.address)),
                    (
                        voting_proposal_client.app_id,
                        get_voter_box_key(committee_member.address),
                    ),
                ],
                suggested_params=sp,
            ),
        )

    reg_gs = xgov_registry_client.get_global_state()
    voting_duration = reg_gs.voting_duration_small  # 86400
    submission_ts = (
        voting_proposal_client.get_global_state().submission_ts
    )  # 1_751_447_221
    time_warp(submission_ts + voting_duration)  # 1_751_533_621

    voting_proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=committee_member.address,
            signer=committee_member.signer,
            foreign_apps=[xgov_registry_client.app_id, voting_proposal_client.app_id],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    return voting_proposal_client


@pytest.fixture(scope="function")
def reviewed_proposal_client(
    xgov_council: AddressAndSigner,
    approved_proposal_client: ProposalClient,
) -> ProposalClient:
    approved_proposal_client.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_council.address,
            signer=xgov_council.signer,
            foreign_apps=[approved_proposal_client.get_global_state().registry_app_id],
        ),
    )
    return approved_proposal_client


@pytest.fixture(scope="function")
def approved_proposal_client_requested_too_much(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    voting_proposal_client_requested_too_much: ProposalClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_3

    for committee_member in committee_members:
        xgov_registry_client.vote_proposal(
            proposal_id=voting_proposal_client_requested_too_much.app_id,
            xgov_address=committee_member.address,
            approval_votes=10,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[
                    xgov_registry_client.app_id,
                    voting_proposal_client_requested_too_much.app_id,
                ],
                boxes=[
                    (0, xgov_box_name(committee_member.address)),
                    (
                        voting_proposal_client_requested_too_much.app_id,
                        get_voter_box_key(committee_member.address),
                    ),
                ],
                suggested_params=sp,
            ),
        )

    reg_gs = xgov_registry_client.get_global_state()
    voting_duration = reg_gs.voting_duration_xlarge
    submission_ts = (
        voting_proposal_client_requested_too_much.get_global_state().submission_ts
    )
    time_warp(submission_ts + voting_duration)

    voting_proposal_client_requested_too_much.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_client.app_id,
                voting_proposal_client_requested_too_much.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client_requested_too_much.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    return voting_proposal_client_requested_too_much


@pytest.fixture(scope="function")
def funded_proposal_client(
    xgov_council: AddressAndSigner,
    xgov_payor: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    reviewed_proposal_client: ProposalClient,
    sp_min_fee_times_4: SuggestedParams,
) -> ProposalClient:
    sp = sp_min_fee_times_4

    proposer_address: str = encode_address(reviewed_proposal_client.get_global_state().proposer.as_bytes)  # type: ignore

    funded_xgov_registry_client.pay_grant_proposal(
        proposal_id=reviewed_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_payor.address,
            signer=xgov_payor.signer,
            foreign_apps=[reviewed_proposal_client.app_id],
            accounts=[proposer_address],
            boxes=[
                (
                    0,
                    proposer_box_name(proposer_address),
                )
            ],
            suggested_params=sp,
        ),
    )

    return reviewed_proposal_client


@pytest.fixture(scope="function")
def funded_unassigned_voters_proposal_client(
    xgov_daemon: AddressAndSigner,
    funded_proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
) -> ProposalClient:

    bulks = 6

    for i in range(1 + len(committee_members) // bulks):
        funded_proposal_client.unassign_voters(
            voters=[
                cm.address for cm in committee_members[i * bulks : (i + 1) * bulks]
            ],
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[
                    funded_proposal_client.get_global_state().registry_app_id
                ],
                boxes=[
                    (
                        0,
                        get_voter_box_key(cm.address),
                    )
                    for cm in committee_members[i * bulks : (i + 1) * bulks]
                ],
            ),
        )

    return funded_proposal_client


@pytest.fixture(scope="function")
def xgov_subscriber_app(
    algorand_client: AlgorandClient,
    deployer: Account,
    sp_min_fee_times_2: SuggestedParams,
) -> XGovSubscriberAppMockClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = sp_min_fee_times_2

    client = XGovSubscriberAppMockClient(
        algorand_client.client.algod,
        sender=deployer.address,
        creator=deployer,
        indexer_client=algorand_client.client.indexer,
    )

    client.create_bare(
        transaction_parameters=CreateTransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    return client


@pytest.fixture(scope="function")
def app_xgov_subscribe_requested(
    algorand_client: AlgorandClient,
    xgov_registry_client: XGovRegistryClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    no_role_account: AddressAndSigner,
) -> XGovSubscriberAppMockClient:
    global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.request_subscribe_xgov(
        xgov_address=xgov_subscriber_app.app_address,
        owner_address=no_role_account.address,
        relation_type=0,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_fee,
                ),
            ),
            signer=no_role_account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            boxes=[
                (0, xgov_box_name(xgov_subscriber_app.app_address)),
                (0, request_box_name(global_state.request_id)),
            ],
            foreign_apps=[xgov_subscriber_app.app_id],
        ),
    )

    return xgov_subscriber_app
