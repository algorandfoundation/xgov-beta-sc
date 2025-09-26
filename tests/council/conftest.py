import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    CreateTransactionParameters,
    EnsureBalanceParameters,
    SigningAccount,
    TransactionParameters,
    ensure_funded,
)
from algokit_utils.config import config

from smart_contracts.artifacts.council.council_client import (
    AddMemberArgs,
    CouncilClient,
    CouncilFactory,
    CreateArgs,
)
from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    SetXgovCouncilArgs,
    XGovRegistryClient,
)
from tests.common import INITIAL_FUNDS, CommitteeMember
from tests.council.common import members_box_name
from tests.xgov_registry.conftest import (
    approved_proposal_client,
    draft_proposal_client,
    proposal_client,
    proposer,
    proposer_no_kyc,
    voting_proposal_client,
    xgov_registry_client,
    xgov_registry_client_committee_not_declared,
    xgov_registry_config,
    xgov_registry_config_dict,
)


@pytest.fixture(scope="function")
def council_client(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
) -> CouncilClient:
    config.configure(
        debug=False,
        populate_app_call_resources=True,
    )

    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=deployer,
        min_spending_balance=INITIAL_FUNDS,
    )

    factory = algorand_client.client.get_typed_app_factory(
        typed_factory=CouncilFactory,
        default_sender=deployer.address,
    )

    client, _ = factory.send.create.create(
        args=CreateArgs(
            admin=deployer.address,
            registry_id=xgov_registry_client.app_id,
        )
    )
    algorand_client.account.ensure_funded_from_environment(
        account_to_fund=client.app_address,
        min_spending_balance=INITIAL_FUNDS,
    )

    # set the xgov council
    xgov_registry_client.send.set_xgov_council(
        args=SetXgovCouncilArgs(
            council=client.app_address,
        ),
        params=CommonAppCallParams(sender=deployer.address, signer=deployer.signer),
    )

    return client


@pytest.fixture(scope="function")
def council_members(
    deployer: SigningAccount,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
) -> list[CommitteeMember]:
    for member in committee:
        council_client.send.add_member(
            args=AddMemberArgs(
                address=member.account.address,
            ),
            params=CommonAppCallParams(
                sender=deployer.address,
                signer=deployer.signer,
            ),
        )

    return committee


@pytest.fixture(scope="function")
def proposal_client_for_council(
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    council_client: CouncilClient,  # Ensure council is set up first
    algorand_client: AlgorandClient,
) -> ProposalClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    proposal_app_id = xgov_registry_client.create_empty_proposal(
        proposer=proposer.address,
        transaction_parameters=TransactionParameters(
            suggested_params=sp,
        ),
    )

    client = ProposalClient(
        algorand_client.client.algod,
        app_id=proposal_app_id.return_value,
    )

    return client
