from algokit_utils import SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from tests.proposal.common import assert_empty_proposal_global_state


def test_empty_proposal(
    proposal_client: ProposalClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )
