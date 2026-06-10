#!/usr/bin/env bash
set -euo pipefail

ES_HOST="${ES_HOST:-https://10.10.188.8:9200}"
ES_USER="${ES_USER:-elastic}"
ES_PASSWORD="${ES_PASSWORD:-changeme}"
CERTS_DIR="$(cd "$(dirname "$0")/../certs" && pwd)"
SHARED_DIR="$(cd "$(dirname "$0")/.." && pwd)"

CURL="curl -sf --cacert ${CERTS_DIR}/ca.crt -u ${ES_USER}:${ES_PASSWORD}"

echo "==> Elasticsearch 클러스터 상태 확인"
$CURL "${ES_HOST}/_cluster/health?pretty"

echo ""
echo "==> ILM 정책 적용"
$CURL -X PUT "${ES_HOST}/_ilm/policy/logs-ilm-policy" \
  -H "Content-Type: application/json" \
  -d @"${SHARED_DIR}/ilm/policy.json"

echo ""
echo "==> 인덱스 템플릿 적용"
$CURL -X PUT "${ES_HOST}/_index_template/logs-template" \
  -H "Content-Type: application/json" \
  -d @"${SHARED_DIR}/index-templates/logs-template.json"

echo ""
echo "==> 초기 인덱스 별칭 생성 (롤오버용)"
for category in syslog auth audit windows_system windows_security; do
  $CURL -X PUT "${ES_HOST}/logs-${category}-000001" \
    -H "Content-Type: application/json" \
    -d "{
      \"aliases\": {
        \"logs-${category}\": { \"is_write_index\": true }
      }
    }" && echo "  [OK] logs-${category}"
done

echo ""
echo "==> 설정 완료"
