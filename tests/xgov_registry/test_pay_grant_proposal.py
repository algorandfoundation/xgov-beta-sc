import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.models import Account

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
    XGovRegistryConfig,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    LogicErrorType,
    proposer_box_name,
)


def test_pay_grant_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    approved_proposal_client: ProposalClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    proposal_global_state = approved_proposal_client.get_global_state()

    before_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    # payout
    xgov_registry_client.pay_grant_proposal(
        proposal_id=approved_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
            foreign_apps=[(approved_proposal_client.app_id)],
            accounts=[(proposer.address)],
        ),
    )

    after_info = xgov_registry_client.algod_client.account_info(
        xgov_registry_client.app_address,
    )

    assert (before_info["amount"] - proposal_global_state.requested_amount) == after_info["amount"]  # type: ignore


def test_pay_grant_proposal_not_payor(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    approved_proposal_client: ProposalClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=approved_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[(approved_proposal_client.app_id)],
                accounts=[(proposer.address)],
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
    with pytest.raises(LogicErrorType, match=err.INVALID_PROPOSAL):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=xgov_registry_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                accounts=[proposer.address],
                foreign_apps=[xgov_registry_client.app_id],
            ),
        )


# TODO: Change to `_not_milestone`
def test_pay_grant_proposal_not_approved(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    proposal_client: ProposalClient,
) -> None:
    sp = algorand_client.get_suggested_params()

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(LogicErrorType, match=err.PROPOSAL_IS_NOT_APPROVED):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[(proposal_client.app_id)],
                accounts=[(proposer.address)],
            ),
        )


def test_pay_grant_proposal_invalid_kyc(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    approved_proposal_client: ProposalClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=False,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(LogicErrorType, match=err.INVALID_KYC):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=approved_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[(approved_proposal_client.app_id)],
                accounts=[(proposer.address)],
            ),
        )


def test_pay_grant_proposal_expired_kyc(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    approved_proposal_client: ProposalClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(LogicErrorType, match=err.INVALID_KYC):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=approved_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[(approved_proposal_client.app_id)],
                accounts=[(proposer.address)],
            ),
        )


def test_pay_grant_proposal_insufficient_funds(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
    approved_proposal_client_requested_too_much: ProposalClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_TREASURY_FUNDS):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=approved_proposal_client_requested_too_much.app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[(approved_proposal_client_requested_too_much.app_id)],
                accounts=[(proposer.address)],
            ),
        )
