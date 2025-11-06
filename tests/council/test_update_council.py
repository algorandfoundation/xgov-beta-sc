import pytest
from algokit_utils import (
    AppClientCompilationParams,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.council.council_client import CouncilClient
from smart_contracts.errors import std_errors as err
from tests.utils import ERROR_TO_REGEX


def test_update_council_success(
    deployer: SigningAccount,
    council_client: CouncilClient,
) -> None:
    """Test that the council contract can be updated by the manager."""
    council_client.send.update.update_council(
        compilation_params=AppClientCompilationParams(
            deploy_time_params={"entropy": b""}
        ),
        params=CommonAppCallParams(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )


def test_update_council_not_manager(
    no_role_account: SigningAccount,
    council_client: CouncilClient,
) -> None:
    """Test that the council contract cannot be updated by a non-manager."""
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        council_client.send.update.update_council(
            compilation_params=AppClientCompilationParams(
                deploy_time_params={"entropy": b""}
            ),
            params=CommonAppCallParams(
                sender=no_role_account.address,
                signer=no_role_account.signer,
            ),
        )


def test_update_council_preserves_state(
    deployer: SigningAccount,
    council_client: CouncilClient,
    council_members: list,
) -> None:
    """Test that the council contract update preserves existing state."""
    # Get the state before update
    before_global_state = council_client.state.global_state.get_all()
    before_member_count = before_global_state.get("member_count")
    before_registry_app_id = before_global_state.get("registry_app_id")

    # Update the contract
    council_client.send.update.update_council(
        compilation_params=AppClientCompilationParams(
            deploy_time_params={"entropy": b""}
        ),
        params=CommonAppCallParams(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    # Get the state after update
    after_global_state = council_client.state.global_state.get_all()
    after_member_count = after_global_state.get("member_count")
    after_registry_app_id = after_global_state.get("registry_app_id")

    # Verify state is preserved
    assert before_member_count == after_member_count
    assert before_registry_app_id == after_registry_app_id
