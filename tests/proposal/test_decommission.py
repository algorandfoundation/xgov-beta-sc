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
from tests.proposal.common import (
    assert_account_balance,
    assert_blocked_proposal_global_state,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    assert_funded_proposal_global_state,
    assert_rejected_proposal_global_state,
    decommission_proposal,
    logic_error_type,
    unassign_voters,
)
from tests.utils import ERROR_TO_REGEX

# TODO add tests for decommission on other statuses


def test_decommission_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    xgov_registry_mock_client.decommission_proposal(
        proposal_app=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
            foreign_apps=[proposal_client.app_id],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        decommissioned=True,
    )
    min_balance = algorand_client.account.get_information(proposal_client.app_address)["min-balance"]  # type: ignore
    assert_account_balance(algorand_client, proposal_client.app_address, min_balance)  # type: ignore

    # Test that decommission cannot be replayed from this state
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.decommission_proposal(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[proposal_client.app_id],
                suggested_params=sp,
                note="replay decommissioning",
            ),
        )


def test_decommission_draft_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    proposer: AddressAndSigner,
    sp_min_fee_times_4: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_4

    locked_amount = submitted_proposal_client.get_global_state().locked_amount
    proposer_balance = algorand_client.account.get_information(proposer.address)[  # type: ignore
        "amount"
    ]

    xgov_registry_mock_client.decommission_proposal(
        proposal_app=submitted_proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
            foreign_apps=[submitted_proposal_client.app_id],
            accounts=[proposer.address],
            suggested_params=sp,
        ),
    )

    global_state = submitted_proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        decommissioned=True,
    )

    min_balance = algorand_client.account.get_information(  # type: ignore
        submitted_proposal_client.app_address
    )["min-balance"]
    assert_account_balance(
        algorand_client, submitted_proposal_client.app_address, min_balance  # type: ignore
    )
    assert_account_balance(
        algorand_client, proposer.address, proposer_balance + locked_amount  # type: ignore
    )

    # Test that decommission cannot be replayed from this state
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.decommission_proposal(
            proposal_app=submitted_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[submitted_proposal_client.app_id],
                accounts=[proposer.address],
                suggested_params=sp,
                note="replay decommissioning",
            ),
        )


def test_decommission_final_proposal(
    finalized_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    proposer: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.decommission_proposal(
            proposal_app=finalized_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[finalized_proposal_client.app_id],
                accounts=[proposer.address],
                suggested_params=sp,
            ),
        )


def test_decommission_voting_proposal(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.decommission_proposal(
            proposal_app=voting_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[voting_proposal_client.app_id],
                accounts=[proposer.address],
                suggested_params=sp,
            ),
        )


def test_decommission_approved_proposal(
    approved_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.decommission_proposal(
            proposal_app=approved_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[approved_proposal_client.app_id],
                accounts=[proposer.address],
                suggested_params=sp,
            ),
        )


def test_decommission_reviewed_proposal(
    reviewed_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.decommission_proposal(
            proposal_app=reviewed_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[reviewed_proposal_client.app_id],
                accounts=[proposer.address],
                suggested_params=sp,
            ),
        )


def test_decommission_success_rejected_proposal(
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

    global_state = rejected_proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        decommissioned=True,
    )

    min_balance = algorand_client.account.get_information(  # type: ignore
        rejected_proposal_client.app_address
    )["min-balance"]
    assert_account_balance(
        algorand_client, rejected_proposal_client.app_address, min_balance  # type: ignore
    )

    # Test that decommission cannot be replayed from this state
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        decommission_proposal(
            xgov_registry_mock_client,
            rejected_proposal_client.app_id,
            xgov_daemon,
            sp,
            note="replay decommissioning",
        )


def test_decommission_success_blocked_proposal(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    composer = blocked_proposal_client.compose()
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
        blocked_proposal_client.app_id,
        xgov_daemon,
        sp,
    )

    global_state = blocked_proposal_client.get_global_state()

    assert_blocked_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        decommissioned=True,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    min_balance = algorand_client.account.get_information(  # type: ignore
        blocked_proposal_client.app_address
    )["min-balance"]
    assert_account_balance(
        algorand_client, blocked_proposal_client.app_address, min_balance  # type: ignore
    )

    # Test that decommission cannot be replayed from this state
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        decommission_proposal(
            xgov_registry_mock_client,
            blocked_proposal_client.app_id,
            xgov_daemon,
            sp,
            note="replay decommissioning",
        )


def test_decommission_success_funded_proposal(
    funded_proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_3: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_3

    composer = funded_proposal_client.compose()
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
        funded_proposal_client.app_id,
        xgov_daemon,
        sp,
    )

    global_state = funded_proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        decommissioned=True,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    min_balance = algorand_client.account.get_information(  # type: ignore
        funded_proposal_client.app_address
    )["min-balance"]
    assert_account_balance(
        algorand_client, funded_proposal_client.app_address, min_balance  # type: ignore
    )

    # Test that decommission cannot be replayed from this state
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        decommission_proposal(
            xgov_registry_mock_client,
            funded_proposal_client.app_id,
            xgov_daemon,
            sp,
            note="replay decommissioning",
        )


def test_decommission_not_registry(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = rejected_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:-1],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        rejected_proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
            ),
        )


def test_decommission_wrong_box_ref(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = rejected_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:-1],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTERS_ASSIGNED]):
        xgov_registry_mock_client.decommission_proposal(
            proposal_app=rejected_proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[rejected_proposal_client.app_id],
                accounts=[proposer.address],
                suggested_params=sp,
            ),
        )
