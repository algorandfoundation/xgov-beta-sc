from abc import ABC, abstractmethod

from algopy import ARC4Contract, arc4, gtxn

from smart_contracts.common import abi_types as typ


class ProposalInterface(ARC4Contract, ABC):
    @abstractmethod
    @arc4.abimethod(create="require")
    def create(self, *, proposer: arc4.Address) -> typ.Error:
        pass

    @abstractmethod
    @arc4.abimethod()
    def open(
        self,
        *,
        payment: gtxn.PaymentTransaction,
        title: arc4.String,
        funding_type: arc4.UInt64,
        requested_amount: arc4.UInt64,
        focus: arc4.UInt8,
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def upload_metadata(
        self, *, payload: arc4.DynamicBytes, is_first_in_group: arc4.Bool
    ) -> None:
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
        voters: arc4.DynamicArray[typ.CommitteeMember],
    ) -> None:
        pass

    @abstractmethod
    @arc4.abimethod()
    def vote(
        self, *, voter: arc4.Address, approvals: arc4.UInt64, rejections: arc4.UInt64
    ) -> typ.Error:
        pass

    @abstractmethod
    @arc4.abimethod()
    def scrutiny(self) -> None:
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
    def unassign_voters(self, *, voters: arc4.DynamicArray[arc4.Address]) -> None:
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
    def get_voter_box(self, *, voter_address: arc4.Address) -> tuple[arc4.UInt64, bool]:
        pass

    @abstractmethod
    @arc4.abimethod(readonly=True)
    def get_voting_state(self) -> typ.VotingState:
        pass

    @abstractmethod
    @arc4.abimethod()
    def op_up(self) -> None:
        pass
