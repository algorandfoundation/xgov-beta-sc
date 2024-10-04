import pytest

from algokit_utils.models import Account
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams

from smart_contracts.artifacts.xgov_registry.client import (
    XGovRegistryClient,
    XGovRegistryConfig
)

from algosdk.encoding import decode_address
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.errors import std_errors as err
from smart_contracts.proposal import enums as enm
from tests.xgov_registry.common import (
    logic_error_type,
    committee_id,
    committee_votes,
    committee_size
)

from smart_contracts.artifacts.proposal_mock.client import ProposalMockClient

def test_pay_grant_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    proposal_mock_client: ProposalMockClient
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    xgov_registry_client.pay_grant_proposal(
        proposal_id=proposal_mock_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))],
            foreign_apps=[(proposal_mock_client.app_id)],
            accounts=[(proposer.address)]
        ),
    )

def test_pay_grant_proposal_not_payor(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    proposal_mock_client: ProposalMockClient
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_not_a_proposal_app(
    xgov_registry_client: XGovRegistryClient,
    xgov_registry_config: XGovRegistryConfig,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    # Call the config_xgov_registry method
    xgov_registry_client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    # payout
    with pytest.raises(logic_error_type, match=err.INVALID_PROPOSAL):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=xgov_registry_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                accounts=[(proposer.address)],
                foreign_apps=[xgov_registry_client.app_id]
            ),
        )

def test_pay_grant_proposal_not_approved(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    proposal_mock_client: ProposalMockClient
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_DRAFT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(logic_error_type, match=err.PROPOSAL_IS_NOT_APPROVED):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_invalid_kyc(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    proposal_mock_client: ProposalMockClient
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=False,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(logic_error_type, match=err.INVALID_KYC):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_expired_kyc(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    proposal_mock_client: ProposalMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(logic_error_type, match=err.EXPIRED_KYC):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_insufficient_funds(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    proposal_mock_client: ProposalMockClient
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_mock_client.set_requested_amount(
        requested_amount=100_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=committee_id,
        size=committee_size,
        votes=committee_votes,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(logic_error_type, match=err.INSUFFICIENT_TREASURY_FUNDS):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(proposer.address)]
            ),
        )