from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts.artifacts.proposal.client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.client import XgovRegistryMockClient
from tests.proposal.common import assert_proposal_global_state


def test_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    global_state = proposal_client.get_global_state()

    assert_proposal_global_state(
        global_state=global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
