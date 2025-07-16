import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

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
from tests.common import logic_error_type
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    REQUESTED_AMOUNT,
    assert_account_balance,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    submit_proposal,
    get_locked_amount
)
from tests.utils import ERROR_TO_REGEX
from tests.xgov_registry.common import LogicErrorType

# TODO add tests for submit on other statuses


def test_submit_success(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )


def test_submit_not_proposer(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    no_role_account: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        submit_proposal(
            proposal_client,
            algorand_client,
            no_role_account,
            xgov_registry_mock_client.app_id,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_twice(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        submit_proposal(
            proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
        )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_title_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_TITLE_LENGTH]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            title="",
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_title_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_TITLE_LENGTH]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            title="a" * (TITLE_MAX_BYTES + 1),
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_funding_type_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_FUNDING_TYPE]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            funding_type=FUNDING_NULL,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_funding_type_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_FUNDING_TYPE]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            funding_type=FUNDING_NULL + 1,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_requested_amount_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = REQUESTED_AMOUNT - 1
    locked_amount = get_locked_amount(requested_amount)
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_MIN_REQUESTED_AMOUNT]
    ):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_requested_amount_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_LARGE + 1
    locked_amount = get_locked_amount(requested_amount)
    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_MAX_REQUESTED_AMOUNT]
    ):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_payment_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    locked_amount = LOCKED_AMOUNT - 1
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_LOCKED_AMOUNT]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            locked_amount=locked_amount,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_payment_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    locked_amount = LOCKED_AMOUNT + 1
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_LOCKED_AMOUNT]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            locked_amount=locked_amount,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_payment_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    no_role_account: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_SENDER]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            payment_sender=no_role_account,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_wrong_payment_4(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.WRONG_RECEIVER]):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            payment_receiver=proposer.address,
        )

    global_state = proposal_client.get_global_state()

    assert_empty_proposal_global_state(
        global_state, proposer.address, xgov_registry_mock_client.app_id
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        PROPOSAL_PARTIAL_FEE,
    )


def test_submit_funding_category_small_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
        registry_app_id=xgov_registry_mock_client.app_id,
        proposer_address=proposer.address,
    )

    assert_account_balance(
        algorand_client,
        proposal_client.app_address,
        LOCKED_AMOUNT + PROPOSAL_PARTIAL_FEE,
    )


def test_submit_funding_category_small_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MIN_REQUESTED_AMOUNT + 1
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_small_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_SMALL - 1
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_small_4(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_SMALL
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_medium_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_SMALL + 1
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_medium_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_MEDIUM - 1
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_medium_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_MEDIUM
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_large_1(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_MEDIUM + 1
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_large_2(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_LARGE - 1
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_funding_category_large_3(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_LARGE
    locked_amount = get_locked_amount(requested_amount)

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )

    global_state = proposal_client.get_global_state()

    assert_draft_proposal_global_state(
        global_state,
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


def test_submit_paused_registry_error(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    requested_amount = MAX_REQUESTED_AMOUNT_LARGE
    locked_amount = get_locked_amount(requested_amount)

    xgov_registry_mock_client.pause_registry()

    with pytest.raises(LogicErrorType, match=err.PAUSED_REGISTRY):
        submit_proposal(
            proposal_client,
            algorand_client,
            proposer,
            xgov_registry_mock_client.app_id,
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )

    xgov_registry_mock_client.resume_registry()

    submit_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        requested_amount=requested_amount,
        locked_amount=locked_amount,
    )
