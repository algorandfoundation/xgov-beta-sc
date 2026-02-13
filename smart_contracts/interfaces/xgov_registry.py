from abc import ABC, abstractmethod

from algopy import Account, Application, ARC4Contract, Array, Bytes, UInt64, arc4, gtxn

import smart_contracts.common.abi_types as typ


class XGovRegistryInterface(ARC4Contract, ABC):
    """xGov Registry Interface"""

    @abstractmethod
    @arc4.abimethod(create="require")
    def create(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def init_proposal_contract(self, *, size: UInt64) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def load_proposal_contract(self, *, offset: UInt64, data: Bytes) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def delete_proposal_contract_box(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def pause_registry(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def pause_proposals(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def resume_registry(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def resume_proposals(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_xgov_manager(self, *, manager: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_payor(self, *, payor: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_xgov_council(self, *, council: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_xgov_subscriber(self, *, subscriber: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_kyc_provider(self, *, provider: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_committee_manager(self, *, manager: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_xgov_daemon(self, *, xgov_daemon: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def config_xgov_registry(self, *, config: typ.XGovRegistryConfig) -> None:
        pass

    @abstractmethod
    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_xgov_registry(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def subscribe_xgov(
        self, *, voting_address: Account, payment: gtxn.PaymentTransaction
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def unsubscribe_xgov(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def unsubscribe_absentee(self, *, xgov_address: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def request_subscribe_xgov(
        self,
        *,
        xgov_address: Account,
        owner_address: Account,
        relation_type: UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> UInt64:
        pass

    @abstractmethod
    @arc4.abimethod()
    def approve_subscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def reject_subscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def request_unsubscribe_xgov(
        self,
        *,
        xgov_address: Account,
        owner_address: Account,
        relation_type: UInt64,
        payment: gtxn.PaymentTransaction,
    ) -> UInt64:
        pass

    @abstractmethod
    @arc4.abimethod()
    def approve_unsubscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def reject_unsubscribe_xgov(self, *, request_id: UInt64) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_voting_account(
        self, *, xgov_address: Account, voting_address: Account
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def subscribe_proposer(self, *, payment: gtxn.PaymentTransaction) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def set_proposer_kyc(
        self,
        *,
        proposer: Account,
        kyc_status: bool,
        kyc_expiring: UInt64,
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def declare_committee(
        self, *, committee_id: typ.Bytes32, size: UInt64, votes: UInt64
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod
    def open_proposal(self, *, payment: gtxn.PaymentTransaction) -> UInt64:
        pass

    @abstractmethod
    @arc4.abimethod()
    def vote_proposal(
        self,
        *,
        proposal_id: Application,
        xgov_address: Account,
        approval_votes: UInt64,
        rejection_votes: UInt64,
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def unassign_absentee_from_proposal(
        self, *, proposal_id: Application, absentees: Array[Account]
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def pay_grant_proposal(self, *, proposal_id: Application) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def finalize_proposal(self, *, proposal_id: Application) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def drop_proposal(self, *, proposal_id: Application) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def deposit_funds(self, *, payment: gtxn.PaymentTransaction) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def withdraw_funds(self, *, amount: UInt64) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def withdraw_balance(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.TypedGlobalState:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_xgov_box(self, *, xgov_address: Account) -> tuple[typ.XGovBoxValue, bool]:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_proposer_box(
        self, *, proposer_address: Account
    ) -> tuple[typ.ProposerBoxValue, bool]:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_request_box(
        self, *, request_id: UInt64
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_request_unsubscribe_box(
        self, *, request_id: UInt64
    ) -> tuple[typ.XGovSubscribeRequestBoxValue, bool]:
        pass

    @abstractmethod
    @arc4.abimethod()
    def is_proposal(self, *, proposal_id: Application) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def op_up(self) -> None:
        pass
