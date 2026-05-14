# This file is auto-generated, do not modify
# flake8: noqa
# fmt: off
import typing

import algopy


class Council(algopy.arc4.ARC4Client, typing.Protocol):
    @algopy.arc4.abimethod(create='require')
    def create(
        self,
        registry_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None:
        """
        Create a new council contract.
        """

    @algopy.arc4.abimethod(allow_actions=['UpdateApplication'])
    def update_council(
        self,
    ) -> None:
        """
        Update the council contract.
        """

    @algopy.arc4.abimethod
    def add_member(
        self,
        address: algopy.arc4.Address,
    ) -> None:
        """
        Add a member to the council.
        """

    @algopy.arc4.abimethod
    def remove_member(
        self,
        address: algopy.arc4.Address,
    ) -> None:
        """
        Remove a member from the council.
        """

    @algopy.arc4.abimethod
    def vote(
        self,
        proposal_id: algopy.arc4.UIntN[typing.Literal[64]],
        block: algopy.arc4.Bool,
    ) -> None:
        """
        Cast a vote on a proposal.
        """

    @algopy.arc4.abimethod
    def op_up(
        self,
    ) -> None: ...
