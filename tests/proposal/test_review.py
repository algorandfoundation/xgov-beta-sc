import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err

# TODO add tests for review on other statuses
from tests.proposal.common import (
    assert_reviewed_proposal_global_state,
    logic_error_type,
)
from tests.utils import ERROR_TO_REGEX


def test_review_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.review(
            block=False,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_review_draft_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        submitted_proposal_client.review(
            block=False,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_review_final_proposal(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        finalized_proposal_client.review(
            block=False,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_review_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        voting_proposal_client.review(
            block=False,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_review_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_council: AddressAndSigner,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        rejected_proposal_client.review(
            block=False,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_review_success(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:

    approved_proposal_client.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_council.address,
            signer=xgov_council.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    global_state = approved_proposal_client.get_global_state()

    assert_reviewed_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )


def test_review_twice(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:

    approved_proposal_client.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_council.address,
            signer=xgov_council.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        approved_proposal_client.review(
            block=False,
            transaction_parameters=TransactionParameters(
                sender=xgov_council.address,
                signer=xgov_council.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                note="Second review",
            ),
        )

    global_state = approved_proposal_client.get_global_state()

    assert_reviewed_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )


def test_review_not_council(
    approved_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    no_role_account: AddressAndSigner,
) -> None:

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        approved_proposal_client.review(
            block=False,
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )
