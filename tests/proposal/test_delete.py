import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import logic_error_type
from tests.proposal.common import (
    decommission_proposal,
    unassign_voters,
)
from tests.utils import ERROR_TO_REGEX


def test_delete_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_draft_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        submitted_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_final_proposal(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        finalized_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        voting_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_approved_proposal(
    approved_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        approved_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_reviewed_proposal(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        reviewed_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_rejected_proposal(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        rejected_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_blocked_proposal(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        blocked_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_funded_proposal(
    funded_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        funded_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_delete_success(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    composer = rejected_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    decommission_proposal(
        xgov_registry_mock_client,
        rejected_proposal_client.app_id,
        xgov_daemon,
        sp,
    )

    rejected_proposal_client.delete_delete(
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
            suggested_params=sp,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(Exception, match="application does not exist"):
        algorand_client.client.algod.application_info(rejected_proposal_client.app_id)


def test_delete_not_xgov_daemon(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    composer = rejected_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    decommission_proposal(
        xgov_registry_mock_client,
        rejected_proposal_client.app_id,
        xgov_daemon,
        sp,
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        rejected_proposal_client.delete_delete(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )
