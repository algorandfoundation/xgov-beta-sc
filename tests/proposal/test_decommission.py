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
    assert_account_balance,
    assert_decommissioned_proposal_global_state,
    assert_empty_proposal_global_state,
    decommission_proposal,
    get_voter_box_key,
    logic_error_type,
    submit_proposal,
    unassign_voters,
)
from tests.utils import ERROR_TO_REGEX, time_warp

# TODO add tests for decommission on other statuses


def test_decommission_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_publisher: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_client.decommission(
        transaction_parameters=TransactionParameters(
            sender=committee_publisher.address,
            signer=committee_publisher.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            boxes=[(0, METADATA_BOX_KEY)],
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

    assert_account_balance(algorand_client, proposal_client.app_address, 0)


def test_decommission_draft_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_publisher: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    locked_amount = proposal_client.get_global_state().locked_amount
    proposer_balance = algorand_client.account.get_information(proposer.address)[  # type: ignore
        "amount"
    ]

    proposal_client.decommission(
        transaction_parameters=TransactionParameters(
            sender=committee_publisher.address,
            signer=committee_publisher.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[proposer.address],
            boxes=[(0, METADATA_BOX_KEY)],
            suggested_params=sp,
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_decommissioned_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        committee_id=b"",
        committee_members=0,
        committee_votes=0,
        voters_count=0,
        assigned_votes=0,
    )

    assert_account_balance(algorand_client, proposal_client.app_address, 0)
    assert_account_balance(
        algorand_client, proposer.address, proposer_balance + locked_amount  # type: ignore
    )


def test_decommission_final_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_publisher: AddressAndSigner,
    proposer: AddressAndSigner,
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
            accounts=[committee_publisher.address],
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )


def test_decommission_voting_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_reviewer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
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
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )


def test_decommission_approved_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
                boxes=[
                    (
                        proposal_client.app_id,
                        get_voter_box_key(committee_member.address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )


def test_decommission_reviewed_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    xgov_reviewer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
                boxes=[
                    (
                        proposal_client.app_id,
                        get_voter_box_key(committee_member.address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    proposal_client.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_reviewer.address,
            signer=xgov_reviewer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )


def test_decommission_success_rejected_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
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
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

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

    cooldown_duration = reg_gs.cooldown_duration
    cooldown_start_ts = proposal_client.get_global_state().cool_down_start_ts
    time_warp(cooldown_start_ts + cooldown_duration)

    unassign_voters(
        proposal_client,
        committee_members,
        committee_publisher,
        sp,
        xgov_registry_mock_client.app_id,
    )

    decommission_proposal(
        proposal_client,
        committee_publisher,
        sp,
        xgov_registry_mock_client.app_id,
    )

    global_state = proposal_client.get_global_state()

    assert_decommissioned_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(algorand_client, proposal_client.app_address, 0)


def test_decommission_success_blocked_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
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
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
                boxes=[
                    (
                        proposal_client.app_id,
                        get_voter_box_key(committee_member.address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    proposal_client.review(
        block=True,
        transaction_parameters=TransactionParameters(
            sender=xgov_reviewer.address,
            signer=xgov_reviewer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            suggested_params=sp,
        ),
    )

    cooldown_duration = reg_gs.cooldown_duration
    cooldown_start_ts = proposal_client.get_global_state().cool_down_start_ts
    time_warp(cooldown_start_ts + cooldown_duration)

    unassign_voters(
        proposal_client,
        committee_members,
        committee_publisher,
        sp,
        xgov_registry_mock_client.app_id,
    )

    decommission_proposal(
        proposal_client,
        committee_publisher,
        sp,
        xgov_registry_mock_client.app_id,
    )

    global_state = proposal_client.get_global_state()

    assert_decommissioned_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(algorand_client, proposal_client.app_address, 0)


def test_decommission_success_funded_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    reg_gs = xgov_registry_mock_client.get_global_state()
    discussion_duration = reg_gs.discussion_duration_small

    submission_ts = proposal_client.get_global_state().submission_ts
    time_warp(submission_ts + discussion_duration)  # so we could actually finalize
    proposal_client.finalize(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

    for committee_member in committee_members[:4]:
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_member.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_member.address,
                signer=committee_member.signer,
                foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
                boxes=[
                    (
                        proposal_client.app_id,
                        get_voter_box_key(committee_member.address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    voting_duration = reg_gs.voting_duration_small
    vote_open_ts = proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    proposal_client.scrutiny(
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    proposal_client.review(
        block=False,
        transaction_parameters=TransactionParameters(
            sender=xgov_reviewer.address,
            signer=xgov_reviewer.signer,
            foreign_apps=[xgov_registry_mock_client.app_id],
        ),
    )

    xgov_registry_mock_client.fund(
        proposal_app=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[proposal_client.app_id],
        ),
    )

    cooldown_duration = reg_gs.cooldown_duration
    cooldown_start_ts = proposal_client.get_global_state().cool_down_start_ts
    time_warp(cooldown_start_ts + cooldown_duration)

    unassign_voters(
        proposal_client,
        committee_members,
        committee_publisher,
        sp,
        xgov_registry_mock_client.app_id,
    )

    decommission_proposal(
        proposal_client,
        committee_publisher,
        sp,
        xgov_registry_mock_client.app_id,
    )

    global_state = proposal_client.get_global_state()

    assert_decommissioned_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(algorand_client, proposal_client.app_address, 0)


def test_decommission_too_early(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
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
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

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

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.TOO_EARLY]):
        proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )


def test_decommission_not_publisher(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
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
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

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

    cooldown_duration = reg_gs.cooldown_duration
    cooldown_start_ts = proposal_client.get_global_state().cool_down_start_ts
    time_warp(cooldown_start_ts + cooldown_duration)

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )


def test_decommission_wrong_box_ref(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
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
            accounts=[committee_publisher.address],
            suggested_params=sp,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
    )

    for committee_member in committee_members:
        proposal_client.assign_voter(
            voter=committee_member.address,
            voting_power=10,
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_member.address),
                    )
                ],
            ),
        )

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

    cooldown_duration = reg_gs.cooldown_duration
    cooldown_start_ts = proposal_client.get_global_state().cool_down_start_ts
    time_warp(cooldown_start_ts + cooldown_duration)

    unassign_voters(
        proposal_client,
        committee_members[:-1],
        committee_publisher,
        sp,
        xgov_registry_mock_client.app_id,
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTERS_ASSIGNED]):
        proposal_client.decommission(
            transaction_parameters=TransactionParameters(
                sender=committee_publisher.address,
                signer=committee_publisher.signer,
                foreign_apps=[xgov_registry_mock_client.app_id],
                boxes=[
                    (
                        0,
                        get_voter_box_key(committee_members[-1].address),
                    )
                ],
                suggested_params=sp,
            ),
        )
