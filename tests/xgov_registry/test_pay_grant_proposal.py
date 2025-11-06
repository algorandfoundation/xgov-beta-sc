import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
    ReviewArgs,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    PayGrantProposalArgs,
    SetProposerKycArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import UNLIMITED_KYC_EXPIRATION


def test_pay_grant_proposal_success(
    algorand_client: AlgorandClient,
    min_fee_times_4: AlgoAmount,
    proposer: SigningAccount,
    xgov_payor: SigningAccount,
    reviewed_proposal_client: ProposalClient,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_treasury_amount = algorand_client.account.get_information(
        funded_xgov_registry_client.app_address
    ).amount.micro_algo
    initial_proposer_amount = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo
    requested_amount = reviewed_proposal_client.state.global_state.requested_amount
    locked_amount = reviewed_proposal_client.state.global_state.locked_amount

    funded_xgov_registry_client.send.pay_grant_proposal(
        args=PayGrantProposalArgs(proposal_id=reviewed_proposal_client.app_id),
        params=CommonAppCallParams(
            sender=xgov_payor.address, static_fee=min_fee_times_4
        ),
    )

    final_treasury_amount = algorand_client.account.get_information(
        funded_xgov_registry_client.app_address
    ).amount.micro_algo
    final_proposer_amount = algorand_client.account.get_information(
        proposer.address
    ).amount.micro_algo

    assert initial_treasury_amount - final_treasury_amount == requested_amount
    assert (
        final_proposer_amount - initial_proposer_amount
        == requested_amount + locked_amount
    )


def test_pay_grant_proposal_not_payor(
    min_fee_times_4: AlgoAmount,
    proposer: SigningAccount,
    reviewed_proposal_client: ProposalClient,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        funded_xgov_registry_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_id=reviewed_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=proposer.address, static_fee=min_fee_times_4
            ),
        )


def test_pay_grant_proposal_not_a_proposal_app(
    min_fee_times_4: AlgoAmount,
    xgov_payor: SigningAccount,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PROPOSAL):
        funded_xgov_registry_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(
                proposal_id=funded_xgov_registry_client.app_id,
            ),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_4
            ),
        )


def test_pay_grant_proposal_not_reviewed(
    min_fee_times_4: AlgoAmount,
    xgov_payor: SigningAccount,
    approved_proposal_client: ProposalClient,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        funded_xgov_registry_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_id=approved_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_4
            ),
        )


def test_pay_grant_proposal_invalid_kyc(
    min_fee_times_4: AlgoAmount,
    kyc_provider: SigningAccount,
    proposer: SigningAccount,
    xgov_payor: SigningAccount,
    reviewed_proposal_client: ProposalClient,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    funded_xgov_registry_client.send.set_proposer_kyc(
        args=SetProposerKycArgs(
            proposer=proposer.address,
            kyc_status=False,
            kyc_expiring=UNLIMITED_KYC_EXPIRATION,
        ),
        params=CommonAppCallParams(sender=kyc_provider.address),
    )
    with pytest.raises(LogicError, match=err.INVALID_KYC):
        funded_xgov_registry_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_id=reviewed_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_4
            ),
        )


def test_pay_grant_proposal_expired_kyc(
    min_fee_times_4: AlgoAmount,
    kyc_provider: SigningAccount,
    proposer: SigningAccount,
    xgov_payor: SigningAccount,
    reviewed_proposal_client: ProposalClient,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    funded_xgov_registry_client.send.set_proposer_kyc(
        args=SetProposerKycArgs(
            proposer=proposer.address,
            kyc_status=True,
            kyc_expiring=0,
        ),
        params=CommonAppCallParams(sender=kyc_provider.address),
    )
    with pytest.raises(LogicError, match=err.INVALID_KYC):
        funded_xgov_registry_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(proposal_id=reviewed_proposal_client.app_id),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_4
            ),
        )


def test_pay_grant_proposal_insufficient_funds(
    min_fee_times_2: AlgoAmount,
    min_fee_times_4: AlgoAmount,
    xgov_council: SigningAccount,
    xgov_payor: SigningAccount,
    approved_proposal_client_requested_too_much: ProposalClient,
    funded_xgov_registry_client: XGovRegistryClient,
) -> None:
    approved_proposal_client_requested_too_much.send.review(
        args=ReviewArgs(block=False),
        params=CommonAppCallParams(
            sender=xgov_council.address, static_fee=min_fee_times_2
        ),
    )
    with pytest.raises(LogicError, match=err.INSUFFICIENT_TREASURY_FUNDS):
        funded_xgov_registry_client.send.pay_grant_proposal(
            args=PayGrantProposalArgs(
                proposal_id=approved_proposal_client_requested_too_much.app_id
            ),
            params=CommonAppCallParams(
                sender=xgov_payor.address, static_fee=min_fee_times_4
            ),
        )
