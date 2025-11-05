import base64
import json

import pytest
from algokit_utils import AlgorandClient, LogicError, SigningAccount

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import (
    assert_boxes,
    open_proposal,
    upload_metadata,
)

# TODO add tests for upload on other statuses


def test_empty_proposal(
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
) -> None:

    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        composer = proposal_client.new_group()
        upload_metadata(
            composer,
            proposer,
            b"ANY PAYLOAD",
        )
        composer.send()


def test_upload_success_1(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:

    payload = json.dumps({"o": "a" * 500}).encode()  # type: ignore

    composer = draft_proposal_client.new_group()
    upload_metadata(
        composer,
        proposer,
        payload,
    )
    composer.send()

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_success_2(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:

    payload = json.dumps({"o": "a" * 1500}).encode()  # type: ignore

    composer = draft_proposal_client.new_group()
    upload_metadata(
        composer,
        proposer,
        payload,
    )
    composer.send()

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_success_3(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:

    payload = json.dumps({"o": "a" * 2500}).encode()  # type: ignore

    composer = draft_proposal_client.new_group()
    upload_metadata(
        composer,
        proposer,
        payload,
    )
    composer.send()

    assert_boxes(
        algorand_client=algorand_client,
        app_id=draft_proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )


def test_upload_not_proposer(
    no_role_account: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:

    with pytest.raises(LogicError, match=err.UNAUTHORIZED):
        composer = draft_proposal_client.new_group()
        upload_metadata(
            composer,
            no_role_account,
            b"ANY PAYLOAD",
        )
        composer.send()


def test_empty_payload(
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:

    with pytest.raises(LogicError, match=err.EMPTY_PAYLOAD):
        composer = draft_proposal_client.new_group()
        upload_metadata(
            composer,
            proposer,
            b"",
        )
        composer.send()


def test_paused_registry_error(
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    draft_proposal_client: ProposalClient,
) -> None:

    xgov_registry_mock_client.send.pause_registry()

    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        composer = draft_proposal_client.new_group()
        upload_metadata(
            composer,
            proposer,
            b"ANY PAYLOAD",
        )
        composer.send()

    # We unpause the xGov Registry due to `xgov_registry_mock_client` fixture "session" scope, to avoid flaky tests.
    xgov_registry_mock_client.send.resume_registry()

    composer = draft_proposal_client.new_group()
    upload_metadata(
        composer,
        proposer,
        b"ANY PAYLOAD",
    )
    composer.send()


def test_open_with_upload_metadata(
    algorand_client: AlgorandClient,
    proposer: SigningAccount,
    xgov_registry_mock_client: XgovRegistryMockClient,
    proposal_client: ProposalClient,
) -> None:
    payload = json.dumps({"o": "a" * 500}).encode()  # type: ignore

    open_proposal(
        proposal_client,
        algorand_client,
        proposer,
        metadata=payload,
    )

    assert_boxes(
        algorand_client=algorand_client,
        app_id=proposal_client.app_id,
        expected_boxes=[
            (METADATA_BOX_KEY.encode(), base64.b64encode(payload).decode())
        ],
    )
