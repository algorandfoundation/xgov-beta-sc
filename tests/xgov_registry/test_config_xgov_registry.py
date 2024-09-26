import pytest

from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams

from smart_contracts.artifacts.xgov_registry.client import (
    XGovRegistryClient,
    XGovRegistryConfig
)

from algosdk.encoding import decode_address
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import (
    assert_registry_config,
    logic_error_type
)

def test_config_xgov_registry_success(
    xgov_registry_client: XGovRegistryClient,
    deployer: AddressAndSigner,
    xgov_registry_config: XGovRegistryConfig
) -> None:
    # Call the config_xgov_registry method
    xgov_registry_client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    # Fetch the updated global state
    global_state = xgov_registry_client.get_global_state()

    assert_registry_config(
        global_state=global_state,
        xgov_min_balance=xgov_registry_config.xgov_min_balance,
        proposal_publishing_bps=xgov_registry_config.proposal_publishing_bps,
        proposal_commitment_bps=xgov_registry_config.proposal_commitment_bps,
        proposer_fee=xgov_registry_config.proposer_fee,
        proposal_fee=xgov_registry_config.proposal_fee,
        max_requested_amount_small=xgov_registry_config.max_requested_amount[0],
        max_requested_amount_medium=xgov_registry_config.max_requested_amount[1],
        max_requested_amount_large=xgov_registry_config.max_requested_amount[2],
        discussion_duration_small=xgov_registry_config.discussion_duration[0],
        discussion_duration_medium=xgov_registry_config.discussion_duration[1],
        discussion_duration_large=xgov_registry_config.discussion_duration[2],
        discussion_duration_xlarge=xgov_registry_config.discussion_duration[3],
        voting_duration_small=xgov_registry_config.voting_duration[0],
        voting_duration_medium=xgov_registry_config.voting_duration[1],
        voting_duration_large=xgov_registry_config.voting_duration[2],
        voting_duration_xlarge=xgov_registry_config.voting_duration[3],
        cool_down_duration=xgov_registry_config.cool_down_duration,
        quorum_small=xgov_registry_config.quorum[0],
        quorum_medium=xgov_registry_config.quorum[1],
        quorum_large=xgov_registry_config.quorum[2],
        weighted_quorum_small=xgov_registry_config.weighted_quorum[0],
        weighted_quorum_medium=xgov_registry_config.weighted_quorum[1],
        weighted_quorum_large=xgov_registry_config.weighted_quorum[2],
    )

def test_config_xgov_registry_not_manager(
    xgov_registry_client: XGovRegistryClient,
    random_account: AddressAndSigner,
    xgov_registry_config: XGovRegistryConfig
) -> None:
    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.config_xgov_registry(
            config=xgov_registry_config,
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
            ),
        )

def test_config_xgov_registry_pending_proposals(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
    xgov_registry_config: XGovRegistryConfig
) -> None:
    global_state = xgov_registry_client.get_global_state()
    
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.subscribe_proposer(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposer_fee
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))]
        ),
    )

    xgov_registry_client.set_kyc_provider(
        provider=deployer.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))]
        ),
    )

    # set pending proposals > 0
    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.proposal_fee
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))]
        ),
    )

    global_state = xgov_registry_client.get_global_state()
    print(global_state.pending_proposals)

    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.config_xgov_registry(
            config=xgov_registry_config,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
            ),
        )