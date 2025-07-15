import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.council.council_client import CouncilClient
from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.enums import STATUS_BLOCKED, STATUS_REVIEWED
from tests.common import logic_error_type
from tests.council.common import members_box_name, votes_box_name
from tests.utils import ERROR_TO_REGEX


def test_vote_approve_success(
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient,
    council_members: list[AddressAndSigner],
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_id = approved_proposal_client.app_id
    half_plus_one = (len(council_members) // 2) + 1

    refs = [(0, votes_box_name(proposal_id))]
    for member in council_members[:half_plus_one]:
        refs.append((0, members_box_name(member.address)))

    for member in council_members[:half_plus_one]:
        composer = council_client.compose()

        composer.vote(
            proposal_id=proposal_id,
            block=False,
            transaction_parameters=TransactionParameters(
                sender=member.address,
                signer=member.signer,
                boxes=refs[:5],
                foreign_apps=[
                    council_client.get_global_state().registry_app_id,
                    proposal_id,
                ],
                suggested_params=sp,
            ),
        )

        for i in range(5, len(refs), 8):
            composer.op_up(
                transaction_parameters=TransactionParameters(
                    boxes=refs[i : i + 8],
                )
            )

        composer.execute()

    global_state = approved_proposal_client.get_global_state()

    assert global_state.status == STATUS_REVIEWED


def test_vote_reject_success(
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient,
    council_members: list[AddressAndSigner],
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    # blocking a proposal transfers the proposal escrow lock up back to the proposer
    sp.min_fee *= 3  # type: ignore

    proposal_id = approved_proposal_client.app_id
    half_plus_one = (len(council_members) // 2) + 1

    refs = [(0, votes_box_name(proposal_id))]
    for member in council_members[:half_plus_one]:
        refs.append((0, members_box_name(member.address)))

    for member in council_members[:half_plus_one]:
        composer = council_client.compose()

        composer.vote(
            proposal_id=proposal_id,
            block=True,
            transaction_parameters=TransactionParameters(
                sender=member.address,
                signer=member.signer,
                boxes=refs[:5],
                foreign_apps=[
                    council_client.get_global_state().registry_app_id,
                    proposal_id,
                ],
                suggested_params=sp,
            ),
        )

        for i in range(5, len(refs), 8):
            composer.op_up(
                transaction_parameters=TransactionParameters(
                    boxes=refs[i : i + 8],
                )
            )

        composer.execute()

    global_state = approved_proposal_client.get_global_state()

    assert global_state.status == STATUS_BLOCKED


def test_vote_mix_success(
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient,
    council_members: list[AddressAndSigner],
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_id = approved_proposal_client.app_id
    half_plus_one = (len(council_members) // 2) + 1

    refs = [(0, votes_box_name(proposal_id))]
    for member in council_members:
        refs.append((0, members_box_name(member.address)))

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

        composer = council_client.compose()

        composer.vote(
            proposal_id=proposal_id,
            block=block,
            transaction_parameters=TransactionParameters(
                sender=member.address,
                signer=member.signer,
                boxes=refs[:5],
                foreign_apps=[
                    council_client.get_global_state().registry_app_id,
                    proposal_id,
                ],
                suggested_params=sp,
            ),
        )

        for i in range(5, len(refs), 8):
            composer.op_up(
                transaction_parameters=TransactionParameters(
                    boxes=refs[i : i + 8],
                )
            )

        composer.execute()

    global_state = approved_proposal_client.get_global_state()

    assert global_state.status == STATUS_REVIEWED


def test_vote_proposal_invalid_state(
    voting_proposal_client: ProposalClient,
    council_client: CouncilClient,
    council_members: list[AddressAndSigner],
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_id = voting_proposal_client.app_id
    member = council_members[0]
    composer = council_client.compose()

    composer.vote(
        proposal_id=proposal_id,
        block=False,
        transaction_parameters=TransactionParameters(
            sender=member.address,
            signer=member.signer,
            boxes=[
                (0, votes_box_name(proposal_id)),
                (0, members_box_name(member.address)),
            ],
            foreign_apps=[
                council_client.get_global_state().registry_app_id,
                proposal_id,
            ],
            suggested_params=sp,
        ),
    )

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer.execute()


def test_vote_not_member(
    approved_proposal_client: ProposalClient,
    council_client: CouncilClient,
    random_account: AddressAndSigner,
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    proposal_id = approved_proposal_client.app_id

    composer = council_client.compose()

    composer.vote(
        proposal_id=proposal_id,
        block=False,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            boxes=[
                (0, votes_box_name(proposal_id)),
                (0, members_box_name(random_account.address)),
            ],
            foreign_apps=[
                council_client.get_global_state().registry_app_id,
                proposal_id,
            ],
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.NOT_A_MEMBER]):
        composer.execute()


def test_vote_not_a_proposal(
    council_client: CouncilClient,
    random_account: AddressAndSigner,
    algorand_client: AlgorandClient,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    # should fail because this uses the mock registry app id
    registry_app_id = council_client.get_global_state().registry_app_id

    composer = council_client.compose()

    composer.vote(
        proposal_id=registry_app_id,
        block=False,
        transaction_parameters=TransactionParameters(
            sender=random_account.address,
            signer=random_account.signer,
            boxes=[
                (0, votes_box_name(registry_app_id)),
                (0, members_box_name(random_account.address)),
            ],
            foreign_apps=[registry_app_id],
            suggested_params=sp,
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.NOT_A_MEMBER]):
        composer.execute()
