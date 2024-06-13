import dataclasses
from typing import Optional

import algosdk.account
from algokit_utils.account import Account as UtilsAccount
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import (
    PaymentTxn,
    SuggestedParams,
    Transaction,
    wait_for_confirmation,
)
from algosdk.v2client.algod import AlgodClient
from typing_extensions import Self


@dataclasses.dataclass(kw_only=True)
class Account(UtilsAccount):
    """Account Client class that handles common account ops (state fetching, transactions creation, signatures)"""

    client: AlgodClient
    """AlgodClient to perform on-chain operations"""

    @staticmethod
    def new_account() -> "UtilsAccount":
        raise NotImplementedError("Use `new_account_client` instead")

    @staticmethod
    def new_account_client(client: AlgodClient) -> "Account":
        private_key, _ = algosdk.account.generate_account()  # type: ignore
        return Account(private_key=private_key, client=client)  # type: ignore

    def get_params(self) -> SuggestedParams:
        return self.client.suggested_params()

    def sign_send_wait(self, txn: Transaction) -> dict[str, str | int]:
        signed_txn = self.signer.sign_transactions([txn], [0]).pop()
        txn_id = signed_txn.get_txid()  # type: ignore
        self.client.send_transaction(signed_txn)
        txn_info = wait_for_confirmation(self.client, txn_id)  # type: ignore
        return {"txn-id": txn_id, **txn_info}  # type: ignore

    def pay_txn(
        self,
        receiver: Self | str,
        amount: int,
        *,
        sp: Optional[SuggestedParams] = None,
        **kwargs: str | bytes
    ) -> TransactionWithSigner:
        txn: PaymentTxn = PaymentTxn(
            self.address,
            sp or self.get_params(),
            receiver if isinstance(receiver, str) else receiver.address,
            amount,
            **kwargs,
        )  # type: ignore
        return TransactionWithSigner(txn, self.signer)

    def pay(
        self,
        receiver: Self | str,
        amount: int,
        *,
        sp: Optional[SuggestedParams] = None,
        **kwargs: str | bytes
    ) -> dict[str, str | int]:
        return self.sign_send_wait(self.pay_txn(receiver, amount, sp=sp, **kwargs).txn)
