from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_TESTNET_COMMITTEE_MEMBERS = 30
DEFAULT_TESTNET_COMMITTEE_VOTES = 9_000_000


@dataclass(frozen=True)
class CommitteeIndexEntry:
    committee_id_b64: str
    total_members: int
    total_votes: int


def compute_target_anchor(last_round: int, governance_period: int) -> int:
    if last_round < 0:
        raise ValueError("last_round must be non-negative")
    if governance_period <= 0:
        raise ValueError("governance_period must be greater than zero")
    return last_round - (last_round % governance_period)


def parse_positive_int(raw_value: object, field_name: str) -> int:
    if isinstance(raw_value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if isinstance(raw_value, int):
        value = raw_value
    elif isinstance(raw_value, str):
        normalized = raw_value.strip().replace("_", "")
        if not normalized:
            raise ValueError(f"{field_name} is required")
        try:
            value = int(normalized)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc
    else:
        raise ValueError(f"{field_name} is required")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return value


def parse_optional_positive_int(raw_value: object, field_name: str) -> int | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, str) and not raw_value.strip():
        return None
    return parse_positive_int(raw_value, field_name)


def decode_committee_id_b64(committee_id_b64: str) -> bytes:
    normalized = committee_id_b64.strip()
    if not normalized:
        raise ValueError("committeeId is required")

    try:
        decoded = base64.b64decode(normalized, validate=True)
    except binascii.Error as exc:
        raise ValueError("committeeId must be valid base64") from exc

    if len(decoded) != 32:
        raise ValueError("committeeId must decode to 32 bytes")
    return decoded


def resolve_testnet_committee_values(
    committee_id_b64: str,
    committee_members: str | int | None,
    committee_votes: str | int | None,
) -> tuple[bytes, int, int]:
    return (
        decode_committee_id_b64(committee_id_b64),
        parse_optional_positive_int(committee_members, "committee_members")
        or DEFAULT_TESTNET_COMMITTEE_MEMBERS,
        parse_optional_positive_int(committee_votes, "committee_votes")
        or DEFAULT_TESTNET_COMMITTEE_VOTES,
    )


def resolve_mainnet_committee_values(
    committee_id_b64: str,
    total_members: str | int,
    total_votes: str | int,
) -> tuple[bytes, int, int]:
    return (
        decode_committee_id_b64(committee_id_b64),
        parse_positive_int(total_members, "totalMembers"),
        parse_positive_int(total_votes, "totalVotes"),
    )


def get_committee_entry(
    index_document: Mapping[str, object], target_anchor: int
) -> CommitteeIndexEntry:
    committees = index_document.get("committees")
    if not isinstance(committees, Mapping):
        raise ValueError("committee index must contain a committees mapping")

    entry = committees.get(str(target_anchor))
    if not isinstance(entry, Mapping):
        raise LookupError(
            f"committee entry not found for target anchor {target_anchor}"
        )

    committee_id_b64 = entry.get("committeeId")
    if not isinstance(committee_id_b64, str) or not committee_id_b64.strip():
        raise ValueError("committeeId is missing from committee index entry")

    total_members = parse_positive_int(entry.get("totalMembers"), "totalMembers")
    total_votes = parse_positive_int(entry.get("totalVotes"), "totalVotes")

    return CommitteeIndexEntry(
        committee_id_b64=committee_id_b64,
        total_members=total_members,
        total_votes=total_votes,
    )
