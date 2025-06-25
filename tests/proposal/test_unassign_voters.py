import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import (
    assert_final_proposal_global_state,
    assert_rejected_proposal_global_state,
    assign_voters,
    logic_error_type,
    submit_proposal,
    unassign_voters,
)
from tests.utils import ERROR_TO_REGEX, time_warp

# TODO add tests for unassign on other statuses


def test_unassign_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    sp = algorand_client.get_suggested_params()

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
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer = proposal_client.compose()
        unassign_voters(
            composer,
            [],
            proposer,
            sp,
            xgov_registry_mock_client.app_id,
        )
        composer.execute()


def test_unassign_no_voters(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = proposal_client.compose()
    unassign_voters(
        composer,
        [],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign_one_voter(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:1],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=10 * (len(committee_members) - 1),
        voters_count=len(committee_members) - 1,
    )


def test_unassign_all_voters(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = proposal_client.compose()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        assigned_votes=0,
        voters_count=0,
    )


def test_unassign_metadata_ref(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match="invalid Box reference"):
        proposal_client.unassign_voters(
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

    global_state = proposal_client.get_global_state()

    assert_rejected_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )


def test_unassign__not_same_app(
    proposal_client: ProposalClient,
    alternative_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    not_proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    submit_proposal(
        alternative_proposal_client,
        algorand_client,
        not_proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = max(
        proposal_client.get_global_state().submission_ts,
        alternative_proposal_client.get_global_state().submission_ts,
    )
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize

    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    alternative_proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=not_proposer.address,
            signer=not_proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    composer = alternative_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = max(
        proposal_client.get_global_state().vote_open_ts,
        alternative_proposal_client.get_global_state().vote_open_ts,
    )
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    alternative_proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=not_proposer.address,
            signer=not_proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = proposal_client.compose()
    unassign_voters(
        composer,
        committee_members,
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )

    alternative_composer = alternative_proposal_client.compose()
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
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = proposal_client.compose()
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
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = proposal_client.compose()
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
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    composer = proposal_client.compose()
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
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_council: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[xgov_daemon.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    composer = proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members[:1],
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    composer = proposal_client.compose()
    unassign_voters(
        composer,
        committee_members[:1],
        xgov_daemon,
        sp,
        xgov_registry_mock_client.app_id,
    )
    composer.execute()

    global_state = proposal_client.get_global_state()

    assert_final_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )
