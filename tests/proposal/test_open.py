import pytest

from algokit_utils import AlgorandClient, SigningAccount, AlgoAmount, LogicError

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.constants import (
    TITLE_MAX_BYTES,
)
from smart_contracts.proposal.enums import (
    FUNDING_CATEGORY_LARGE,
    FUNDING_CATEGORY_MEDIUM,
    FUNDING_NULL,
)
from smart_contracts.xgov_registry.config import (
    MAX_REQUESTED_AMOUNT_LARGE,
    MAX_REQUESTED_AMOUNT_MEDIUM,
    MAX_REQUESTED_AMOUNT_SMALL,
    MIN_REQUESTED_AMOUNT,
)

from tests.utils import ERROR_TO_REGEX
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    REQUESTED_AMOUNT,
    assert_account_balance,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    get_locked_amount,
    open_proposal,
)

# TODO add tests for open on other statuses


def test_open_success(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:

    open_proposal(proposal_client, algorand_client, proposer)

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT.micro_algo + PROPOSAL_PARTIAL_FEE,
    )


def test_open_not_proposer(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        open_proposal(
            proposal_client,
            algorand_client,
            no_role_account,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_twice(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:

    open_proposal(proposal_client, algorand_client, proposer)
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]):
        open_proposal(proposal_client, algorand_client, proposer)

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_title_1(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_TITLE_LENGTH]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            title="",
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_title_2(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_TITLE_LENGTH]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            title="a" * (TITLE_MAX_BYTES + 1),
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_funding_type_1(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_FUNDING_TYPE]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            funding_type=FUNDING_NULL,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_funding_type_2(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_FUNDING_TYPE]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            funding_type=FUNDING_NULL + 1,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_requested_amount_1(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = REQUESTED_AMOUNT - 1
    locked_amount = get_locked_amount(requested_amount)
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_MIN_REQUESTED_AMOUNT]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_requested_amount_2(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_LARGE + 1)
    locked_amount = get_locked_amount(requested_amount)
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_MAX_REQUESTED_AMOUNT]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_payment_1(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    locked_amount = AlgoAmount(micro_algo=LOCKED_AMOUNT.micro_algo - 1)
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_LOCKED_AMOUNT]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            locked_amount=locked_amount,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_payment_2(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    locked_amount = LOCKED_AMOUNT + 1
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_LOCKED_AMOUNT]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            locked_amount=locked_amount,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_payment_3(
    algorand_client: AlgorandClient,
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_SENDER]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            payment_sender=no_role_account,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_wrong_payment_4(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.WRONG_RECEIVER]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            payment_receiver=proposer.address,
        )

    assert_empty_proposal_global_state(
        proposal_client, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_small_1(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:

    open_proposal(proposal_client, algorand_client, proposer)

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_small_2(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MIN_REQUESTED_AMOUNT + 1)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_small_3(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_SMALL - 1)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_small_4(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_SMALL)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_medium_1(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_SMALL + 1)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        funding_category=FUNDING_CATEGORY_MEDIUM,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_medium_2(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_MEDIUM - 1)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        funding_category=FUNDING_CATEGORY_MEDIUM,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_medium_3(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_MEDIUM)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        funding_category=FUNDING_CATEGORY_MEDIUM,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_large_1(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_MEDIUM + 1)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        funding_category=FUNDING_CATEGORY_LARGE,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_large_2(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_LARGE - 1)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        funding_category=FUNDING_CATEGORY_LARGE,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_funding_category_large_3(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_LARGE)
    locked_amount = get_locked_amount(requested_amount)

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    assert_draft_proposal_global_state(
        proposal_client,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
        funding_category=FUNDING_CATEGORY_LARGE,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        locked_amount + PROPOSAL_PARTIAL_FEE,
    )


def test_open_paused_registry_error(
    algorand_client: AlgorandClient,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposer: SigningAccount,
    proposal_client: ProposalClient,
) -> None:
    requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_LARGE)
    locked_amount = get_locked_amount(requested_amount)

    xgov_registry_mock_client.send.pause_registry()

    with pytest.raises(LogicError, match=ERROR_TO_REGEX[err.PAUSED_REGISTRY]):
        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )

    xgov_registry_mock_client.send.resume_registry()

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )
