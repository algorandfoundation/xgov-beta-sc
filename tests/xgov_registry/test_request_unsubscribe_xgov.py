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
    GetRequestUnsubscribeBoxArgs,
    GetXgovBoxArgs,
    RequestUnsubscribeXgovArgs,
    SetVotingAccountArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from smart_contracts.errors import std_errors as err
from tests.xgov_registry.common import get_xgov_fee


def test_request_unsubscribe_xgov_success(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
) -> None:
    initial_request_unsubscribe_id = (
        xgov_registry_client.state.global_state.request_unsubscribe_id
    )
    xgov_address = app_xgov_managed_subscription.app_address
    owner_address = deployer.address
    relation_type = 0
    xgov_registry_client.send.request_unsubscribe_xgov(
        args=RequestUnsubscribeXgovArgs(
            xgov_address=xgov_address,
            owner_address=owner_address,
            relation_type=relation_type,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=owner_address,
                    receiver=xgov_registry_client.app_address,
                    amount=get_xgov_fee(xgov_registry_client),
                )
            ),
        )
    )
    final_request_unsubscribe_id = (
        xgov_registry_client.state.global_state.request_unsubscribe_id
    )
    assert final_request_unsubscribe_id == initial_request_unsubscribe_id + 1

    request_unsubscribe_box = xgov_registry_client.send.get_request_unsubscribe_box(
        args=GetRequestUnsubscribeBoxArgs(
            request_unsubscribe_id=initial_request_unsubscribe_id
        )
    ).abi_return

    assert request_unsubscribe_box.owner_addr == owner_address
    assert request_unsubscribe_box.xgov_addr == xgov_address
    assert request_unsubscribe_box.relation_type == relation_type


def test_request_unsubscribe_unauthorized(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        xgov_registry_client.send.request_unsubscribe_xgov(
            args=RequestUnsubscribeXgovArgs(
                xgov_address=app_xgov_managed_subscription.app_address,
                owner_address=no_role_account.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                ),
            )
        )


def test_request_unsubscribe_xgov_not_xgov(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    no_role_account: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
) -> None:
    with pytest.raises(LogicError, match=err.NOT_XGOV):
        xgov_registry_client.send.request_unsubscribe_xgov(
            args=RequestUnsubscribeXgovArgs(
                xgov_address=no_role_account.address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                ),
            ),
        )


def test_request_unsubscribe_xgov_wrong_recipient(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PAYMENT):
        xgov_registry_client.send.request_unsubscribe_xgov(
            args=RequestUnsubscribeXgovArgs(
                xgov_address=app_xgov_managed_subscription.app_address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=deployer.address,
                        amount=get_xgov_fee(xgov_registry_client),
                    )
                ),
            ),
        )


def test_request_unsubscribe_xgov_wrong_amount(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
) -> None:
    with pytest.raises(LogicError, match=err.INVALID_PAYMENT):
        xgov_registry_client.send.request_unsubscribe_xgov(
            args=RequestUnsubscribeXgovArgs(
                xgov_address=app_xgov_managed_subscription.app_address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=AlgoAmount(
                            micro_algo=get_xgov_fee(xgov_registry_client).micro_algo - 1
                        ),
                    )
                ),
            ),
        )


def test_request_unsubscribe_xgov_paused_registry_error(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
) -> None:
    xgov_fee = get_xgov_fee(xgov_registry_client)
    xgov_registry_client.send.pause_registry()
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        xgov_registry_client.send.request_unsubscribe_xgov(
            args=RequestUnsubscribeXgovArgs(
                xgov_address=app_xgov_managed_subscription.app_address,
                owner_address=deployer.address,
                relation_type=0,
                payment=algorand_client.create_transaction.payment(
                    PaymentParams(
                        sender=deployer.address,
                        receiver=xgov_registry_client.app_address,
                        amount=xgov_fee,
                    )
                ),
            ),
        )

    xgov_registry_client.send.resume_registry()
    xgov_registry_client.send.request_unsubscribe_xgov(
        args=RequestUnsubscribeXgovArgs(
            xgov_address=app_xgov_managed_subscription.app_address,
            owner_address=deployer.address,
            relation_type=0,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=xgov_fee,
                )
            ),
        )
    )


def test_request_unsubscribe_xgov_locked(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_managed_subscription: XGovSubscriberAppMockClient,
) -> None:

    # Lock voting address
    xgov_box = xgov_registry_client.send.get_xgov_box(
        args=GetXgovBoxArgs(xgov_address=app_xgov_managed_subscription.app_address)
    ).abi_return
    xgov_registry_client.send.set_voting_account(
        args=SetVotingAccountArgs(
            xgov_address=app_xgov_managed_subscription.app_address,
            voting_address=app_xgov_managed_subscription.app_address,
        ),
        params=CommonAppCallParams(sender=xgov_box.voting_address),
    )

    # Request managed unsubscription via owner
    initial_request_unsubscribe_id = (
        xgov_registry_client.state.global_state.request_unsubscribe_id
    )
    xgov_registry_client.send.request_unsubscribe_xgov(
        args=RequestUnsubscribeXgovArgs(
            xgov_address=app_xgov_managed_subscription.app_address,
            owner_address=deployer.address,
            relation_type=0,
            payment=algorand_client.create_transaction.payment(
                PaymentParams(
                    sender=deployer.address,
                    receiver=xgov_registry_client.app_address,
                    amount=get_xgov_fee(xgov_registry_client),
                )
            ),
        )
    )
    final_request_unsubscribe_id = (
        xgov_registry_client.state.global_state.request_unsubscribe_id
    )
    assert final_request_unsubscribe_id == initial_request_unsubscribe_id + 1
