from algopy import (
    Account,
    Application,
    ARC4Contract,
    Global,
    arc4,
    itxn,
    op,
)

from ..xgov_registry import config as rcfg
from ..xgov_registry import contract as registry_contract


class XGovSubscriberAppMock(ARC4Contract):
    @arc4.abimethod()
    def subscribe_xgov(self, app_id: Application, voting_address: Account) -> None:

        xgov_fee, _xgov_min_balance_exists = op.AppGlobal.get_ex_uint64(
            app_id, rcfg.GS_KEY_XGOV_FEE
        )

        payment = itxn.Payment(
            receiver=app_id.address,
            amount=xgov_fee,
        )

        arc4.abi_call(
            registry_contract.XGovRegistry.subscribe_xgov,
            voting_address,
            payment,
            app_id=app_id.id,
        )

    @arc4.abimethod()
    def unsubscribe_xgov(self, app: Application) -> None:
        arc4.abi_call(
            registry_contract.XGovRegistry.unsubscribe_xgov,
            app_id=app.id,
            fee=(Global.min_txn_fee * 2),
        )
