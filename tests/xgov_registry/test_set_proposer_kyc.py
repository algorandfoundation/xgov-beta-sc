import pytest
from algokit_utils import CommonAppCallParams, LogicError, SigningAccount

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    SetProposerKycArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import UNLIMITED_KYC_EXPIRATION


def test_set_proposer_kyc_success(
    kyc_provider: SigningAccount,
    proposer_no_kyc: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.set_proposer_kyc(
        args=SetProposerKycArgs(
            proposer=proposer_no_kyc.address,
            kyc_status=True,
            kyc_expiring=UNLIMITED_KYC_EXPIRATION,
        ),
        params=CommonAppCallParams(sender=kyc_provider.address),
    )

    proposer_box = xgov_registry_client.state.box.proposer_box.get_value(
        proposer_no_kyc.address
    )
    assert proposer_box.kyc_status  # type: ignore
    assert proposer_box.kyc_expiring == UNLIMITED_KYC_EXPIRATION  # type: ignore


def test_set_proposer_kyc_not_kyc_provider(
    no_role_account: SigningAccount,
    proposer_no_kyc: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.set_proposer_kyc(
            args=SetProposerKycArgs(
                proposer=proposer_no_kyc.address,
                kyc_status=True,
                kyc_expiring=UNLIMITED_KYC_EXPIRATION,
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_set_proposer_kyc_not_a_proposer(
    no_role_account: SigningAccount,
    kyc_provider: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.PROPOSER_DOES_NOT_EXIST):
        xgov_registry_client.send.set_proposer_kyc(
            args=SetProposerKycArgs(
                proposer=no_role_account.address,
                kyc_status=True,
                kyc_expiring=UNLIMITED_KYC_EXPIRATION,
            ),
            params=CommonAppCallParams(sender=kyc_provider.address),
        )
