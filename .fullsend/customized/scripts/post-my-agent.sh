#!/usr/bin/env bash
set -euo pipefail

RESULT_FILE=""
for dir in iteration-*/output; do
  if [[ -f "${dir}/agent-result.json" ]]; then
    RESULT_FILE="${dir}/agent-result.json"
  fi
done

if [[ -z "${RESULT_FILE}" ]]; then
  echo "ERROR: agent-result.json not found"
  exit 1
fi

# Validate JSON structure before extracting fields.
# The agent runs in an untrusted sandbox — treat its output as untrusted input.
if ! jq empty "${RESULT_FILE}" 2>/dev/null; then
  echo "ERROR: agent-result.json is not valid JSON"
  exit 1
fi

STATUS=$(jq -r '.status // ""' "${RESULT_FILE}")
COMMENT=$(jq -r '.comment // ""' "${RESULT_FILE}")

# Validate status against known values before acting on it.
case "${STATUS}" in
  complete)
    echo "Agent completed successfully"
    ;;
  needs_input)
    echo "Agent needs more information"
    ;;
  *)
    echo "ERROR: Unknown or missing status '${STATUS}'"
    exit 1
    ;;
esac
