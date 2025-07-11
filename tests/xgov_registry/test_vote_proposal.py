import base64

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk import abi
from algosdk.transaction import SuggestedParams

from smart_contracts.artifacts.proposal.proposal_client import (
    ProposalClient,
)
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.common import get_voter_box_key
from tests.xgov_registry.common import (
    COMMITTEE_VOTES,
    LogicErrorType,
    xgov_box_name,
)


def test_vote_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    voting_proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    xgov_registry_client.vote_proposal(
        proposal_id=voting_proposal_client.app_id,
        xgov_address=committee_members[0].address,
        approval_votes=10,
        rejection_votes=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            suggested_params=sp,
            boxes=[
                (0, xgov_box_name(committee_members[0].address)),
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                ),
            ],
            foreign_apps=[voting_proposal_client.app_id],
            accounts=[committee_members[0].address],
        ),
    )

    box_info = xgov_registry_client.algod_client.application_box_by_name(
        application_id=xgov_registry_client.app_id,
        box_name=xgov_box_name(committee_members[0].address),
    )

    box_value = base64.b64decode(box_info["value"])  # type: ignore
    box_abi = abi.ABIType.from_string("(address,uint64,uint64)")
    _, voted_proposals, last_vote_timestamp = box_abi.decode(box_value)  # type: ignore

    assert voted_proposals == 1  # type: ignore
    assert last_vote_timestamp > 0  # type: ignore


def test_vote_proposal_not_in_voting_phase(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    proposal_client: ProposalClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.PROPOSAL_IS_NOT_VOTING):
        xgov_registry_client.vote_proposal(
            proposal_id=proposal_client.app_id,
            xgov_address=xgov.address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=xgov.address,
                signer=xgov.signer,
                suggested_params=sp,
                boxes=[
                    (0, xgov_box_name(xgov.address)),
                    (
                        proposal_client.app_id,
                        get_voter_box_key(xgov.address),
                    ),
                ],
                foreign_apps=[proposal_client.app_id],
                accounts=[xgov.address],
            ),
        )


def test_vote_proposal_not_a_proposal_app(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.INVALID_PROPOSAL):
        xgov_registry_client.vote_proposal(
            proposal_id=xgov_registry_client.app_id,
            xgov_address=committee_members[0].address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                suggested_params=sp,
                boxes=[
                    (0, xgov_box_name(committee_members[0].address)),
                    (
                        xgov_registry_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    ),
                ],
                foreign_apps=[xgov_registry_client.app_id],
                accounts=[proposer.address],
            ),
        )


def test_vote_proposal_not_an_xgov(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
    voting_proposal_client: ProposalClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.vote_proposal(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=random_account.address,
            approval_votes=COMMITTEE_VOTES,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(random_account.address))],
                foreign_apps=[voting_proposal_client.app_id],
                accounts=[random_account.address],
            ),
        )


def test_vote_proposal_wrong_voting_address(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    xgov: AddressAndSigner,
    random_account: AddressAndSigner,
    voting_proposal_client: ProposalClient,
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    with pytest.raises(LogicErrorType, match=err.MUST_BE_VOTING_ADDRESS):
        xgov_registry_client.vote_proposal(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=xgov.address,
            approval_votes=0,
            rejection_votes=COMMITTEE_VOTES,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, xgov_box_name(xgov.address))],
                foreign_apps=[voting_proposal_client.app_id],
                accounts=[xgov.address],
            ),
        )


def test_vote_proposal_paused_registry_error(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    voting_proposal_client: ProposalClient,
    committee_members: list[AddressAndSigner],
    sp_min_fee_times_2: SuggestedParams,
) -> None:
    sp = sp_min_fee_times_2

    xgov_registry_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.vote_proposal(
            proposal_id=voting_proposal_client.app_id,
            xgov_address=committee_members[0].address,
            approval_votes=10,
            rejection_votes=0,
            transaction_parameters=TransactionParameters(
                sender=committee_members[0].address,
                signer=committee_members[0].signer,
                suggested_params=sp,
                boxes=[
                    (0, xgov_box_name(committee_members[0].address)),
                    (
                        voting_proposal_client.app_id,
                        get_voter_box_key(committee_members[0].address),
                    ),
                ],
                foreign_apps=[voting_proposal_client.app_id],
                accounts=[committee_members[0].address],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.vote_proposal(
        proposal_id=voting_proposal_client.app_id,
        xgov_address=committee_members[0].address,
        approval_votes=10,
        rejection_votes=0,
        transaction_parameters=TransactionParameters(
            sender=committee_members[0].address,
            signer=committee_members[0].signer,
            suggested_params=sp,
            boxes=[
                (0, xgov_box_name(committee_members[0].address)),
                (
                    voting_proposal_client.app_id,
                    get_voter_box_key(committee_members[0].address),
                ),
            ],
            foreign_apps=[voting_proposal_client.app_id],
            accounts=[committee_members[0].address],
        ),
    )
