#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/tmp/workspace"
mkdir -p "$WORKSPACE"

if [[ "${ISSUE_SOURCE}" == "jira" ]]; then
  AUTH=$(printf '%s:%s' "$JIRA_EMAIL" "$JIRA_API_TOKEN" | base64 -w0)
  curl -sSf -H "Authorization: Basic $AUTH" \
    "https://${JIRA_HOST}/rest/api/3/issue/${ISSUE_KEY}" \
    > "$WORKSPACE/my-input.json"

elif [[ "${ISSUE_SOURCE}" == "github" ]]; then
  gh issue view "$ISSUE_KEY" --repo "$REPO_FULL_NAME" \
    --json number,title,body,labels,comments \
    > "$WORKSPACE/my-input.json"
fi

echo "Pre-script complete."
