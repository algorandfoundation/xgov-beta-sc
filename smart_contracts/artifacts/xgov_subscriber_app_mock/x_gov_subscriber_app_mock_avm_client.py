# This file is auto-generated, do not modify
# flake8: noqa
# fmt: off
import typing

import algopy


class XGovSubscriberAppMock(algopy.arc4.ARC4Client, typing.Protocol):
    @algopy.arc4.abimethod
    def subscribe_xgov(
        self,
        app_id: algopy.arc4.UIntN[typing.Literal[64]],
        voting_address: algopy.arc4.Address,
    ) -> None: ...

    @algopy.arc4.abimethod
    def unsubscribe_xgov(
        self,
        app_id: algopy.arc4.UIntN[typing.Literal[64]],
    ) -> None: ...
