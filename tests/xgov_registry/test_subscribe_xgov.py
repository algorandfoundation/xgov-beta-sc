import pytest
from algokit_utils import SigningAccount, AlgorandClient, PaymentParams, AlgoAmount, CommonAppCallParams, LogicError

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    XGovRegistryClient, SubscribeXgovArgs, GetXgovBoxArgs,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import SubscribeXgovArgs as AppSubscribeXgovArgs
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import get_xgov_fee


def test_subscribe_xgov_success(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    initial_amount = algorand_client.account.get_information(xgov_registry_client.app_address).amount.micro_algo

    xgov_fee = get_xgov_fee(xgov_registry_client)
    xgov_registry_client.send.subscribe_xgov(
        args=SubscribeXgovArgs(
            voting_address=no_role_account.address,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=xgov_fee,
                )
            )
        ),
        params=CommonAppCallParams(sender=no_role_account.address)
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs
    final_amount = algorand_client.account.get_information(xgov_registry_client.app_address).amount.micro_algo

    assert final_amount == initial_amount + xgov_fee.micro_algo
    assert final_xgovs == initial_xgovs + 1

    xgov_box = xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(xgov_address=no_role_account.address),
    ).abi_return

    assert no_role_account.address == xgov_box.voting_address


def test_app_subscribe_xgov_success(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    min_fee_times_3: AlgoAmount,
    xgov_subscriber_app: XGovSubscriberAppMockClient,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    initial_amount = algorand_client.account.get_information(xgov_registry_client.app_address).amount.micro_algo
    xgov_subscriber_app.send.subscribe_xgov(
        args=AppSubscribeXgovArgs(
            app_id=xgov_registry_client.app_id,
            voting_address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            static_fee=min_fee_times_3,
            app_references=[xgov_registry_client.app_id]  #FIXME: This should have been autopopulated
        )
    )
    final_xgovs = xgov_registry_client.state.global_state.xgovs
    final_amount = algorand_client.account.get_information(xgov_registry_client.app_address).amount.micro_algo

    assert final_amount == initial_amount + get_xgov_fee(xgov_registry_client).micro_algo
    assert final_xgovs == initial_xgovs + 1

    xgov_box = xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(xgov_address=xgov_subscriber_app.app_address),
    ).abi_return

    assert no_role_account.address == xgov_box.voting_address


def test_subscribe_xgov_already_xgov(
    algorand_client: AlgorandClient,
    xgov: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.ALREADY_XGOV):
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                voting_address=xgov.address,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=xgov.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                )
            ),
            params=CommonAppCallParams(sender=xgov.address)
        )


def test_subscribe_xgov_wrong_recipient(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PAYMENT):
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                voting_address=no_role_account.address,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=no_role_account.address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_subscribe_xgov_wrong_amount(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PAYMENT):
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                voting_address=no_role_account.address,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=AlgoAmount(micro_algo=get_xgov_fee(xgov_registry_client).micro_algo - 1),
                    )
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address)
        )


def test_subscribe_xgov_paused_registry_error(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    xgov_registry_client.send.pause_registry()
    xgov_fee = get_xgov_fee(xgov_registry_client)
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                voting_address=no_role_account.address,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=no_role_account.address,
                        receiver=xgov_registry_client.app_address,
                        amount=xgov_fee,
                    )
                )
            ),
            params=CommonAppCallParams(sender=no_role_account.address)
        )

    xgov_registry_client.send.resume_registry()
    xgov_registry_client.send.subscribe_xgov(
        args=SubscribeXgovArgs(
            voting_address=no_role_account.address,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=no_role_account.address,
                    receiver=xgov_registry_client.app_address,
                    amount=xgov_fee
                )
            )
        ),
        params=CommonAppCallParams(sender=no_role_account.address)
    )
