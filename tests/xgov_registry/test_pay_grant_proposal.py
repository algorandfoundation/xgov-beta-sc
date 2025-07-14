import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    LogicErrorType,
    proposer_box_name,
)


def test_pay_grant_proposal_success(
    xgov_council: AddressAndSigner,
    xgov_payor: AddressAndSigner,
    proposer: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    reviewed_proposal_client: ProposalClient,
    sp_min_fee_times_4: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_4

    proposal_global_state = reviewed_proposal_client.get_global_state()

    before_info = funded_xgov_registry_client.algod_client.account_info(
        funded_xgov_registry_client.app_address,
    )

    # payout
    funded_xgov_registry_client.pay_grant_proposal(
        proposal_id=reviewed_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_payor.address,
            signer=xgov_payor.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
            foreign_apps=[reviewed_proposal_client.app_id],
            accounts=[proposer.address],
        ),
    )

    after_info = funded_xgov_registry_client.algod_client.account_info(
        funded_xgov_registry_client.app_address,
    )

    assert (before_info["amount"] - proposal_global_state.requested_amount) == after_info["amount"]  # type: ignore


def test_pay_grant_proposal_not_payor(
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    approved_proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    # payout
    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.pay_grant_proposal(
            proposal_id=approved_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[approved_proposal_client.app_id],
                accounts=[proposer.address],
            ),
        )


def test_pay_grant_proposal_not_a_proposal_app(
    algorand_client: AlgorandClient,
    xgov_payor: AddressAndSigner,
    proposer: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2
    # payout
    with pytest.raises(LogicErrorType, match=err.INVALID_PROPOSAL):
        funded_xgov_registry_client.pay_grant_proposal(
            proposal_id=funded_xgov_registry_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_payor.address,
                signer=xgov_payor.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                accounts=[proposer.address],
                foreign_apps=[funded_xgov_registry_client.app_id],
            ),
        )


# TODO: Change to `_not_milestone`
def test_pay_grant_proposal_not_reviewed(
    algorand_client: AlgorandClient,
    xgov_payor: AddressAndSigner,
    proposer: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    proposal_client: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    # payout
    with pytest.raises(LogicErrorType, match=err.PROPOSAL_WAS_NOT_REVIEWED):
        funded_xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_payor.address,
                signer=xgov_payor.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[proposal_client.app_id],
                accounts=[proposer.address],
            ),
        )


def test_pay_grant_proposal_invalid_kyc(
    algorand_client: AlgorandClient,
    xgov_council: AddressAndSigner,
    kyc_provider: AddressAndSigner,
    xgov_payor: AddressAndSigner,
    proposer: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    reviewed_proposal_client: ProposalClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    funded_xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=False,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=kyc_provider.address,
            signer=kyc_provider.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(LogicErrorType, match=err.INVALID_KYC):
        funded_xgov_registry_client.pay_grant_proposal(
            proposal_id=reviewed_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_payor.address,
                signer=xgov_payor.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[reviewed_proposal_client.app_id],
                accounts=[proposer.address],
            ),
        )


def test_pay_grant_proposal_expired_kyc(
    algorand_client: AlgorandClient,
    xgov_council: AddressAndSigner,
    kyc_provider: AddressAndSigner,
    xgov_payor: AddressAndSigner,
    proposer: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    reviewed_proposal_client: ProposalClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    funded_xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=kyc_provider.address,
            signer=kyc_provider.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    # payout
    with pytest.raises(LogicErrorType, match=err.INVALID_KYC):
        funded_xgov_registry_client.pay_grant_proposal(
            proposal_id=reviewed_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_payor.address,
                signer=xgov_payor.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[reviewed_proposal_client.app_id],
                accounts=[proposer.address],
            ),
        )


def test_pay_grant_proposal_insufficient_funds(
    algorand_client: AlgorandClient,
    xgov_council: AddressAndSigner,
    xgov_payor: AddressAndSigner,
    proposer: AddressAndSigner,
    funded_xgov_registry_client: XGovRegistryClient,
    approved_proposal_client_requested_too_much: ProposalClient,
    sp_min_fee_times_3: SuggestedParams,
) -> None:

    approved_proposal_client_requested_too_much.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_council.address,
            signer=xgov_council.signer,
            foreign_apps=[funded_xgov_registry_client.app_id],
        ),
    )

    sp = sp_min_fee_times_3

    # payout
    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_TREASURY_FUNDS):
        funded_xgov_registry_client.pay_grant_proposal(
            proposal_id=approved_proposal_client_requested_too_much.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_payor.address,
                signer=xgov_payor.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
                foreign_apps=[approved_proposal_client_requested_too_much.app_id],
                accounts=[proposer.address],
            ),
        )
