import pytest

from algokit_utils import (
    EnsureBalanceParameters,
    ensure_funded,
    get_localnet_default_account,
)
from algokit_utils.models import Account
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.config import config

from smart_contracts.artifacts.proposal_mock.client import ProposalMockClient
from smart_contracts.artifacts.xgov_registry.client import (
    XGovRegistryClient,
    XGovRegistryConfig
)

from smart_contracts.artifacts.xgov_subscriber_app_mock.client import XGovSubscriberAppMockClient

from algosdk.encoding import decode_address
from algosdk.atomic_transaction_composer import TransactionWithSigner

from tests.proposal.common import INITIAL_FUNDS
from tests.xgov_registry.common import (
    AddressAndSignerFromAccount,
    XGOV_MIN_BALANCE,
    PROPOSER_FEE,
    PROPOSAL_FEE,
    PROPOSAL_PUBLISHING_BPS,
    PROPOSAL_COMMITTMENT_BPS,
    MIN_REQUESTED_AMOUNT,
    MAX_REQUESTED_AMOUNT_SMALL,
    MAX_REQUESTED_AMOUNT_MEDIUM,
    MAX_REQUESTED_AMOUNT_LARGE,
    DISCUSSION_DURATION_SMALL,
    DISCUSSION_DURATION_MEDIUM,
    DISCUSSION_DURATION_LARGE,
    DISCUSSION_DURATION_XLARGE,
    VOTING_DURATION_SMALL,
    VOTING_DURATION_MEDIUM,
    VOTING_DURATION_LARGE,
    VOTING_DURATION_XLARGE,
    COOL_DOWN_DURATION,
    QUORUM_SMALL,
    QUORUM_MEDIUM,
    QURUM_LARGE,
    WEIGHTED_QUORUM_SMALL,
    WEIGHTED_QUORUM_MEDIUM,
    WEIGHTED_QUORUM_LARGE,
)

@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client

@pytest.fixture(scope="function")
def deployer(algorand_client: AlgorandClient) -> Account:
    deployer = get_localnet_default_account(algorand_client.client.algod)
    account = AddressAndSignerFromAccount(deployer)
    algorand_client.account.set_signer(deployer.address, account.signer)

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=deployer.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    return deployer

@pytest.fixture(scope="function")
def committee_manager(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account
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
    xgov_registry_config: XGovRegistryConfig
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
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp
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
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp
        ),
    )

    client.set_committee_manager(
        manager=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp
        ),
    )

    # Call the config_xgov_registry method
    client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp
        ),
    )

    client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=client.app_address,
                    amount=10_000_001
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
def xgov_registry_config() -> XGovRegistryConfig:
    return XGovRegistryConfig(
        xgov_min_balance=XGOV_MIN_BALANCE,
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
        quorum=[
            QUORUM_SMALL,
            QUORUM_MEDIUM,
            QURUM_LARGE,
        ],
        weighted_quorum=[
            WEIGHTED_QUORUM_SMALL,
            WEIGHTED_QUORUM_MEDIUM,
            WEIGHTED_QUORUM_LARGE,
        ]
    )

@pytest.fixture(scope="function")
def xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient
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
    sp.min_fee *= 2  # type: ignore

    print(global_state.xgov_min_balance)

    xgov_registry_client.subscribe_xgov(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.xgov_min_balance
                ),
            ),
            signer=account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=account.address,
            signer=account.signer,
            suggested_params=sp,
            boxes=[(0, b"x" + decode_address(account.address))]
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
                    amount=global_state.proposer_fee
                ),
            ),
            signer=account.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=account.address,
            signer=account.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(account.address))]
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
            boxes=[(0, b"p" + decode_address(account.address))]
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
                    amount=global_state.proposal_fee
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))]
        ),
    )

    proposal_mock_app_id = open_proposal_response.return_value
    
    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
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
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp
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
