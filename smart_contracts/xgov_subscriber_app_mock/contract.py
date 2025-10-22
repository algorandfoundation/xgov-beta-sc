from algopy import (
    Application,
    ARC4Contract,
    Global,
    UInt64,
    arc4,
    itxn,
    op,
)

from ..xgov_registry import config as rcfg
from ..xgov_registry import contract as registry_contract


class XGovSubscriberAppMock(ARC4Contract):
    @arc4.abimethod()
    def subscribe_xgov(self, app_id: UInt64, voting_address: arc4.Address) -> None:

        xgov_fee, _xgov_min_balance_exists = op.AppGlobal.get_ex_uint64(
            app_id, rcfg.GS_KEY_XGOV_FEE
        )

        payment = itxn.Payment(
            receiver=Application(app_id).address,
            amount=xgov_fee,
        )

        arc4.abi_call(
            registry_contract.XGovRegistry.subscribe_xgov,
            voting_address,
            payment,
            app_id=app_id,
        )

    @arc4.abimethod()
    def unsubscribe_xgov(self, app_id: UInt64) -> None:
        arc4.abi_call(
            registry_contract.XGovRegistry.unsubscribe_xgov,
            arc4.Address(Global.current_application_address),
            app_id=app_id,
            fee=(Global.min_txn_fee * 2),
        )
