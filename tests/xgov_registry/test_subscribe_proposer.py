import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    PaymentParams,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    GetProposerBoxArgs,
    SubscribeProposerArgs,
    XGovRegistryClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import get_proposer_fee


def test_subscribe_proposer_success(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_amount = algorand_client.account.get_information(
        xgov_registry_client.app_address,
    ).amount.micro_algo

    proposer_fee = get_proposer_fee(xgov_registry_client)
    xgov_registry_client.send.subscribe_proposer(
        args=SubscribeProposerArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=proposer_fee,
                )
            )
        ),
        params=CommonAppCallParams(sender=no_role_account.address),
    )

    final_amount: int = algorand_client.account.get_information(
        xgov_registry_client.app_address,
    ).amount.micro_algo

    assert final_amount == initial_amount + proposer_fee.micro_algo

    proposer_box = xgov_registry_client.send.get_proposer_box(
        args=GetProposerBoxArgs(proposer_address=no_role_account.address)
    ).abi_return

    assert not proposer_box.active_proposal  # type: ignore
    assert not proposer_box.kyc_status  # type: ignore
    assert proposer_box.kyc_expiring == 0  # type: ignore


def test_subscribe_proposer_already_proposer(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.ALREADY_PROPOSER):
        xgov_registry_client.send.subscribe_proposer(
            args=SubscribeProposerArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=proposer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_proposer_fee(xgov_registry_client),
                    )
                )
            ),
            params=CommonAppCallParams(sender=proposer.address),
        )


def test_subscribe_proposer_wrong_recipient(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_RECEIVER):
        xgov_registry_client.send.subscribe_proposer(
            args=SubscribeProposerArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=no_role_account.address,
                        amount=get_proposer_fee(xgov_registry_client),
                    )
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_subscribe_proposer_wrong_amount(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.WRONG_PAYMENT_AMOUNT):
        xgov_registry_client.send.subscribe_proposer(
            args=SubscribeProposerArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=AlgoAmount(
                            micro_algo=get_proposer_fee(xgov_registry_client).micro_algo
                            - 1
                        ),
                    )
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )


def test_subscribe_proposer_paused_registry_error(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.pause_registry()
    proposer_fee = get_proposer_fee(xgov_registry_client)
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.subscribe_proposer(
            args=SubscribeProposerArgs(
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=proposer_fee,
                    )
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address),
        )

    xgov_registry_client.send.resume_registry()

    xgov_registry_client.send.subscribe_proposer(
        args=SubscribeProposerArgs(
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=proposer_fee,
                )
            )
        ),
        params=CommonAppCallParams(sender=no_role_account.address),
    )
