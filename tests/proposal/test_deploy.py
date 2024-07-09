from algosdk.v2client.algod import AlgodClient

from smart_contracts.artifacts.proposal.client import ProposalClient


def test_says_hello(proposal_client: ProposalClient) -> None:
    result = proposal_client.hello(name="World")

    assert result.return_value == "Hello, World"


def test_simulate_says_hello_with_correct_budget_consumed(
    proposal_client: ProposalClient, algod_client: AlgodClient
) -> None:
    result = proposal_client.compose().hello(name="World").hello(name="Jane").simulate()

    assert result.abi_results[0].return_value == "Hello, World"  # type: ignore[misc]
    assert result.abi_results[1].return_value == "Hello, Jane"  # type: ignore[misc]
    assert result.simulate_response["txn-groups"][0]["app-budget-consumed"] < 100  # type: ignore[misc]
