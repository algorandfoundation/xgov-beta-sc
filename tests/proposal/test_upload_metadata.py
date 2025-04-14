import base64
import json

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import (
    assert_boxes,
    logic_error_type,
    submit_proposal,
    upload_metadata,
)
from tests.utils import ERROR_TO_REGEX

# TODO add tests for upload on other statuses

max_payload_size = 2042


def test_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        upload_metadata(
            proposal_client,
            proposer,
            xgov_registry_mock_client.app_id,
            b"ANY PAYLOAD",
        )


def test_upload_success_1(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    payload = json.dumps({"o": "a" * 500}).encode()  # type: ignore

    upload_metadata(
        proposal_client,
        proposer,
        xgov_registry_mock_client.app_id,
        payload,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_success_2(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    payload = json.dumps({"o": "a" * 1500}).encode()  # type: ignore

    upload_metadata(
        proposal_client,
        proposer,
        xgov_registry_mock_client.app_id,
        payload,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_success_3(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    payload = json.dumps({"o": "a" * 2500}).encode()  # type: ignore

    upload_metadata(
        proposal_client,
        proposer,
        xgov_registry_mock_client.app_id,
        payload,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_not_proposer(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    not_proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        upload_metadata(
            proposal_client,
            not_proposer,
            xgov_registry_mock_client.app_id,
            b"ANY PAYLOAD",
        )


def test_empty_payload(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:

    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.EMPTY_PAYLOAD]):
        upload_metadata(
            proposal_client,
            proposer,
            xgov_registry_mock_client.app_id,
            b"",
        )


def test_paused_registry_error(
    proposal_client: ProposalClient,
    algorand_client: AlgorandClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:
    submit_proposal(
        proposal_client, algorand_client, proposer, xgov_registry_mock_client.app_id
    )

    xgov_registry_mock_client.pause_registry()

    with pytest.raises(logic_error_type, match=err.PAUSED_REGISTRY):
        upload_metadata(
            proposal_client,
            proposer,
            xgov_registry_mock_client.app_id,
            b"ANY PAYLOAD",
        )

    # We unpause the xGov Registry due to `xgov_registry_mock_client` fixture "session" scope, to avoid flaky tests.
    xgov_registry_mock_client.resume_registry()

    upload_metadata(
        proposal_client,
        proposer,
        xgov_registry_mock_client.app_id,
        b"ANY PAYLOAD",
    )
