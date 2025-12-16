import pytest
from algokit_utils import (
    AppClientCompilationParams,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err


def test_update_xgov_registry_success(
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.update.update_xgov_registry(
        compilation_params=AppClientCompilationParams(
            deploy_time_params={
                "entropy": b"",
                "governance_period": 69,
                "committee_grace_period": 42,
            }
        ),
    )


def test_update_xgov_registry_not_manager(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.update.update_xgov_registry(
            compilation_params=AppClientCompilationParams(
                deploy_time_params={
                    "entropy": b"",
                    "governance_period": 69,
                    "committee_grace_period": 42,
                }
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )
