from pathlib import Path

import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    SigningAccount,
)
from algosdk.constants import MIN_TXN_FEE
from dotenv import load_dotenv

from tests.common import (
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_MEMBER_VOTES,
    INITIAL_FUNDS,
    CommitteeMember,
)


@pytest.fixture(autouse=True, scope="session")
def environment_fixture() -> None:
    env_path = Path(__file__).parent.parent / ".env.localnet"
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_localnet()
    client.set_suggested_params_cache_timeout(0)
    return client


@pytest.fixture(autouse=True, scope="function")
def reset_blockchain_timestamp(algorand_client: AlgorandClient):
    """Reset blockchain timestamp after each test to prevent time leakage"""
    yield  # Run the test first
    # Reset after test completes
    algorand_client.client.algod.set_timestamp_offset(0)


@pytest.fixture(autouse=True, scope="function")
def isolate_error_transformers(algorand_client: AlgorandClient):
    """Prevent error-transformer leakage between tests.

    Every ``AppClient`` created during test setup registers an error
    transformer on the shared session-scoped ``algorand_client``.
    Function-scoped clients are recreated each test, but their stale
    transformers accumulate and are never removed.

    The SDK identifies the owning app via a *substring* check
    (``f"app={app_id}" in str(error)``), so a stale transformer for
    e.g. app 1142 can incorrectly match an error for app 11423 because
    ``"app=1142"`` is a prefix of ``"app=11423"``.  When this happens
    the error is transformed using the wrong (stale) source map,
    stripping the human-readable error text and causing ``match=``
    assertions in ``pytest.raises`` to fail.

    This fixture snapshots the transformer set before each test (which
    contains only session-scoped transformers) and restores it
    afterwards, so function-scoped transformers never leak across tests.
    """
    baseline = algorand_client._error_transformers.copy()  # noqa: SLF001
    yield
    algorand_client._error_transformers.clear()  # noqa: SLF001
    algorand_client._error_transformers.update(baseline)  # noqa: SLF001


@pytest.fixture(scope="session")
def min_fee() -> AlgoAmount:
    return AlgoAmount(micro_algo=MIN_TXN_FEE)


@pytest.fixture(scope="session")
def min_fee_times_2() -> AlgoAmount:
    return AlgoAmount(micro_algo=MIN_TXN_FEE * 2)


@pytest.fixture(scope="session")
def min_fee_times_3() -> AlgoAmount:
    return AlgoAmount(micro_algo=MIN_TXN_FEE * 3)


@pytest.fixture(scope="session")
def min_fee_times_4() -> AlgoAmount:
    return AlgoAmount(micro_algo=MIN_TXN_FEE * 4)


@pytest.fixture(scope="session")
def deployer(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def committee_manager(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def xgov_subscriber(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def xgov_payor(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def xgov_daemon(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def xgov_council(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def kyc_provider(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account


@pytest.fixture(scope="session")
def committee_member(algorand_client: AlgorandClient) -> CommitteeMember:
    cm = CommitteeMember(
        account=algorand_client.account.random(), votes=DEFAULT_MEMBER_VOTES
    )

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=cm.account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return cm


@pytest.fixture(scope="session")
def committee(algorand_client: AlgorandClient) -> list[CommitteeMember]:
    members = [
        CommitteeMember(
            account=algorand_client.account.random(), votes=DEFAULT_MEMBER_VOTES
        )
        for _ in range(DEFAULT_COMMITTEE_MEMBERS)
    ]
    for cm in members:
        algorand_client.account.ensure_funded_from_environment(
            account_to_fund=cm.account.address,
            min_spending_balance=INITIAL_FUNDS,
        )
    return members


@pytest.fixture(scope="session")
def no_role_account(algorand_client: AlgorandClient) -> SigningAccount:
    account = algorand_client.account.random()
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=account.address,
        min_spending_balance=INITIAL_FUNDS,
    )
    return account
