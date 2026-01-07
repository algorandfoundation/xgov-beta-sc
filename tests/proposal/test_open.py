import pytest
from algokit_utils import AlgoAmount, AlgorandClient, LogicError, SigningAccount

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
    FUNDING_CATEGORY_SMALL,
    FUNDING_NULL,
)
from smart_contracts.xgov_registry.config import (
    MAX_REQUESTED_AMOUNT_LARGE,
    MAX_REQUESTED_AMOUNT_MEDIUM,
    MAX_REQUESTED_AMOUNT_SMALL,
    MIN_REQUESTED_AMOUNT,
)
from tests.proposal.common import (
    LOCKED_AMOUNT,
    PROPOSAL_PARTIAL_FEE,
    assert_account_balance,
    assert_draft_proposal_global_state,
    assert_empty_proposal_global_state,
    get_locked_amount,
    open_proposal,
)

# TODO add tests for open on other statuses


class TestOpenSuccess:
    """Tests for successful proposal opening with different funding categories."""

    def test_open_success(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
    ) -> None:
        open_proposal(proposal_client, algorand_client, proposer, metadata=b"")

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

    @pytest.mark.parametrize(
        "requested_micro_algo,expected_category",
        [
            # Small category
            (MIN_REQUESTED_AMOUNT, FUNDING_CATEGORY_SMALL),
            (MIN_REQUESTED_AMOUNT + 1, FUNDING_CATEGORY_SMALL),
            (MAX_REQUESTED_AMOUNT_SMALL - 1, FUNDING_CATEGORY_SMALL),
            (MAX_REQUESTED_AMOUNT_SMALL, FUNDING_CATEGORY_SMALL),
            # Medium category
            (MAX_REQUESTED_AMOUNT_SMALL + 1, FUNDING_CATEGORY_MEDIUM),
            (MAX_REQUESTED_AMOUNT_MEDIUM - 1, FUNDING_CATEGORY_MEDIUM),
            (MAX_REQUESTED_AMOUNT_MEDIUM, FUNDING_CATEGORY_MEDIUM),
            # Large category
            (MAX_REQUESTED_AMOUNT_MEDIUM + 1, FUNDING_CATEGORY_LARGE),
            (MAX_REQUESTED_AMOUNT_LARGE - 1, FUNDING_CATEGORY_LARGE),
            (MAX_REQUESTED_AMOUNT_LARGE, FUNDING_CATEGORY_LARGE),
        ],
        ids=[
            "small_min",
            "small_min_plus_1",
            "small_max_minus_1",
            "small_max",
            "medium_min",
            "medium_max_minus_1",
            "medium_max",
            "large_min",
            "large_max_minus_1",
            "large_max",
        ],
    )
    def test_open_funding_categories(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
        requested_micro_algo: int,
        expected_category: int,
    ) -> None:
        requested_amount = AlgoAmount(micro_algo=requested_micro_algo)
        locked_amount = get_locked_amount(requested_amount)

        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            metadata=b"",
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )

        assert_draft_proposal_global_state(
            proposal_client,
            registry_app_id=xgov_registry_mock_client.app_id,
            proposer_address=proposer.address,
            requested_amount=requested_amount,
            locked_amount=locked_amount,
            funding_category=expected_category,
        )

        assert_account_balance(
            algorand_client,
            proposal_client.app_address,
            int(locked_amount + AlgoAmount(micro_algo=PROPOSAL_PARTIAL_FEE)),
        )


class TestOpenErrors:
    """Tests for proposal opening error cases."""

    def test_open_not_proposer(
        self,
        algorand_client: AlgorandClient,
        no_role_account: SigningAccount,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
    ) -> None:
        with pytest.raises(LogicError, match=err.UNAUTHORIZED):
            open_proposal(
                proposal_client,
                algorand_client,
                no_role_account,
                metadata=b"",
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
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
    ) -> None:
        open_proposal(proposal_client, algorand_client, proposer, metadata=b"")

        with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
            )

        assert_draft_proposal_global_state(
            proposal_client,
            registry_app_id=xgov_registry_mock_client.app_id,
            proposer_address=proposer.address,
        )

        assert_account_balance(
            algorand_client,
            proposal_client.app_address,
            int(LOCKED_AMOUNT + AlgoAmount(micro_algo=PROPOSAL_PARTIAL_FEE)),
        )

    @pytest.mark.parametrize(
        "title",
        ["", "a" * (TITLE_MAX_BYTES + 1)],
        ids=["empty_title", "title_too_long"],
    )
    def test_open_wrong_title(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
        title: str,
    ) -> None:
        with pytest.raises(LogicError, match=err.WRONG_TITLE_LENGTH):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
                title=title,
            )

        assert_empty_proposal_global_state(
            proposal_client, proposer.address, xgov_registry_mock_client.app_id
        )

        assert_account_balance(
            algorand_client,
            proposal_client.app_address,
            PROPOSAL_PARTIAL_FEE,
        )

    @pytest.mark.parametrize(
        "funding_type",
        [FUNDING_NULL, FUNDING_NULL + 1],
        ids=["funding_null", "funding_invalid"],
    )
    def test_open_wrong_funding_type(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
        funding_type: int,
    ) -> None:
        with pytest.raises(LogicError, match=err.WRONG_FUNDING_TYPE):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
                funding_type=funding_type,
            )

        assert_empty_proposal_global_state(
            proposal_client, proposer.address, xgov_registry_mock_client.app_id
        )

        assert_account_balance(
            algorand_client,
            proposal_client.app_address,
            PROPOSAL_PARTIAL_FEE,
        )

    @pytest.mark.parametrize(
        "amount_offset,expected_error",
        [
            (-1, err.WRONG_MIN_REQUESTED_AMOUNT),
            (
                MAX_REQUESTED_AMOUNT_LARGE - MIN_REQUESTED_AMOUNT + 1,
                err.WRONG_MAX_REQUESTED_AMOUNT,
            ),
        ],
        ids=["below_min", "above_max"],
    )
    def test_open_wrong_requested_amount(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
        amount_offset: int,
        expected_error: str,
    ) -> None:
        requested_amount = AlgoAmount(micro_algo=MIN_REQUESTED_AMOUNT + amount_offset)
        locked_amount = get_locked_amount(requested_amount)

        with pytest.raises(LogicError, match=expected_error):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
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

    @pytest.mark.parametrize(
        "locked_amount_offset",
        [-1, 1],
        ids=["underpayment", "overpayment"],
    )
    def test_open_wrong_locked_amount(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
        locked_amount_offset: int,
    ) -> None:
        locked_amount = AlgoAmount(
            micro_algo=LOCKED_AMOUNT.micro_algo + locked_amount_offset
        )

        with pytest.raises(LogicError, match=err.WRONG_LOCKED_AMOUNT):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
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

    @pytest.mark.skip("waiting for simulate bug to be fixed")
    def test_open_wrong_payment_sender(
        self,
        algorand_client: AlgorandClient,
        no_role_account: SigningAccount,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
    ) -> None:
        with pytest.raises(LogicError, match=err.WRONG_SENDER):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
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

    def test_open_wrong_payment_receiver(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
    ) -> None:
        with pytest.raises(LogicError, match=err.WRONG_RECEIVER):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
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

    def test_open_paused_registry_error(
        self,
        algorand_client: AlgorandClient,
        proposer: SigningAccount,
        xgov_registry_mock_client: XgovRegistryMockClient,
        proposal_client: ProposalClient,
    ) -> None:
        requested_amount = AlgoAmount(micro_algo=MAX_REQUESTED_AMOUNT_LARGE)
        locked_amount = get_locked_amount(requested_amount)

        xgov_registry_mock_client.send.pause_registry()

        with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
            open_proposal(
                proposal_client,
                algorand_client,
                proposer,
                metadata=b"",
                requested_amount=requested_amount,
                locked_amount=locked_amount,
            )

        xgov_registry_mock_client.send.resume_registry()

        open_proposal(
            proposal_client,
            algorand_client,
            proposer,
            metadata=b"",
            requested_amount=requested_amount,
            locked_amount=locked_amount,
        )
