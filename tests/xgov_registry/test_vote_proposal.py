import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal_mock.proposal_mock_client import (
    ProposalMockClient,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    COMMITTEE_VOTES,
    LogicErrorType,
    xgov_box_name,
)


def test_vote_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    voting_proposal_mock_client: ProposalMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.vote_proposal(
        proposal_id=voting_proposal_mock_client.app_id,
        xgov_address=xgov.address,
        approval_votes=COMMITTEE_VOTES,
        rejection_votes=0,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp,
            boxes=[(0, xgov_box_name(xgov.address))],
            foreign_apps=[voting_proposal_mock_client.app_id],
            accounts=[xgov.address],
        ),
    )


def test_vote_proposal_not_in_voting_phase(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    proposal_mock_client: ProposalMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(LogicErrorType, match=err.PROPOSAL_IS_NOT_VOTING):
        xgov_registry_client.vote_proposal(
            proposal_id=proposal_mock_client.app_id,
            xgov_address=xgov.address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(xgov.address))],
                foreign_apps=[proposal_mock_client.app_id],
                accounts=[xgov.address],
            ),
        )


def test_vote_proposal_not_a_proposal_app(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(LogicErrorType, match=err.INVALID_PROPOSAL):
        xgov_registry_client.vote_proposal(
            proposal_id=xgov_registry_client.app_id,
            xgov_address=xgov.address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(xgov.address))],
                foreign_apps=[xgov_registry_client.app_id],
                accounts=[proposer.address],
            ),
        )


def test_vote_proposal_not_an_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
    voting_proposal_mock_client: ProposalMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.vote_proposal(
            proposal_id=voting_proposal_mock_client.app_id,
            xgov_address=random_account.address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(random_account.address))],
                foreign_apps=[voting_proposal_mock_client.app_id],
                accounts=[random_account.address],
            ),
        )


def test_vote_proposal_wrong_voting_address(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    random_account: AddressAndSigner,
    voting_proposal_mock_client: ProposalMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    with pytest.raises(LogicErrorType, match=err.MUST_BE_VOTING_ADDRESS):
        xgov_registry_client.vote_proposal(
            proposal_id=voting_proposal_mock_client.app_id,
            xgov_address=xgov.address,
            approval_votes=0,
            rejection_votes=COMMITTEE_VOTES,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(xgov.address))],
                foreign_apps=[voting_proposal_mock_client.app_id],
                accounts=[xgov.address],
            ),
        )
