import base64
import json
import uuid

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry_mock.xgov_registry_mock_client import (
    XgovRegistryMockClient,
)
from smart_contracts.errors import std_errors as err
from smart_contracts.proposal.config import METADATA_BOX_KEY
from tests.proposal.common import assert_boxes, logic_error_type, submit_proposal
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
        proposal_client.upload_metadata(
            payload=b"payload",
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                boxes=[(0, METADATA_BOX_KEY)],
            ),
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

    proposal_client.upload_metadata(
        payload=payload,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            boxes=[(0, METADATA_BOX_KEY)],
        ),
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

    proposal_client.upload_metadata(
        payload=payload,
        transaction_parameters=TransactionParameters(
            sender=proposer.address,
            signer=proposer.signer,
            boxes=[(0, METADATA_BOX_KEY), (0, METADATA_BOX_KEY)],
        ),
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

    composer = proposal_client.compose()

    for i in range((len(payload) // max_payload_size) + 1):
        composer.upload_metadata(
            payload=payload[i * max_payload_size : (i + 1) * max_payload_size],
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                boxes=[(0, METADATA_BOX_KEY), (0, METADATA_BOX_KEY)],
                note=uuid.uuid4().bytes,
            ),
        )

    composer.execute()

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
        proposal_client.upload_metadata(
            payload=b"payload",
            transaction_parameters=TransactionParameters(
                sender=not_proposer.address,
                signer=not_proposer.signer,
                boxes=[(0, METADATA_BOX_KEY)],
            ),
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
        proposal_client.upload_metadata(
            payload=b"",
            transaction_parameters=TransactionParameters(
                sender=proposer.address,
                signer=proposer.signer,
                boxes=[(0, METADATA_BOX_KEY)],
            ),
        )
