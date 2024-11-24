from algopy import (
    Application,
    ARC4Contract,
    Global,
    StateTotals,
    Txn,
    UInt64,
    arc4,
    itxn,
    op,
)

import smart_contracts.errors.std_errors as err

from ..xgov_registry import config as rcfg
from ..xgov_registry import contract as registry_contract
from . import config as mock_cfg


class XGovSubscriberAppMock(
    ARC4Contract,
    state_totals=StateTotals(
        global_bytes=mock_cfg.GLOBAL_BYTES,
        global_uints=mock_cfg.GLOBAL_UINTS,
        local_bytes=mock_cfg.LOCAL_BYTES,
        local_uints=mock_cfg.LOCAL_UINTS,
    ),
):

    def __init__(self) -> None:
        # Preconditions
        assert (
            Txn.global_num_byte_slice == mock_cfg.GLOBAL_BYTES
        ), err.WRONG_GLOBAL_BYTES
        assert Txn.global_num_uint == mock_cfg.GLOBAL_UINTS, err.WRONG_GLOBAL_UINTS
        assert Txn.local_num_byte_slice == mock_cfg.LOCAL_BYTES, err.WRONG_LOCAL_BYTES
        assert Txn.local_num_uint == mock_cfg.LOCAL_UINTS, err.WRONG_LOCAL_UINTS

    @arc4.abimethod()
    def subscribe_xgov(self, app_id: UInt64, voting_address: arc4.Address) -> None:

        xgov_fee, xgov_min_balance_exists = op.AppGlobal.get_ex_uint64(
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
