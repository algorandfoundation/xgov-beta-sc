import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    PaymentParams,
    SigningAccount,
)

from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ApproveUnsubscribeXgovArgs,
    GetXgovBoxArgs,
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
            request_unsubscribe_id=xgov_registry_client.state.global_state.request_unsubscribe_id
            - 1
        ),
        params=CommonAppCallParams(sender=xgov_subscriber.address),
    )

    final_xgovs = xgov_registry_client.state.global_state.xgovs
    assert final_xgovs == initial_xgovs - 1

    with pytest.raises(LogicError, match="entry exists"):
        xgov_registry_client.send.get_xgov_box(
            args=GetXgovBoxArgs(xgov_address=app_xgov_unsubscribe_requested.app_address)
        )

    # Request new subscription
    initial_request_id = xgov_registry_client.state.global_state.request_id
    xgov_registry_client.send.request_subscribe_xgov(
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
    )
    final_request_id = xgov_registry_client.state.global_state.request_id
    assert final_request_id == initial_request_id + 1
