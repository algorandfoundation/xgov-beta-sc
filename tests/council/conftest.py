import pytest
from algokit_utils import (
    CreateTransactionParameters,
    EnsureBalanceParameters,
    TransactionParameters,
    ensure_funded,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.config import config
from algokit_utils.models import Account

from smart_contracts.artifacts.council.council_client import CouncilClient
from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
)
from tests.conftest import no_role_account
from tests.council.common import members_box_name
from tests.proposal.common import (
    INITIAL_FUNDS,
)
from tests.xgov_registry.conftest import (
    approved_proposal_client,
    draft_proposal_client,
    proposal_client,
    proposer,
    voting_proposal_client,
    xgov_registry_client,
    xgov_registry_client_committee_not_declared,
    xgov_registry_config,
)


@pytest.fixture(scope="function")
def council_client(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
) -> CouncilClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    client = CouncilClient(
        algorand_client.client.algod,
        sender=deployer.address,
        creator=deployer,
        indexer_client=algorand_client.client.indexer,
    )

    client.create_create(
        admin=deployer.address,
        registry_id=xgov_registry_client.app_id,
        transaction_parameters=CreateTransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    ensure_funded(
        algorand_client.client.algod,
        EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=INITIAL_FUNDS,
        ),
    )

    # set the xgov council
    xgov_registry_client.set_xgov_council(
        council=client.app_address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address, signer=deployer.signer, suggested_params=sp
        ),
    )

    return client


@pytest.fixture(scope="function")
def council_members(
    deployer: Account,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
    committee_members: list[AddressAndSigner],
) -> list[AddressAndSigner]:

    sp = algorand_client.get_suggested_params()

    for member in committee_members:
        council_client.add_member(
            address=member.address,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[
                    (0, members_box_name(member.address)),
                ],
            ),
        )

    return committee_members


@pytest.fixture(scope="function")
def proposal_client_for_council(
    proposer: AddressAndSigner,
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
