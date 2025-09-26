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
)
from smart_contracts.errors import std_errors as err
from tests.utils import ERROR_TO_REGEX


def test_add_member_success(
    deployer: SigningAccount,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
) -> None:
    before_global_state = council_client.state.global_state.get_all()
    # sp = algorand_client.get_suggested_params()

    council_client.send.add_member(
        args=AddMemberArgs(
            address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    after_global_state = council_client.state.global_state.get_all()

    assert (before_global_state.get("member_count") + 1) == after_global_state.get(
        "member_count"
    )


def test_add_member_not_admin(
    no_role_account: SigningAccount,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        council_client.send.add_member(
            args=AddMemberArgs(
                address=no_role_account.address,
            ),
            params=CommonAppCallParams(
                sender=no_role_account.address,
                signer=no_role_account.signer,
            ),
        )


def test_add_member_already_member(
    deployer: SigningAccount,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
) -> None:
    council_client.send.add_member(
        args=AddMemberArgs(
            address=no_role_account.address,
        ),
        params=CommonAppCallParams(
            sender=deployer.address,
            signer=deployer.signer,
        ),
    )

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.VOTER_ALREADY_ASSIGNED]):
        council_client.send.add_member(
            args=AddMemberArgs(
                address=no_role_account.address,
            ),
            params=CommonAppCallParams(
                sender=deployer.address,
                signer=deployer.signer,
                note=b"meh",
            ),
        )
