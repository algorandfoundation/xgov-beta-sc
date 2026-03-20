import pytest

from smart_contracts.xgov_registry.committee_publish import (
    DEFAULT_TESTNET_COMMITTEE_MEMBERS,
    DEFAULT_TESTNET_COMMITTEE_VOTES,
    compute_target_anchor,
    decode_committee_id_b64,
    get_committee_entry,
    parse_positive_int,
    resolve_mainnet_committee_values,
    resolve_testnet_committee_values,
)

VALID_COMMITTEE_ID_B64 = "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE="


def test_compute_target_anchor_before_boundary() -> None:
    assert compute_target_anchor(59_440_079, 1_000_000) == 59_000_000


def test_compute_target_anchor_exact_boundary() -> None:
    assert compute_target_anchor(60_000_000, 1_000_000) == 60_000_000


def test_compute_target_anchor_uses_configured_governance_period() -> None:
    assert compute_target_anchor(59_440_079, 500_000) == 59_000_000


def test_compute_target_anchor_rejects_negative_round() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        compute_target_anchor(-1, 1_000_000)


def test_compute_target_anchor_rejects_non_positive_governance_period() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        compute_target_anchor(60_000_000, 0)


def test_get_committee_entry_success() -> None:
    entry = get_committee_entry(
        {
            "committees": {
                "60000000": {
                    "committeeId": VALID_COMMITTEE_ID_B64,
                    "totalMembers": 162,
                    "totalVotes": 508887,
                }
            }
        },
        60_000_000,
    )

    assert entry.committee_id_b64 == VALID_COMMITTEE_ID_B64
    assert entry.total_members == 162
    assert entry.total_votes == 508887


def test_get_committee_entry_missing_target_anchor() -> None:
    with pytest.raises(LookupError, match="target anchor 60000000"):
        get_committee_entry({"committees": {}}, 60_000_000)


def test_get_committee_entry_invalid_committee_id() -> None:
    with pytest.raises(ValueError, match="committeeId is missing"):
        get_committee_entry(
            {
                "committees": {
                    "60000000": {
                        "committeeId": "",
                        "totalMembers": 10,
                        "totalVotes": 20,
                    }
                }
            },
            60_000_000,
        )


def test_parse_positive_int_accepts_underscored_string() -> None:
    assert parse_positive_int("9_000_000", "committee_votes") == 9_000_000


@pytest.mark.parametrize("raw_value", ["", "0", "-1", "abc"])
def test_parse_positive_int_rejects_invalid_values(raw_value: str) -> None:
    with pytest.raises(ValueError):
        parse_positive_int(raw_value, "committee_members")


def test_decode_committee_id_b64_rejects_wrong_size() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        decode_committee_id_b64("AQID")


def test_resolve_mainnet_committee_values_success() -> None:
    committee_id, members, votes = resolve_mainnet_committee_values(
        VALID_COMMITTEE_ID_B64, "162", "508_887"
    )

    assert len(committee_id) == 32
    assert members == 162
    assert votes == 508887


def test_resolve_testnet_committee_values_defaults() -> None:
    committee_id, members, votes = resolve_testnet_committee_values(
        VALID_COMMITTEE_ID_B64, "", None
    )

    assert len(committee_id) == 32
    assert members == DEFAULT_TESTNET_COMMITTEE_MEMBERS
    assert votes == DEFAULT_TESTNET_COMMITTEE_VOTES


def test_resolve_testnet_committee_values_members_override_only() -> None:
    _, members, votes = resolve_testnet_committee_values(
        VALID_COMMITTEE_ID_B64, "45", ""
    )

    assert members == 45
    assert votes == DEFAULT_TESTNET_COMMITTEE_VOTES


def test_resolve_testnet_committee_values_votes_override_only() -> None:
    _, members, votes = resolve_testnet_committee_values(
        VALID_COMMITTEE_ID_B64, "", "12_345"
    )

    assert members == DEFAULT_TESTNET_COMMITTEE_MEMBERS
    assert votes == 12345


def test_resolve_testnet_committee_values_both_overridden() -> None:
    _, members, votes = resolve_testnet_committee_values(
        VALID_COMMITTEE_ID_B64, "55", "12000000"
    )

    assert members == 55
    assert votes == 12000000


@pytest.mark.parametrize(
    ("committee_members", "committee_votes"),
    [("0", ""), ("-1", ""), ("", "0"), ("", "-2"), ("abc", ""), ("", "bad")],
)
def test_resolve_testnet_committee_values_reject_invalid_overrides(
    committee_members: str,
    committee_votes: str,
) -> None:
    with pytest.raises(ValueError):
        resolve_testnet_committee_values(
            VALID_COMMITTEE_ID_B64, committee_members, committee_votes
        )
