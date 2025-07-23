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
from tests.common import logic_error_type
from tests.proposal.common import (
    assert_boxes,
    open_proposal,
    upload_metadata,
)
from tests.utils import ERROR_TO_REGEX

# TODO add tests for upload on other statuses


def test_empty_proposal(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    with pytest.raises(
        logic_error_type, match=ERROR_TO_REGEX[err.WRONG_PROPOSAL_STATUS]
    ):
        composer = proposal_client.compose()
        upload_metadata(
            composer,
            proposer,
            xgov_registry_mock_client.app_id,
            b"ANY PAYLOAD",
        )
        composer.execute()


def test_upload_success_1(
    draft_proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:

    payload = json.dumps({"o": "a" * 500}).encode()  # type: ignore

    composer = draft_proposal_client.compose()
    upload_metadata(
        composer,
        proposer,
        xgov_registry_mock_client.app_id,
        payload,
    )
    composer.execute()

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_success_2(
    draft_proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:

    payload = json.dumps({"o": "a" * 1500}).encode()  # type: ignore

    composer = draft_proposal_client.compose()
    upload_metadata(
        composer,
        proposer,
        xgov_registry_mock_client.app_id,
        payload,
    )
    composer.execute()

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_success_3(
    draft_proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:

    payload = json.dumps({"o": "a" * 2500}).encode()  # type: ignore

    composer = draft_proposal_client.compose()
    upload_metadata(
        composer,
        proposer,
        xgov_registry_mock_client.app_id,
        payload,
    )
    composer.execute()

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_not_proposer(
    draft_proposal_client: ProposalClient,
    no_role_account: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.UNAUTHORIZED]):
        composer = draft_proposal_client.compose()
        upload_metadata(
            composer,
            no_role_account,
            xgov_registry_mock_client.app_id,
            b"ANY PAYLOAD",
        )
        composer.execute()


def test_empty_payload(
    draft_proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    with pytest.raises(logic_error_type, match=ERROR_TO_REGEX[err.EMPTY_PAYLOAD]):
        composer = draft_proposal_client.compose()
        upload_metadata(
            composer,
            proposer,
            xgov_registry_mock_client.app_id,
            b"",
        )
        composer.execute()


def test_paused_registry_error(
    draft_proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
) -> None:

    xgov_registry_mock_client.pause_registry()

    with pytest.raises(logic_error_type, match=err.PAUSED_REGISTRY):
        composer = draft_proposal_client.compose()
        upload_metadata(
            composer,
            proposer,
            xgov_registry_mock_client.app_id,
            b"ANY PAYLOAD",
        )
        composer.execute()

    # We unpause the xGov Registry due to `xgov_registry_mock_client` fixture "session" scope, to avoid flaky tests.
    xgov_registry_mock_client.resume_registry()

    composer = draft_proposal_client.compose()
    upload_metadata(
        composer,
        proposer,
        xgov_registry_mock_client.app_id,
        b"ANY PAYLOAD",
    )
    composer.execute()


def test_open_with_upload_metadata(
    proposal_client: ProposalClient,
    proposer: AddressAndSigner,
    xgov_registry_mock_client: XgovRegistryMockClient,
    algorand_client: AlgorandClient,
) -> None:
    payload = json.dumps({"o": "a" * 500}).encode()  # type: ignore

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        xgov_registry_mock_client.app_id,
        metadata=payload,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )
