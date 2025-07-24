from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)


def test_pause_and_resume(
    xgov_registry_client: XGovRegistryClient,
) -> None:

    # Pause Registry
    assert not xgov_registry_client.state.global_state.paused_registry
    xgov_registry_client.send.pause_registry()
    assert xgov_registry_client.state.global_state.paused_registry
    xgov_registry_client.send.resume_registry()
    assert not xgov_registry_client.state.global_state.paused_registry

    # Pause Proposals
    assert not xgov_registry_client.state.global_state.paused_proposals
    xgov_registry_client.send.pause_proposals()
    assert xgov_registry_client.state.global_state.paused_proposals
    xgov_registry_client.send.resume_proposals()
    assert not xgov_registry_client.state.global_state.paused_proposals
