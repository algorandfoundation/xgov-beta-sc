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

from smart_contracts.artifacts.proposal_mock.client import ProposalMockClient
from smart_contracts.artifacts.xgov_registry.client import (
    XGovRegistryClient,
    XGovRegistryConfig,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.proposal import enums as enm
from tests.proposal.common import INITIAL_FUNDS
from tests.xgov_registry.common import (
    COMMITTEE_ID,
    COMMITTEE_SIZE,
    COMMITTEE_VOTES,
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
    PROPOSAL_COMMITTMENT_BPS,
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
        proposal_commitment_bps=PROPOSAL_COMMITTMENT_BPS,
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
def proposal_mock_client(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> ProposalMockClient:
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

    proposal_mock_app_id = open_proposal_response.return_value

    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    return proposal_mock_client


@pytest.fixture(scope="function")
def approved_proposal_mock_client(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> ProposalMockClient:
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

    proposal_mock_app_id = open_proposal_response.return_value

    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        cid=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    return proposal_mock_client


@pytest.fixture(scope="function")
def voting_proposal_mock_client(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
) -> ProposalMockClient:
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

    proposal_mock_app_id = open_proposal_response.return_value

    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_VOTING,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        cid=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    return proposal_mock_client


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
