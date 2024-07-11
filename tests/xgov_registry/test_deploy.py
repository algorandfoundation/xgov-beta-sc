from algosdk.v2client.algod import AlgodClient

from smart_contracts.artifacts.xgov_registry.client import XgovRegistryClient


def test_says_hello(xgov_registry_client: XgovRegistryClient) -> None:
    result = xgov_registry_client.hello(name="World")

    assert result.return_value == "Hello, World"


def test_simulate_says_hello_with_correct_budget_consumed(
    xgov_registry_client: XgovRegistryClient, algod_client: AlgodClient
) -> None:
    result = (
        xgov_registry_client.compose().hello(name="World").hello(name="Jane").simulate()
    )

    assert result.abi_results[0].return_value == "Hello, World"  # type: ignore[misc]
    assert result.abi_results[1].return_value == "Hello, Jane"  # type: ignore[misc]
    assert result.simulate_response["txn-groups"][0]["app-budget-consumed"] < 100  # type: ignore[misc]
