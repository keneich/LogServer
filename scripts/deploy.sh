#!/usr/bin/env bash
set -euo pipefail

# 배포 순서: node1 → node2/3 (병렬) → buffer-b → buffer-a
# 에이전트는 별도 수동 배포

echo "==> [1/4] TLS 인증서 생성"
pnpm --filter shared run gen-certs

echo "==> [2/4] Elasticsearch node1 (Master + Kibana) 기동"
pnpm run up:node1
sleep 30

echo "==> [3/4] Elasticsearch node2, node3 (Data) 병렬 기동"
pnpm run up:node2 & pnpm run up:node3 &
wait
sleep 20

echo "==> [4/4] ES 초기설정 (ILM 정책, 인덱스 템플릿)"
pnpm --filter shared run setup

echo "==> [5/5] Buffer 서버 기동 (ZoneB → ZoneA 순)"
pnpm run up:buffer-b
pnpm run up:buffer-a

echo ""
echo "==> 전체 배포 완료. 헬스 체크:"
node scripts/health-check.mjs
