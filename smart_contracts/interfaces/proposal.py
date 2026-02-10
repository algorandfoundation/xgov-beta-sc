from abc import ABC, abstractmethod

from algopy import Account, ARC4Contract, Array, Bytes, String, UInt64, arc4, gtxn

import smart_contracts.common.abi_types as typ


class ProposalInterface(ARC4Contract, ABC):
    """Proposal Contract Interface"""

    @abstractmethod
    @arc4.abimethod(create="require")
    def create(self, *, proposer: Account) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def open(
        self,
        *,
        payment: gtxn.PaymentTransaction,
        title: String,
        funding_type: UInt64,
        requested_amount: UInt64,
        focus: arc4.UInt8,
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def upload_metadata(self, *, payload: Bytes, is_first_in_group: bool) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def drop(self) -> typ.Error:
        pass

    @abstractmethod
    @arc4.abimethod()
    def submit(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def assign_voters(
        self,
        *,
        voters: Array[typ.CommitteeMember],
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def vote(
        self, *, voter: Account, approvals: UInt64, rejections: UInt64
    ) -> typ.Error:
        pass

    @abstractmethod
    @arc4.abimethod()
    def scrutiny(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def unassign_absentees(self, *, absentees: Array[Account]) -> typ.Error:
        pass

    @abstractmethod
    @arc4.abimethod()
    def review(self, *, block: bool) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def fund(self) -> typ.Error:
        pass

    @abstractmethod
    @arc4.abimethod()
    def unassign_voters(self, *, voters: Array[Account]) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def finalize(self) -> typ.Error:
        pass

    @abstractmethod
    @arc4.abimethod(allow_actions=("DeleteApplication",))
    def delete(self) -> None:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_state(self) -> typ.ProposalTypedGlobalState:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_voter_box(self, *, voter_address: Account) -> tuple[UInt64, bool]:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_voting_state(self) -> typ.VotingState:
        pass

    @abstractmethod
    @arc4.abimethod()
    def op_up(self) -> None:
        pass
