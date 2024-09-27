import pytest

from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams

from smart_contracts.artifacts.xgov_registry.client import XGovRegistryClient

from algosdk.encoding import decode_address
from algosdk.atomic_transaction_composer import TransactionWithSigner

from smart_contracts.errors import std_errors as err
from smart_contracts.proposal import enums as enm
from tests.xgov_registry.common import logic_error_type

from smart_contracts.artifacts.proposal_mock.client import ProposalMockClient

def test_pay_grant_proposal_success(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=10_000_001
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

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

    open_proposal_response = xgov_registry_client.open_proposal(
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

    # finalize
    proposal_mock_app_id = open_proposal_response.return_value
    
    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # payout
    xgov_registry_client.pay_grant_proposal(
        proposal_id=proposal_mock_app_id,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))],
            foreign_apps=[(proposal_mock_app_id)],
            accounts=[(proposer.address)]
        ),
    )

def test_pay_grant_proposal_not_payor(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=10_000_001
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

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

    open_proposal_response = xgov_registry_client.open_proposal(
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

    # finalize
    proposal_mock_app_id = open_proposal_response.return_value
    
    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # payout
    with pytest.raises(logic_error_type, match=err.UNAUTHORIZED):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_app_id,
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_not_a_proposal_app(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore
    # payout
    with pytest.raises(logic_error_type, match=err.INVALID_PROPOSAL):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=100,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_not_approved(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=10_000_001
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

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

    open_proposal_response = xgov_registry_client.open_proposal(
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

    # finalize
    proposal_mock_app_id = open_proposal_response.return_value
    
    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_DRAFT,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # payout
    with pytest.raises(logic_error_type, match=err.PROPOSAL_IS_NOT_APPROVED):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_invalid_kyc(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=10_000_001
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

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

    open_proposal_response = xgov_registry_client.open_proposal(
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

    # finalize
    proposal_mock_app_id = open_proposal_response.return_value
    
    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=False,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))],
        ),
    )

    # payout
    with pytest.raises(logic_error_type, match=err.INVALID_KYC):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_expired_kyc(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
) -> None:
    global_state = xgov_registry_client.get_global_state()
    
    sp = algorand_client.get_suggested_params()
    sp.min_fee *= 2  # type: ignore

    xgov_registry_client.deposit_funds(
        payment=TransactionWithSigner(
            txn=algorand_client.transactions.payment(
                PayParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=10_000_001
                ),
            ),
            signer=deployer.signer,
        ),
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
        ),
    )

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

    open_proposal_response = xgov_registry_client.open_proposal(
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

    # finalize
    proposal_mock_app_id = open_proposal_response.return_value
    
    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    xgov_registry_client.set_proposer_kyc(
        proposer=proposer.address,
        kyc_status=True,
        kyc_expiring=321321,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[(0, b"p" + decode_address(proposer.address))],
        ),
    )

    # payout
    with pytest.raises(logic_error_type, match=err.EXPIRED_KYC):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_app_id)],
                accounts=[(proposer.address)]
            ),
        )

def test_pay_grant_proposal_insufficient_funds(
    xgov_registry_client: XGovRegistryClient,
    algorand_client: AlgorandClient,
    deployer: AddressAndSigner,
    proposer: AddressAndSigner,
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

    open_proposal_response = xgov_registry_client.open_proposal(
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

    # finalize
    proposal_mock_app_id = open_proposal_response.return_value
    
    proposal_mock_client = ProposalMockClient(
        algorand_client.client.algod,
        app_id=proposal_mock_app_id,
    )

    proposal_mock_client.set_requested_amount(
        requested_amount=10_000_000,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # approve
    proposal_mock_client.set_status(
        status=enm.STATUS_APPROVED,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            suggested_params=sp,
        ),
    )

    # payout
    with pytest.raises(logic_error_type, match=err.INSUFFICIENT_TREASURY_FUNDS):
        xgov_registry_client.pay_grant_proposal(
            proposal_id=proposal_mock_app_id,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[(0, b"p" + decode_address(proposer.address))],
                foreign_apps=[(proposal_mock_app_id)],
                accounts=[(proposer.address)]
            ),
        )