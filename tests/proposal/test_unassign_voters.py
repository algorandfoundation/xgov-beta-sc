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
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.common import logic_error_type
from tests.proposal.common import (
    assert_blocked_proposal_global_state,
    assert_final_proposal_global_state,
    assert_funded_proposal_global_state,
    assert_rejected_proposal_global_state,
    assign_voters,
    unassign_voters,
)
from tests.utils import ERROR_TO_REGEX, time_warp

# TODO add tests for unassign on other statuses


def test_unassign_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp: SuggestedParams,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = proposal_client.compose()
        unassign_voters(
            composer,
            committee_members,
            xgov_daemon,
            sp,
            xgov_registry_mock_client.app_id,
        )
        composer.execute()


def test_unassign_unauthorized(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer = submitted_proposal_client.compose()
        unassign_voters(
            composer,
            [],
            proposer,
            sp,
            xgov_registry_mock_client.app_id,
        )
        composer.execute()


def test_unassign_no_voters(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = rejected_proposal_client.compose()
    unassign_voters(
        composer,
        [],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = rejected_proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign_one_voter(
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
        committee_members[:1],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = rejected_proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_rejected_not_daemon(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    no_role_account: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = rejected_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:1],
        no_role_account,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = rejected_proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_funded_not_daemon(
    funded_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    no_role_account: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = funded_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:1],
        no_role_account,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = funded_proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_blocked_not_daemon(
    blocked_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    no_role_account: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = blocked_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:1],
        no_role_account,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = blocked_proposal_client.get_global_state()

    assert_blocked_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_all_voters(
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
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = rejected_proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=0,
        voters_count=0,
    )


def test_unassign_metadata_ref(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(logic_error_type, match="invalid Box reference"):
        rejected_proposal_client.unassign_voters(
            voters=[committee_members[0].address],
            transaction_parameters=TransactionParameters(
                sender=xgov_daemon.address,
                signer=xgov_daemon.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        METADATA_BOX_KEY.encode(),
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = rejected_proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign_not_same_app(
    submitted_proposal_client: ProposalClient,
    alternative_submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    no_role_account: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = submitted_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    composer = alternative_submitted_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    reg_gs = xgov_registry_mock_client.get_global_state()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = max(
        submitted_proposal_client.get_global_state().vote_open_ts,
        alternative_submitted_proposal_client.get_global_state().vote_open_ts,
    )
    time_warp(vote_open_ts + voting_duration + 1)

    submitted_proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    alternative_submitted_proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = submitted_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )

    alternative_composer = alternative_submitted_proposal_client.compose()
    unassign_voters(
        alternative_composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )

    alternative_composer.atc.txn_list[0] = composer.atc.txn_list[0]
    alternative_composer.atc.method_dict[0] = composer.atc.method_dict[0]

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_APP_ID]):
        alternative_composer.execute()


def test_unassign_not_same_method(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = rejected_proposal_client.compose()
    composer.get_state(
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
        ),
    )
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.execute()


def test_unassign_not_same_method_2(
    rejected_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = rejected_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.get_state(
        transaction_parameters=TransactionParameters(
            sender=xgov_daemon.address,
            signer=xgov_daemon.signer,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_METHOD_CALL]):
        composer.execute()


def test_unassign_one_call_not_xgov_daemon(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = submitted_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:-1],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    unassign_voters(
        composer,
        committee_members[-1:],
        proposer,
        sp,
        xgov_registry_mock_client.app_id,
    )
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer.execute()


def test_unassign_final_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    composer = submitted_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members[:1],
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    composer = submitted_proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:1],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = submitted_proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
