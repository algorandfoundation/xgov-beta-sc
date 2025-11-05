import pytest
from algokit_utils import (
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.council.council_client import (
    AddMemberArgs,
    CouncilClient,
    RemoveMemberArgs,
)
from smart_contracts.errors import std_errors as err
from tests.utils import ERROR_TO_REGEX


def test_remove_member_success(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    no_role_account: SigningAccount,
    council_client: CouncilClient
) -> None:
    before_global_state = council_client.state.global_state.get_all()

    council_client.send.add_member(
        args=AddMemberArgs(
            address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    added_global_state = council_client.state.global_state.get_all()

    assert (before_global_state.get("member_count") + 1) == added_global_state.get(
        "member_count"
    )

    council_client.send.remove_member(
        args=RemoveMemberArgs(
            address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    removed_global_state = council_client.state.global_state.get_all()

    assert before_global_state.get("member_count") == removed_global_state.get(
        "member_count"
    )


def test_remove_member_not_admin(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    council_client: CouncilClient
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        council_client.send.remove_member(
            args=RemoveMemberArgs(
                address=no_role_account.address,
            ),
            params=CommonAppCallParams(
                sender=no_role_account.address,
                signer=no_role_account.signer,
            ),
        )


def test_remove_member_not_member(
    algorand_client: AlgorandClient,
    deployer: SigningAccount,
    no_role_account: SigningAccount,
    council_client: CouncilClient
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTER_NOT_FOUND]):
        council_client.send.remove_member(
            args=RemoveMemberArgs(
                address=no_role_account.address,
            ),
            params=CommonAppCallParams(
                sender=deployer.address,
                signer=deployer.signer,
            ),
        )
