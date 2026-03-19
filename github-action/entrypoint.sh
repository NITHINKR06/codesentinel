#!/bin/bash
set -e

API_URL="${API_URL:-http://localhost:8000}"
REPO_URL="${REPO_URL}"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-true}"
FAIL_THRESHOLD="${FAIL_THRESHOLD:-50}"

echo "╔══════════════════════════════════╗"
echo "║     CodeSentinel Security Scan    ║"
echo "╚══════════════════════════════════╝"
echo ""
echo "Repo: $REPO_URL"
echo "API:  $API_URL"
echo ""

# Start scan
echo "→ Starting scan..."
RESPONSE=$(curl -sf -X POST "$API_URL/api/scan" \
  -H "Content-Type: application/json" \
  -d "{\"github_url\": \"$REPO_URL\"}")

SCAN_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['scan_id'])")
echo "→ Scan ID: $SCAN_ID"

# Poll for completion
echo "→ Waiting for scan to complete..."
MAX_WAIT=300
WAITED=0
while true; do
  STATUS_RESP=$(curl -sf "$API_URL/api/scan/$SCAN_ID")
  STATUS=$(echo "$STATUS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")

  if [ "$STATUS" = "complete" ]; then
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "✗ Scan failed"
    exit 1
  fi

  if [ "$WAITED" -ge "$MAX_WAIT" ]; then
    echo "✗ Scan timed out after ${MAX_WAIT}s"
    exit 1
  fi

  sleep 5
  WAITED=$((WAITED + 5))
  echo "  ... $STATUS ($WAITED s)"
done

# Get report
REPORT=$(curl -sf "$API_URL/api/report/$SCAN_ID")

SCORE_BEFORE=$(echo "$REPORT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('score_before',0))")
SCORE_AFTER=$(echo "$REPORT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('score_after',0))")
CRITICAL=$(echo "$REPORT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('critical_count',0))")
TOTAL=$(echo "$REPORT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_findings',0))")

echo ""
echo "════════════════════════════════════"
echo "  Security Score:  $SCORE_BEFORE → $SCORE_AFTER / 100"
echo "  Total Findings:  $TOTAL"
echo "  Critical:        $CRITICAL"
echo "  Report:          $API_URL/scan/$SCAN_ID/report"
echo "════════════════════════════════════"

# Set GitHub Action outputs
echo "score_before=$SCORE_BEFORE" >> "$GITHUB_OUTPUT"
echo "score_after=$SCORE_AFTER" >> "$GITHUB_OUTPUT"
echo "critical_count=$CRITICAL" >> "$GITHUB_OUTPUT"
echo "report_url=$API_URL/scan/$SCAN_ID/report" >> "$GITHUB_OUTPUT"

# Post comment on PR if available
if [ -n "$GITHUB_EVENT_PATH" ] && [ -n "$GITHUB_TOKEN" ]; then
  PR_NUMBER=$(python3 -c "
import json, sys
with open('$GITHUB_EVENT_PATH') as f:
    e = json.load(f)
print(e.get('pull_request', {}).get('number', ''))
" 2>/dev/null || echo "")

  if [ -n "$PR_NUMBER" ]; then
    COMMENT="## 🛡️ CodeSentinel Security Report

| Metric | Value |
|--------|-------|
| Security Score | $SCORE_BEFORE → **$SCORE_AFTER** / 100 |
| Total Findings | $TOTAL |
| Critical | $CRITICAL |

[View full report]($API_URL/scan/$SCAN_ID/report)"

    curl -sf -X POST \
      "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments" \
      -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"body\": $(echo "$COMMENT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" \
      > /dev/null && echo "→ PR comment posted"
  fi
fi

# Fail conditions
if [ "$FAIL_ON_CRITICAL" = "true" ] && [ "$CRITICAL" -gt "0" ]; then
  echo ""
  echo "✗ Failing: $CRITICAL critical vulnerabilities found"
  exit 1
fi

if [ "$SCORE_AFTER" -lt "$FAIL_THRESHOLD" ]; then
  echo ""
  echo "✗ Failing: security score $SCORE_AFTER below threshold $FAIL_THRESHOLD"
  exit 1
fi

echo ""
echo "✓ Scan passed"
exit 0
