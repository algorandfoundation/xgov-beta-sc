from pathlib import Path

import pytest
from algokit_utils import (
    EnsureBalanceParameters,
    ensure_funded,
    get_algod_client,
    get_indexer_client,
    get_localnet_default_account,
    is_localnet,
)
from algokit_utils.account import Account as AlgokitAccount
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.transaction import SuggestedParams
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv

from models.account import Account
from tests.common import DEFAULT_COMMITTEE_MEMBERS, INITIAL_FUNDS
from tests.xgov_registry.common import address_and_signer_from_account


@pytest.fixture(autouse=True, scope="session")
def environment_fixture() -> None:
    env_path = Path(__file__).parent.parent / ".env.localnet"
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    client = get_algod_client()

    # you can remove this assertion to test on other networks,
    # included here to prevent accidentally running against other networks
    assert is_localnet(client)
    return client


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return get_indexer_client()


@pytest.fixture(scope="session")
def faucet(algod_client: AlgodClient) -> Account:
    faucet = get_localnet_default_account(algod_client)
    return Account(private_key=faucet.private_key, client=algod_client)


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client


@pytest.fixture(scope="function")
def sp(algorand_client: AlgorandClient) -> SuggestedParams:
    return algorand_client.get_suggested_params()


@pytest.fixture(scope="function")
def sp_min_fee_times_2(sp: SuggestedParams) -> SuggestedParams:
    sp.min_fee *= 2  # type: ignore
    return sp


@pytest.fixture(scope="function")
def sp_min_fee_times_3(sp: SuggestedParams) -> SuggestedParams:
    sp.min_fee *= 3  # type: ignore
    return sp


@pytest.fixture(scope="function")
def sp_min_fee_times_4(sp: SuggestedParams) -> SuggestedParams:
    sp.min_fee *= 4  # type: ignore
    return sp


@pytest.fixture(scope="session")
def deployer(algorand_client: AlgorandClient) -> AlgokitAccount:
    deployer = get_localnet_default_account(algorand_client.client.algod)
    account = address_and_signer_from_account(deployer)
    algorand_client.account.set_signer(deployer.address, account.signer)

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=deployer.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    return deployer


@pytest.fixture(scope="session")
def committee_manager(
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
    return account


@pytest.fixture(scope="session")
def xgov_subscriber(
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
    return account


@pytest.fixture(scope="session")
def xgov_payor(
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
    return account


@pytest.fixture(scope="session")
def xgov_daemon(
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
    return account


@pytest.fixture(scope="session")
def xgov_council(
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
    return account


@pytest.fixture(scope="session")
def kyc_provider(
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
    return account


@pytest.fixture(scope="session")
def committee_member(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account


@pytest.fixture(scope="session")
def committee_members(algorand_client: AlgorandClient) -> list[AddressAndSigner]:
    accounts = [
        algorand_client.account.random() for _ in range(DEFAULT_COMMITTEE_MEMBERS)
    ]

    for account in accounts:
        ensure_funded(
            algorand_client.client.algod,
            EnsureBalanceParameters(
                account_to_fund=account.address,
                min_spending_balance_micro_algos=INITIAL_FUNDS,
            ),
        )

    return accounts


@pytest.fixture(scope="session")
def no_role_account(algorand_client: AlgorandClient) -> AddressAndSigner:
    account = algorand_client.account.random()

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=account.address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )
    return account
