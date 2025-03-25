from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)


def test_pause_and_resume(
    xgov_registry_client: XGovRegistryClient,
) -> None:

    assert not xgov_registry_client.get_global_state().paused_registry

    xgov_registry_client.pause_registry()

    assert xgov_registry_client.get_global_state().paused_registry

    xgov_registry_client.resume_registry()

    assert not xgov_registry_client.get_global_state().paused_registry

    assert not xgov_registry_client.get_global_state().paused_proposals

    xgov_registry_client.pause_proposals()

    assert xgov_registry_client.get_global_state().paused_proposals

    xgov_registry_client.resume_proposals()

    assert not xgov_registry_client.get_global_state().paused_proposals
