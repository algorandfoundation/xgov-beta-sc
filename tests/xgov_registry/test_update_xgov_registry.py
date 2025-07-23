import pytest
from algokit_utils import SigningAccount, CommonAppCallParams, AppClientCompilationParams, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err

from tests.utils import ERROR_TO_REGEX


def test_update_xgov_registry_success(
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.update.update_xgov_registry(
        compilation_params=AppClientCompilationParams(
            deploy_time_params={"entropy": b""}
        )
    )


def test_update_xgov_registry_not_manager(
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        xgov_registry_client.send.update.update_xgov_registry(
            compilation_params=AppClientCompilationParams(
                deploy_time_params={"entropy": b""}
            ),
            params=CommonAppCallParams(sender=no_role_account.address)
        )
