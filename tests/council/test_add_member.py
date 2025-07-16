import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.models import Account

from smart_contracts.artifacts.council.council_client import CouncilClient
from smart_contracts.errors import std_errors as err
from tests.common import logic_error_type
from tests.council.common import members_box_name
from tests.utils import ERROR_TO_REGEX


def test_add_member_success(
    deployer: Account,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
) -> None:
    before_global_state = council_client.get_global_state()
    sp = algorand_client.get_suggested_params()

    council_client.add_member(
        address=no_role_account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[
                (0, members_box_name(no_role_account.address)),
            ],
        ),
    )

    after_global_state = council_client.get_global_state()

    assert (before_global_state.member_count + 1) == after_global_state.member_count


def test_add_member_not_admin(
    no_role_account: AddressAndSigner,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
) -> None:
    sp = algorand_client.get_suggested_params()

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        council_client.add_member(
            address=no_role_account.address,
            transaction_parameters=TransactionParameters(
                sender=no_role_account.address,
                signer=no_role_account.signer,
                suggested_params=sp,
                boxes=[
                    (0, members_box_name(no_role_account.address)),
                ],
            ),
        )


def test_add_member_already_member(
    deployer: Account,
    council_client: CouncilClient,
    algorand_client: AlgorandClient,
    no_role_account: AddressAndSigner,
) -> None:
    sp = algorand_client.get_suggested_params()

    council_client.add_member(
        address=no_role_account.address,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            suggested_params=sp,
            boxes=[
                (0, members_box_name(no_role_account.address)),
            ],
        ),
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.VOTER_ALREADY_ASSIGNED]):
        council_client.add_member(
            address=no_role_account.address,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                suggested_params=sp,
                boxes=[
                    (0, members_box_name(no_role_account.address)),
                ],
                note=b"meh",
            ),
        )
