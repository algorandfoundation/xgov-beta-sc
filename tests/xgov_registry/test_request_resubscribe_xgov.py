from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    PaymentParams,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ApproveUnsubscribeXgovArgs,
    RequestSubscribeXgovArgs,
    XGovRegistryClient,
)
from smart_contracts.artifacts.xgov_subscriber_app_mock.x_gov_subscriber_app_mock_client import (
    XGovSubscriberAppMockClient,
)
from tests.xgov_registry.common import get_xgov_fee


def test_request_resubscribe_xgov_success(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    xgov_subscriber: SigningAccount,
    xgov_registry_client: XGovRegistryClient,
    app_xgov_unsubscribe_requested: XGovSubscriberAppMockClient,
) -> None:
    # Approve unsubscribe
    initial_xgovs = xgov_registry_client.state.global_state.xgovs
    xgov_registry_client.send.approve_unsubscribe_xgov(
        args=ApproveUnsubscribeXgovArgs(
            request_id=xgov_registry_client.state.global_state.request_id - 1
        ),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    xgovs = xgov_registry_client.state.global_state.xgovs
    assert xgovs == initial_xgovs - 1
    assert (
        xgov_registry_client.state.box.xgov_box.get_value(
            app_xgov_unsubscribe_requested.app_address
        ).unsubscribed_round
        > 0
    )

    # Request new subscription
    initial_request_id = xgov_registry_client.state.global_state.request_id
    rid = xgov_registry_client.send.request_subscribe_xgov(
        args=RequestSubscribeXgovArgs(
            xgov_address=app_xgov_unsubscribe_requested.app_address,
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
    ).abi_return
    final_request_id = xgov_registry_client.state.global_state.request_id
    assert rid == initial_request_id
    assert final_request_id == initial_request_id + 1

    # Approve resubscribe
    xgov_registry_client.send.approve_subscribe_xgov(
        args=ApproveUnsubscribeXgovArgs(request_id=rid),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs
    assert final_xgovs == xgovs + 1
    assert (
        xgov_registry_client.state.box.xgov_box.get_value(
            app_xgov_unsubscribe_requested.app_address
        ).unsubscribed_round
        == 0
    )
