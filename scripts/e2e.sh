#!/usr/bin/env bash
set -euo pipefail

API="http://localhost:8000"
KEY="${API_KEY:-change-me-super-secret}"

echo "1) Health..."
curl -fsS "$API/api/v1/health" | python -m json.tool >/dev/null
echo "   OK"

echo "2) Create monitor..."
MID=$(curl -fsS -X POST "$API/api/v1/monitors" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d '{"name":"E2E","url":"https://httpbin.org/status/200","expected_status":200,"interval_sec":60,"timeout_ms":3000,"is_active":true}' \
  | python -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "   monitor_id=$MID"

echo "3) Force failure (500) and check twice -> should OPEN incident + Slack..."
curl -fsS -X PATCH "$API/api/v1/monitors/$MID" \
  -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
  -d '{"url":"https://httpbin.org/status/500"}' >/dev/null

curl -fsS -X POST "$API/api/v1/monitors/$MID/check-now" -H "X-API-Key: $KEY" >/dev/null
curl -fsS -X POST "$API/api/v1/monitors/$MID/check-now" -H "X-API-Key: $KEY" >/dev/null

echo "4) Confirm OPEN incident exists for this monitor..."
curl -fsS "$API/api/v1/monitors/$MID/incidents" -H "X-API-Key: $KEY" \
| python -c 'import sys,json; d=json.load(sys.stdin); open_=[x for x in d if x.get("status")=="OPEN"]; print("open_for_monitor=", len(open_)); assert len(open_)>=1, d'
echo "   OK"

echo "5) Fix (200) and check twice -> should RESOLVE incident + Slack..."
curl -fsS -X PATCH "$API/api/v1/monitors/$MID" \
  -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
  -d '{"url":"https://httpbin.org/status/200"}' >/dev/null

curl -fsS -X POST "$API/api/v1/monitors/$MID/check-now" -H "X-API-Key: $KEY" >/dev/null
curl -fsS -X POST "$API/api/v1/monitors/$MID/check-now" -H "X-API-Key: $KEY" >/dev/null

echo "6) Confirm RESOLVED incident exists for this monitor..."
curl -fsS "$API/api/v1/monitors/$MID/incidents" -H "X-API-Key: $KEY" \
| python -c 'import sys,json; d=json.load(sys.stdin); res=[x for x in d if x.get("status")=="RESOLVED"]; print("resolved_for_monitor=", len(res)); assert len(res)>=1, d'
echo "   OK"

echo "✅ E2E PASS (scoped to this monitor_id only)"
