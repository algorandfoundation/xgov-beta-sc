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
    assert_boxes,
    assert_voting_proposal_global_state,
    assign_voters,
    submit_proposal,
)
from tests.utils import ERROR_TO_REGEX, time_warp
from tests.xgov_registry.common import LogicErrorType, get_voter_box_key


def test_vote_success(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=10,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [(get_voter_box_key(committee_members[0].address), "AAAAAAAAAAqA")],
    )


def test_vote_not_committee_member(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTER_NOT_FOUND]):
        xgov_registry_mock_client.vote(
            proposal_app=voting_proposal_client.app_id,
            voter=proposer.address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                foreign_apps=[
                    xgov_registry_mock_client.app_id,
                    voting_proposal_client.app_id,
                ],
                boxes=[
                    (voting_proposal_client.app_id, get_voter_box_key(proposer.address))
                ],
                suggested_params=sp,
            ),
        )


def test_vote_already_voted(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=10,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTER_ALREADY_VOTED]):
        xgov_registry_mock_client.vote(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                foreign_apps=[
                    xgov_registry_mock_client.app_id,
                    voting_proposal_client.app_id,
                ],
                boxes=[
                    (
                        voting_proposal_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    )
                ],
                suggested_params=sp,
                note="Second vote",
            ),
        )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [(get_voter_box_key(committee_members[0].address), "AAAAAAAAAAqA")],
    )


def test_vote_empty_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.vote(
            proposal_app=proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                foreign_apps=[xgov_registry_mock_client.app_id, proposal_client.app_id],
                boxes=[
                    (
                        proposal_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    )
                ],
                suggested_params=sp,
            ),
        )


def test_vote_draft_proposal(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.vote(
            proposal_app=draft_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                foreign_apps=[
                    xgov_registry_mock_client.app_id,
                    draft_proposal_client.app_id,
                ],
                boxes=[
                    (
                        draft_proposal_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    )
                ],
                suggested_params=sp,
            ),
        )


def test_vote_submitted_proposal(
    submitted_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.vote(
            proposal_app=submitted_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                foreign_apps=[
                    xgov_registry_mock_client.app_id,
                    submitted_proposal_client.app_id,
                ],
                boxes=[
                    (
                        submitted_proposal_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    )
                ],
                suggested_params=sp,
            ),
        )


def test_vote_voting_expired(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    reg_gs = xgov_registry_mock_client.get_global_state()

    voting_duration = reg_gs.voting_duration_small

    vote_open_ts = voting_proposal_client.get_global_state().vote_open_ts
    time_warp(vote_open_ts + voting_duration + 1)

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.VOTING_PERIOD_EXPIRED]
    ):
        xgov_registry_mock_client.vote(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=10,
            rejections=0,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                foreign_apps=[
                    xgov_registry_mock_client.app_id,
                    voting_proposal_client.app_id,
                ],
                boxes=[
                    (
                        voting_proposal_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members
        ],
    )


def test_vote_reject(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        rejections=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAqA",
            )
        ],
    )


def test_vote_null(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=0,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        nulls=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAqA",
            )
        ],
    )


def test_vote_mixed(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=10,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[1].address,
        approvals=0,
        rejections=10,
        transaction_parameters=TransactionParameters(
            sender=committee_members[1].address,
            signer=committee_members[1].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[1].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[2].address,
        approvals=0,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[2].address,
            signer=committee_members[2].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[2].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=3,
        approvals=10,
        rejections=10,
        nulls=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[3:]
        ]
        + [
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAqA",
            )
            for committee_member in committee_members[:3]
        ],
    )


def test_vote_mixed_same_vote_call(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    xgov_registry_mock_client.vote(
        proposal_app=voting_proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=6,
        rejections=4,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                voting_proposal_client.app_id,
            ],
            boxes=[
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=6,
        rejections=4,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAqA",
            )
        ],
    )


def test_vote_exceeded(
    voting_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTES_EXCEEDED]):
        xgov_registry_mock_client.vote(
            proposal_app=voting_proposal_client.app_id,
            voter=committee_members[0].address,
            approvals=6,
            rejections=5,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                foreign_apps=[
                    xgov_registry_mock_client.app_id,
                    voting_proposal_client.app_id,
                ],
                boxes=[
                    (
                        voting_proposal_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    )
                ],
                suggested_params=sp,
            ),
        )

    global_state = voting_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=voting_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_members[0].address),
                "AAAAAAAAAAoA",
            )
        ],
    )


def test_vote_paused_registry_error(
    draft_proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_daemon: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:

    sp = sp_min_fee_times_2

    xgov_registry_mock_client.pause_registry()
    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        submit_proposal(
            proposal_client=draft_proposal_client,
            xgov_registry_mock_client=xgov_registry_mock_client,
            proposer=proposer,
            xgov_daemon=xgov_daemon,
            sp_min_fee_times_2=sp,
        )

    xgov_registry_mock_client.resume_registry()

    submit_proposal(
        proposal_client=draft_proposal_client,
        xgov_registry_mock_client=xgov_registry_mock_client,
        proposer=proposer,
        xgov_daemon=xgov_daemon,
        sp_min_fee_times_2=sp,
    )

    composer = draft_proposal_client.compose()
    assign_voters(
        proposal_client_composer=composer,
        xgov_daemon=xgov_daemon,
        committee_members=committee_members,
        xgov_registry_app_id=xgov_registry_mock_client.app_id,
        sp=sp,
    )
    composer.execute()

    xgov_registry_mock_client.vote(
        proposal_app=draft_proposal_client.app_id,
        voter=committee_members[0].address,
        approvals=10,
        rejections=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            foreign_apps=[
                xgov_registry_mock_client.app_id,
                draft_proposal_client.app_id,
            ],
            boxes=[
                (
                    draft_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                )
            ],
            suggested_params=sp,
        ),
    )

    global_state = draft_proposal_client.get_global_state()

    assert_voting_proposal_global_state(
        global_state,
        proposer_address=proposer.address,
        registry_app_id=xgov_registry_mock_client.app_id,
        voted_members=1,
        approvals=10,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (
                get_voter_box_key(committee_member.address),
                "AAAAAAAAAAoA",
            )
            for committee_member in committee_members[1:]
        ]
        + [(get_voter_box_key(committee_members[0].address), "AAAAAAAAAAqA")],
    )
