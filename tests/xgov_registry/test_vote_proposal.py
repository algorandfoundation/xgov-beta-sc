import pytest

from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient
from smart_contracts.artifacts.proposal_mock.client import ProposalMockClient

from algosdk.encoding import decode_address

from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    logic_error_type,
    COMMITTEE_ID,
    COMMITTEE_VOTES,
    COMMITTEE_SIZE,
)

from smart_contracts.proposal import enums as enm

def test_vote_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
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

    # voting
    proposal_mock_client.set_status(
        status=enm.STATUS_VOTING,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    xgov_registry_client.vote_proposal(
        proposal_id=proposal_mock_client.app_id,
        xgov_address=xgov.address,
        approval_votes=COMMITTEE_VOTES,
        rejection_votes=0,
        null_votes=0,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp,
            boxes=[(0, b"x" + decode_address(xgov.address))],
            foreign_apps=[(proposal_mock_client.app_id)],
            accounts=[(xgov.address)]
        ),
    )

def test_vote_proposal_not_in_voting_phase(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
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

    # voting
    proposal_mock_client.set_status(
        status=enm.STATUS_VOTING,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    xgov_registry_client.vote_proposal(
        proposal_id=proposal_mock_client.app_id,
        xgov_address=xgov.address,
        approval_votes=COMMITTEE_VOTES,
        rejection_votes=0,
        null_votes=0,
        transaction_parameters=TransactionParameters(
            sender=xgov.address,
            signer=xgov.signer,
            suggested_params=sp,
            boxes=[(0, b"x" + decode_address(xgov.address))],
            foreign_apps=[(proposal_mock_client.app_id)],
            accounts=[(xgov.address)]
        ),
    )

def test_vote_proposal_wrong_vote_amount(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
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

    # voting
    proposal_mock_client.set_status(
        status=enm.STATUS_VOTING,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=err.INVALID_VOTE):
        xgov_registry_client.vote_proposal(
            proposal_id=proposal_mock_client.app_id,
            xgov_address=xgov.address,
            approval_votes=(COMMITTEE_VOTES + 1),
            rejection_votes=0,
            null_votes=0,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(xgov.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(proposer.address)]
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

    with pytest.raises(logic_error_type, match=err.INVALID_PROPOSAL):
        xgov_registry_client.vote_proposal(
            proposal_id=xgov_registry_client.app_id,
            xgov_address=xgov.address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            null_votes=0,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(xgov.address))],
                foreign_apps=[(xgov_registry_client.app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_vote_proposal_not_an_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
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

    # voting
    proposal_mock_client.set_status(
        status=enm.STATUS_VOTING,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.vote_proposal(
            proposal_id=proposal_mock_client.app_id,
            xgov_address=random_account.address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            null_votes=0,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(random_account.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(random_account.address)]
            ),
        )

def test_vote_proposal_wrong_voting_address(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    proposer: AddressAndSigner,
    random_account: AddressAndSigner,
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

    # voting
    proposal_mock_client.set_status(
        status=enm.STATUS_VOTING,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    proposal_mock_client.set_committee_details(
        id=COMMITTEE_ID,
        size=COMMITTEE_SIZE,
        votes=COMMITTEE_VOTES,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=err.MUST_BE_VOTING_ADDRESS):
        xgov_registry_client.vote_proposal(
            proposal_id=proposal_mock_client.app_id,
            xgov_address=xgov.address,
            approval_votes=0,
            rejection_votes=COMMITTEE_VOTES,
            null_votes=0,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, b"x" + decode_address(xgov.address))],
                foreign_apps=[(proposal_mock_client.app_id)],
                accounts=[(xgov.address)]
            ),
        )