import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.proposal.common import (
    assert_account_balance,
    assert_funded_proposal_global_state,
    get_voter_box_key,
    logic_error_type,
    submit_proposal,
)
from tests.utils import ERROR_TO_REGEX, time_warp

# TODO add tests for fund on other statuses


def test_fund_empty_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_draft_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_final_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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
            suggested_params=sp,
            accounts=[committee_publisher.address],
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_voting_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_approved_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_rejected_proposal(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_blocked_proposal(
    proposal_client: ProposalClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            ),
        )


def test_fund_success(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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

    proposer_balance_before = algorand_client.account.get_information(proposer.address)[  # type: ignore
        "amount"
    ]
    locked_amount = proposal_client.get_global_state().locked_amount

    xgov_registry_mock_client.fund(
        proposal_app=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[proposal_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before + locked_amount - sp.min_fee,  # type: ignore
    )


def test_fund_twice(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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

    proposer_balance_before = algorand_client.account.get_information(proposer.address)[  # type: ignore
        "amount"
    ]
    locked_amount = proposal_client.get_global_state().locked_amount

    xgov_registry_mock_client.fund(
        proposal_app=proposal_client.app_id,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            foreign_apps=[proposal_client.app_id],
        ),
    )

    global_state = proposal_client.get_global_state()

    assert_funded_proposal_global_state(
        global_state,
        proposer.address,
        xgov_registry_mock_client.app_id,
        voted_members=len(committee_members[:4]),
        approvals=10 * len(committee_members[:4]),
    )

    assert_account_balance(
        algorand_client,
        proposer.address,
        proposer_balance_before + locked_amount - sp.min_fee,  # type: ignore
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        xgov_registry_mock_client.fund(
            proposal_app=proposal_client.app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
                note="Second funding",
            ),
        )


def test_fund_not_registry(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    committee_publisher: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    xgov_reviewer: AddressAndSigner,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
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

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        proposal_client.fund(
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                foreign_apps=[proposal_client.app_id],
            )
        )
