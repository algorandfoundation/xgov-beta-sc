import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    BoxReference,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.council.council_client import CouncilClient, VoteArgs
from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.enums import STATUS_BLOCKED, STATUS_REVIEWED
from tests.common import CommitteeMember
from tests.council.common import members_box_name, votes_box_name
from tests.utils import ERROR_TO_REGEX


def test_vote_approve_success(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    council_members: list[CommitteeMember],
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient,
) -> None:

    proposal_id = approved_proposal_client.app_id
    half_plus_one = (len(council_members) // 2) + 1

    refs = [BoxReference(app_id=0, name=votes_box_name(proposal_id))]
    for member in council_members[:half_plus_one]:
        refs.append(
            BoxReference(app_id=0, name=members_box_name(member.account.address))
        )

    for member in council_members[:half_plus_one]:
        composer = council_client.new_group()

        composer.vote(
            args=VoteArgs(
                proposal_id=proposal_id,
                block=False,
            ),
            params=CommonAppCallParams(
                sender=member.account.address,
                signer=member.account.signer,
                static_fee=min_fee_times_3,
            ),
        )

        for i in range(5, len(refs), 8):
            composer.op_up(
                params=CommonAppCallParams(
                    box_references=refs[i : i + 8],
                )
            )

        composer.send()

    global_state = approved_proposal_client.state.global_state.get_all()

    assert global_state.get("status") == STATUS_REVIEWED


def test_vote_reject_success(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    council_members: list[CommitteeMember],
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient,
) -> None:

    proposal_id = approved_proposal_client.app_id
    half_plus_one = (len(council_members) // 2) + 1

    refs = [BoxReference(app_id=0, name=votes_box_name(proposal_id))]
    for member in council_members[:half_plus_one]:
        refs.append(
            BoxReference(app_id=0, name=members_box_name(member.account.address))
        )

    for member in council_members[:half_plus_one]:
        composer = council_client.new_group()

        composer.vote(
            args=VoteArgs(
                proposal_id=proposal_id,
                block=True,
            ),
            params=CommonAppCallParams(
                sender=member.account.address,
                signer=member.account.signer,
                static_fee=min_fee_times_3,
            ),
        )

        for i in range(5, len(refs), 8):
            composer.op_up(
                params=CommonAppCallParams(
                    box_references=refs[i : i + 8],
                )
            )

        composer.send()

    global_state = approved_proposal_client.state.global_state.get_all()

    assert global_state.get("status") == STATUS_BLOCKED


def test_vote_mix_success(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    council_members: list[CommitteeMember],
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient,
) -> None:

    proposal_id = approved_proposal_client.app_id
    half_plus_one = (len(council_members) // 2) + 1

    refs: list[BoxReference] = [
        BoxReference(app_id=0, name=votes_box_name(proposal_id))
    ]
    for member in council_members:
        refs.append(
            BoxReference(app_id=0, name=members_box_name(member.account.address))
        )

    approvals = 0
    for i in range(len(council_members)):
        member = council_members[i]

        if approvals >= half_plus_one:
            break

        if (i % 3) == 0:
            block = True
        else:
            block = False
            approvals += 1

        composer = council_client.new_group()

        composer.vote(
            args=VoteArgs(
                proposal_id=proposal_id,
                block=block,
            ),
            params=CommonAppCallParams(
                sender=member.account.address,
                signer=member.account.signer,
                static_fee=min_fee_times_3,
            ),
        )

        for i in range(5, len(refs), 8):
            composer.op_up(
                params=CommonAppCallParams(
                    box_references=refs[i : i + 8],
                )
            )

        composer.send()

    global_state = approved_proposal_client.state.global_state.get_all()

    assert global_state.get("status") == STATUS_REVIEWED


def test_vote_proposal_invalid_state(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    council_members: list[CommitteeMember],
    voting_proposal_client: ProposalClient,
    council_client: CouncilClient,
) -> None:

    proposal_id = voting_proposal_client.app_id
    member = council_members[0]
    composer = council_client.new_group()

    composer.vote(
        args=VoteArgs(
            proposal_id=proposal_id,
            block=False,
        ),
        params=CommonAppCallParams(
            sender=member.account.address,
            signer=member.account.signer,
            static_fee=min_fee_times_3,
        ),
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]):
        composer.send()


def test_vote_not_member(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient
) -> None:

    proposal_id = approved_proposal_client.app_id

    composer = council_client.new_group()

    composer.vote(
        args=VoteArgs(
            proposal_id=proposal_id,
            block=False,
        ),
        params=CommonAppCallParams(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            static_fee=min_fee_times_3,
        ),
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTER_NOT_FOUND]):
        composer.send()


def test_vote_not_a_proposal(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    no_role_account: SigningAccount,
    council_client: CouncilClient
) -> None:

    # should fail because this uses the mock registry app id
    registry_app_id = council_client.state.global_state.registry_app_id

    composer = council_client.new_group()

    composer.vote(
        args=VoteArgs(
            proposal_id=registry_app_id,
            block=False,
        ),
        params=CommonAppCallParams(
            sender=no_role_account.address,
            signer=no_role_account.signer,
            static_fee=min_fee_times_3,
        ),
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTER_NOT_FOUND]):
        composer.send()
