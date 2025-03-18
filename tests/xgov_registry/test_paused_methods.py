from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)


def test_pause_and_resume(
    xgov_registry_client: XGovRegistryClient,
) -> None:

    assert (
        xgov_registry_client.get_global_state().paused_non_admin.as_hex == "00"
    )  # I.e, False

    xgov_registry_client.pause_non_admin()

    assert (
        xgov_registry_client.get_global_state().paused_non_admin.as_hex == "80"
    )  # I.e, True, is paused (ARC4 Boolean representation)

    xgov_registry_client.resume_non_admin()

    assert (
        xgov_registry_client.get_global_state().paused_non_admin.as_hex == "00"
    )  # I.e, False again

    assert xgov_registry_client.get_global_state().paused_proposals.as_hex == "00"

    xgov_registry_client.pause_proposals()

    assert xgov_registry_client.get_global_state().paused_proposals.as_hex == "80"

    xgov_registry_client.resume_proposals()

    assert xgov_registry_client.get_global_state().paused_proposals.as_hex == "00"
