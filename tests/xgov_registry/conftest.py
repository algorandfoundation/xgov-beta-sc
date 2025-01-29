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
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    DEFAULT_FOCUS,
    get_locked_amount,
    get_voter_box_key,
)
from tests.proposal.common import (
    INITIAL_FUNDS,
    PROPOSAL_CID,
    PROPOSAL_TITLE,
)
from tests.utils import time_warp
from tests.xgov_registry.common import (
    COOL_DOWN_DURATION,
    DEPOSIT_AMOUNT,
    DISCUSSION_DURATION_LARGE,
    DISCUSSION_DURATION_MEDIUM,
    DISCUSSION_DURATION_SMALL,
    DISCUSSION_DURATION_XLARGE,
    MAX_REQUESTED_AMOUNT_LARGE,
    MAX_REQUESTED_AMOUNT_MEDIUM,
    MAX_REQUESTED_AMOUNT_SMALL,
    MIN_REQUESTED_AMOUNT,
    PROPOSAL_COMMITMENT_BPS,
    PROPOSAL_FEE,
    PROPOSAL_PUBLISHING_BPS,
    PROPOSER_FEE,
    QUORUM_MEDIUM,
    QUORUM_SMALL,
    QURUM_LARGE,
    STALE_PROPOSAL_DURATION,
    VOTING_DURATION_LARGE,
    VOTING_DURATION_MEDIUM,
    VOTING_DURATION_SMALL,
    VOTING_DURATION_XLARGE,
    WEIGHTED_QUORUM_LARGE,
    WEIGHTED_QUORUM_MEDIUM,
    WEIGHTED_QUORUM_SMALL,
    XGOV_FEE,
    proposer_box_name,
    request_box_name,
    xgov_box_name,
)


@pytest.fixture(scope="function")
def committee_manager(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    xgov_registry_client.set_committee_manager(
        manager=account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    return account


@pytest.fixture(scope="function")
def xgov_registry_client(
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_registry_config: XGovRegistryConfig,
) -> XGovRegistryClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    client = XGovRegistryClient(
        algorand_client.client.algod,
        sender=deployer.address,
        creator=deployer,
        indexer_client=algorand_client.client.indexer,
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

    client.set_xgov_subscriber(
        subscriber=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_payor(
        payor=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_committee_manager(
        manager=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_committee_publisher(
        publisher=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.declare_committee(
        cid=DEFAULT_COMMITTEE_ID,
        size=DEFAULT_COMMITTEE_MEMBERS,
        votes=DEFAULT_COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    # Call the config_xgov_registry method
    client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=client.app_address,
                    amount=10_000_001,
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

    client.set_kyc_provider(
        provider=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    return client


@pytest.fixture(scope="function")
def funded_xgov_registry_client(
    algorand_client: AlgorandClient,
    deployer: Account,
    xgov_registry_config: XGovRegistryConfig,
) -> XGovRegistryClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    client = XGovRegistryClient(
        algorand_client.client.algod,
        sender=deployer.address,
        creator=deployer,
        indexer_client=algorand_client.client.indexer,
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

    client.set_xgov_subscriber(
        subscriber=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_payor(
        payor=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.set_committee_manager(
        manager=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    # Call the config_xgov_registry method
    client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=client.app_address,
                    amount=10_000_001,
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

    client.set_kyc_provider(
        provider=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=client.app_address,
                    amount=DEPOSIT_AMOUNT,
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

    return client


@pytest.fixture(scope="function")
def xgov_registry_config() -> XGovRegistryConfig:
    return XGovRegistryConfig(
        xgov_fee=XGOV_FEE,
        proposer_fee=PROPOSER_FEE,
        proposal_fee=PROPOSAL_FEE,
        proposal_publishing_bps=PROPOSAL_PUBLISHING_BPS,
        proposal_commitment_bps=PROPOSAL_COMMITMENT_BPS,
        min_requested_amount=MIN_REQUESTED_AMOUNT,
        max_requested_amount=[
            MAX_REQUESTED_AMOUNT_SMALL,
            MAX_REQUESTED_AMOUNT_MEDIUM,
            MAX_REQUESTED_AMOUNT_LARGE,
        ],
        discussion_duration=[
            DISCUSSION_DURATION_SMALL,
            DISCUSSION_DURATION_MEDIUM,
            DISCUSSION_DURATION_LARGE,
            DISCUSSION_DURATION_XLARGE,
        ],
        voting_duration=[
            VOTING_DURATION_SMALL,
            VOTING_DURATION_MEDIUM,
            VOTING_DURATION_LARGE,
            VOTING_DURATION_XLARGE,
        ],
        cool_down_duration=COOL_DOWN_DURATION,
        stale_proposal_duration=STALE_PROPOSAL_DURATION,
        quorum=[
            QUORUM_SMALL,
            QUORUM_MEDIUM,
            QURUM_LARGE,
        ],
        weighted_quorum=[
            WEIGHTED_QUORUM_SMALL,
            WEIGHTED_QUORUM_MEDIUM,
            WEIGHTED_QUORUM_LARGE,
        ],
    )


@pytest.fixture(scope="function")
def xgov(
    xgov_registry_client: XGovRegistryClient, algorand_client: AlgorandClient
) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=account.address,
                    receiver=xgov_registry_client.app_address,
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
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=account.address,
                    receiver=xgov_registry_client.app_address,
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

    xgov_registry_client.set_proposer_kyc(
        proposer=account.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(account.address))],
        ),
    )

    return account


@pytest.fixture(scope="function")
def random_account(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="function")
def proposal_client(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> ProposalClient:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    global_state = xgov_registry_client.get_global_state()

    open_proposal_response = xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposal_fee,
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
def voting_proposal_client(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    deployer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> ProposalClient:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    global_state = xgov_registry_client.get_global_state()

    open_proposal_response = xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposal_fee,
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

    sp.min_fee *= 2  # type: ignore

    requested_amount = 10_000_000

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
        cid=PROPOSAL_CID,
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

    reg_gs = xgov_registry_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small
    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)

    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_client.app_id],
            accounts=[deployer.address],
            suggested_params=sp,
        ),
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

        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
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
def voting_proposal_client_requested_too_much(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    deployer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> ProposalClient:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    global_state = xgov_registry_client.get_global_state()

    open_proposal_response = xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposal_fee,
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

    sp.min_fee *= 2  # type: ignore

    requested_amount = 10_000_000_000

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
        cid=PROPOSAL_CID,
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

    reg_gs = xgov_registry_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_xlarge
    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)

    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_client.app_id],
            accounts=[deployer.address],
            suggested_params=sp,
        ),
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

        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
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
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    voting_proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
) -> ProposalClient:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

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
    voting_duration = reg_gs.voting_duration_small
    submission_ts = voting_proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + voting_duration)

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
def approved_proposal_client_requested_too_much(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    voting_proposal_client_requested_too_much: ProposalClient,
    committee_members: list[AddressAndSigner],
) -> ProposalClient:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

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
            sender=committee_member.address,
            signer=committee_member.signer,
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
def xgov_subscriber_app(
    algorand_client: AlgorandClient,
    deployer: Account,
) -> XGovSubscriberAppMockClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

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
def app_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    deployer: Account,
) -> XGovSubscriberAppMockClient:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    xgov_registry_client.subscribe_xgov_app(
        app_id=xgov_subscriber_app.app_id,
        voting_address=deployer.address,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_fee,
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(xgov_subscriber_app.app_address))],
            foreign_apps=[xgov_subscriber_app.app_id],
        ),
    )

    return xgov_subscriber_app


@pytest.fixture(scope="function")
def app_xgov_subscribe_requested(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    deployer: Account,
) -> XGovSubscriberAppMockClient:
    global_state = xgov_registry_client.get_global_state()

    xgov_registry_client.request_subscribe_xgov(
        xgov_address=xgov_subscriber_app.app_address,
        owner_address=deployer.address,
        relation_type=0,
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_fee,
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            boxes=[
                (0, xgov_box_name(xgov_subscriber_app.app_address)),
                (0, request_box_name(global_state.request_id)),
            ],
            foreign_apps=[xgov_subscriber_app.app_id],
        ),
    )

    return xgov_subscriber_app
