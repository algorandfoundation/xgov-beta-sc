import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.models import Account
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient,
    XGovRegistryConfig,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import LogicErrorType, proposer_box_name


def test_open_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    xgov_registry_config: XGovRegistryConfig,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    # Call the config_xgov_registry method
    xgov_registry_client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert after_global_state.pending_proposals == (global_state.pending_proposals + 1)


def test_open_proposal_not_a_proposer(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    random_account: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 3  # type: ignore

    with pytest.raises(LogicErrorType, match=err.UNAUTHORIZED):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=random_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=random_account.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=random_account.address,
                signer=random_account.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(random_account.address))],
            ),
        )


def test_open_proposal_active_proposal(
    xgov_registry_client: XGovRegistryClient,
    xgov_registry_config: XGovRegistryConfig,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.ALREADY_ACTIVE_PROPOSAL):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_wrong_fee(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    with pytest.raises(LogicErrorType, match=err.INSUFFICIENT_FEE):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_wrong_amount(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    with pytest.raises(LogicErrorType, match=err.WRONG_PAYMENT_AMOUNT):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=1_000,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_wrong_recipient(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    sp.min_fee *= 3  # type: ignore

    with pytest.raises(LogicErrorType, match=err.WRONG_RECEIVER):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=proposer.address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )


def test_open_proposal_paused_registry_error(
    xgov_registry_client: XGovRegistryClient,
    xgov_registry_config: XGovRegistryConfig,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    # Call the config_xgov_registry method
    xgov_registry_client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    xgov_registry_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )

    xgov_registry_client.resume_registry()

    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert after_global_state.pending_proposals == (global_state.pending_proposals + 1)


def test_open_proposal_paused_proposal_error(
    xgov_registry_client: XGovRegistryClient,
    xgov_registry_config: XGovRegistryConfig,
    algorand_client: AlgorandClient,
    deployer: Account,
    proposer: AddressAndSigner,
) -> None:

    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    # Call the config_xgov_registry method
    xgov_registry_client.config_xgov_registry(
        config=xgov_registry_config,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    global_state = xgov_registry_client.get_global_state()

    sp.min_fee *= 3  # type: ignore

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=18446744073709551615,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    xgov_registry_client.pause_proposals()

    with pytest.raises(LogicErrorType, match=err.PAUSED_PROPOSALS):
        xgov_registry_client.open_proposal(
            payment=TransactionWithSigner(
                txn=algorand_client.transactions.payment(
                    PayParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=global_state.open_proposal_fee,
                    ),
                ),
                signer=proposer.signer,
            ),
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, proposer_box_name(proposer.address))],
            ),
        )

    xgov_registry_client.resume_proposals()

    xgov_registry_client.open_proposal(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=proposer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=global_state.open_proposal_fee,
                ),
            ),
            signer=proposer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
            boxes=[(0, proposer_box_name(proposer.address))],
        ),
    )

    after_global_state = xgov_registry_client.get_global_state()

    assert after_global_state.pending_proposals == (global_state.pending_proposals + 1)
