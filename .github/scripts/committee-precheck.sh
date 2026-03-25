#!/usr/bin/env bash

set -euo pipefail

mode="${COMMITTEE_PRECHECK_MODE:?COMMITTEE_PRECHECK_MODE is required}"
network="${COMMITTEE_NETWORK:?COMMITTEE_NETWORK is required}"
api_base="${ALGOD_API_BASE:?ALGOD_API_BASE is required}"
app_id="${XGOV_REGISTRY_ID:?XGOV_REGISTRY_ID is required}"
index_url="${COMMITTEE_INDEX_URL:?COMMITTEE_INDEX_URL is required}"
tolerance_rounds="${COMMITTEE_TOLERANCE_ROUNDS:-5000}"
force_publish="${COMMITTEE_FORCE_PUBLISH:-false}"
force_alert="${COMMITTEE_FORCE_ALERT:-false}"

normalize_positive_int() {
  local raw_value="$1"
  local field_name="$2"
  local normalized="${raw_value//_/}"

  if [[ -z "${normalized}" ]]; then
    echo "${field_name} is required" >&2
    return 1
  fi
  if [[ ! "${normalized}" =~ ^[0-9]+$ ]]; then
    echo "${field_name} must be a positive integer" >&2
    return 1
  fi
  if [[ "${normalized}" -le 0 ]]; then
    echo "${field_name} must be greater than zero" >&2
    return 1
  fi

  printf '%s\n' "${normalized}"
}

status_json="$(curl -fsS "${api_base}/v2/status")"
app_json="$(curl -fsS "${api_base}/v2/applications/${app_id}")"
index_json="$(curl -fsS "${index_url}")"

last_round="$(jq -r '."last-round"' <<<"${status_json}")"
committee_last_anchor="$(jq -r '
  .params["global-state"]
  | map(select(.key == "Y29tbWl0dGVlX2xhc3RfYW5jaG9y"))
  | .[0].value.uint
' <<<"${app_json}")"
governance_period="$(jq -r '
  .params["global-state"]
  | map(select(.key == "Z292ZXJuYW5jZV9wZXJpb2Q="))
  | .[0].value.uint
' <<<"${app_json}")"

governance_period="$(normalize_positive_int "${governance_period}" "governance_period")"

target_anchor=$((last_round - (last_round % governance_period)))
lag_rounds=$((last_round - target_anchor))

should_publish="false"
alert_required="false"
close_issue="false"
reason="unknown"
committee_id_b64=""
index_total_members=""
index_total_votes=""
effective_committee_members=""
effective_committee_votes=""
members_source="index"
votes_source="index"
issue_title="Committee update overdue for anchor ${target_anchor}"
issue_body=""

entry_json="$(jq -c --arg key "${target_anchor}" '.committees[$key] // empty' <<<"${index_json}")"
if [[ -n "${entry_json}" ]]; then
  committee_id_b64="$(jq -r '.committeeId // ""' <<<"${entry_json}")"
  index_total_members="$(jq -r '.totalMembers // ""' <<<"${entry_json}")"
  index_total_votes="$(jq -r '.totalVotes // ""' <<<"${entry_json}")"
fi

if [[ "${mode}" == "publisher" ]]; then
  if [[ "${target_anchor}" -eq "${committee_last_anchor}" && "${force_publish}" != "true" ]]; then
    reason="registry_up_to_date"
  elif [[ -z "${entry_json}" ]]; then
    reason="committee_entry_not_ready"
  elif [[ -z "${committee_id_b64}" ]]; then
    reason="invalid_committee_id"
  elif [[ "${network}" == "mainnet" ]]; then
    # This condition could be relaxed to allow empty committees (no members, no votes)
    if ! effective_committee_members="$(normalize_positive_int "${index_total_members}" "totalMembers")"; then
      reason="invalid_total_members"
    elif ! effective_committee_votes="$(normalize_positive_int "${index_total_votes}" "totalVotes")"; then
      reason="invalid_total_votes"
    else
      should_publish="true"
      reason="ready_to_publish"
    fi
  else
    raw_committee_members="${COMMITTEE_INPUT_MEMBERS:-}"
    raw_committee_votes="${COMMITTEE_INPUT_VOTES:-}"

    if [[ -n "${raw_committee_members}" ]]; then
      if ! effective_committee_members="$(normalize_positive_int "${raw_committee_members}" "committee_members")"; then
        reason="invalid_committee_members_override"
      else
        members_source="manual"
      fi
    else
      effective_committee_members="30"
      members_source="default"
    fi

    if [[ "${reason}" == "unknown" ]]; then
      if [[ -n "${raw_committee_votes}" ]]; then
        if ! effective_committee_votes="$(normalize_positive_int "${raw_committee_votes}" "committee_votes")"; then
          reason="invalid_committee_votes_override"
        else
          votes_source="manual"
        fi
      else
        effective_committee_votes="9000000"
        votes_source="default"
      fi
    fi

    if [[ "${reason}" == "unknown" ]]; then
      should_publish="true"
      reason="ready_to_publish"
    fi
  fi
elif [[ "${mode}" == "watchdog" ]]; then
  if [[ "${force_alert}" == "true" ]]; then
    alert_required="true"
    reason="forced"
    issue_body=$(
      cat <<EOF
Committee update alert was forced manually (for testing).

- Network: ${network}
- Last round: ${last_round}
- Target anchor: ${target_anchor}
- Current committee_last_anchor: ${committee_last_anchor}
- Lag rounds since target anchor: ${lag_rounds}
EOF
    )
  elif [[ "${target_anchor}" -gt "${committee_last_anchor}" ]]; then
    if [[ "${last_round}" -ge $((target_anchor + tolerance_rounds)) ]]; then
      alert_required="true"
      reason="overdue"
      issue_body=$(
        cat <<EOF
Committee update is overdue.

- Network: ${network}
- Last round: ${last_round}
- Target anchor: ${target_anchor}
- Current committee_last_anchor: ${committee_last_anchor}
- Lag rounds since target anchor: ${lag_rounds}
- Tolerance rounds: ${tolerance_rounds}
EOF
      )
    else
      reason="within_tolerance"
    fi
  elif [[ "${committee_last_anchor}" -eq "${target_anchor}" && "${target_anchor}" -gt 0 ]]; then
    close_issue="true"
    reason="up_to_date"
  else
    reason="before_next_anchor"
  fi
else
  echo "Unsupported COMMITTEE_PRECHECK_MODE: ${mode}" >&2
  exit 1
fi

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "network=${network}"
    echo "last_round=${last_round}"
    echo "committee_last_anchor=${committee_last_anchor}"
    echo "governance_period=${governance_period}"
    echo "target_anchor=${target_anchor}"
    echo "lag_rounds=${lag_rounds}"
    echo "should_publish=${should_publish}"
    echo "alert_required=${alert_required}"
    echo "close_issue=${close_issue}"
    echo "reason=${reason}"
    echo "committee_id_b64=${committee_id_b64}"
    echo "index_total_members=${index_total_members}"
    echo "index_total_votes=${index_total_votes}"
    echo "effective_committee_members=${effective_committee_members}"
    echo "effective_committee_votes=${effective_committee_votes}"
    echo "members_source=${members_source}"
    echo "votes_source=${votes_source}"
    echo "issue_title=${issue_title}"
    echo "issue_body<<EOF"
    printf '%s\n' "${issue_body}"
    echo "EOF"
  } >>"${GITHUB_OUTPUT}"
fi

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    echo "## Committee precheck"
    echo
    echo "- Mode: ${mode}"
    echo "- Network: ${network}"
    echo "- Force publish: ${force_publish}"
    echo "- Force alert: ${force_alert}"
    echo "- Last round: ${last_round}"
    echo "- committee_last_anchor: ${committee_last_anchor}"
    echo "- governance_period: ${governance_period}"
    echo "- Target anchor: ${target_anchor}"
    echo "- Lag rounds from target anchor: ${lag_rounds}"
    echo "- Result: ${reason}"
    if [[ -n "${committee_id_b64}" ]]; then
      echo "- committeeId: ${committee_id_b64}"
    fi
    if [[ -n "${index_total_members}" ]]; then
      echo "- Index totalMembers: ${index_total_members}"
    fi
    if [[ -n "${index_total_votes}" ]]; then
      echo "- Index totalVotes: ${index_total_votes}"
    fi
    if [[ -n "${effective_committee_members}" ]]; then
      echo "- Effective committee_members: ${effective_committee_members} (${members_source})"
    fi
    if [[ -n "${effective_committee_votes}" ]]; then
      echo "- Effective committee_votes: ${effective_committee_votes} (${votes_source})"
    fi
  } >>"${GITHUB_STEP_SUMMARY}"
fi
