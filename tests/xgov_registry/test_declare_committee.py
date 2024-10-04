import pytest

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils import TransactionParameters

from smart_contracts.errors import std_errors as err

from tests.xgov_registry.common import (
    logic_error_type,
    committee_id,
    committee_size,
    committee_votes,
)

def test_declare_committee_success(
    xgov_registry_client: XGovRegistryClient,
    committee_manager: AddressAndSigner
) -> None:
    xgov_registry_client.declare_committee(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=committee_manager.address,
            signer=committee_manager.signer,
        ),
    )

def test_declare_committee_not_manager(
    xgov_registry_client: XGovRegistryClient,
    random_account: AddressAndSigner
) -> None:
    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.declare_committee(
            id=committee_id,
            size=committee_size,
            votes=committee_votes,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
            ),
        )