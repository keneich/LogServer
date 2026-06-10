#!/usr/bin/env bash
set -euo pipefail

CERTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ES_VERSION="${ES_VERSION:-8.17.4}"
NODE1_IP="${ES_NODE1_IP:-10.10.188.8}"
NODE2_IP="${ES_NODE2_IP:-10.10.191.16}"
NODE3_IP="${ES_NODE3_IP:-10.10.191.17}"

echo "==> TLS 인증서 생성 (Elasticsearch ${ES_VERSION})"

# 임시 컨테이너로 elasticsearch-certutil 실행
docker run --rm \
  -v "${CERTS_DIR}:/certs" \
  "docker.elastic.co/elasticsearch/elasticsearch:${ES_VERSION}" \
  bash -c "
    bin/elasticsearch-certutil ca \
      --out /certs/ca.p12 --pass '' --pem &&
    bin/elasticsearch-certutil cert \
      --ca /certs/ca.p12 --ca-pass '' \
      --name node1 --dns node1 --ip ${NODE1_IP} \
      --out /certs/node1.p12 --pass '' --pem &&
    bin/elasticsearch-certutil cert \
      --ca /certs/ca.p12 --ca-pass '' \
      --name node2 --dns node2 --ip ${NODE2_IP} \
      --out /certs/node2.p12 --pass '' --pem &&
    bin/elasticsearch-certutil cert \
      --ca /certs/ca.p12 --ca-pass '' \
      --name node3 --dns node3 --ip ${NODE3_IP} \
      --out /certs/node3.p12 --pass '' --pem
  "

echo "==> 인증서 생성 완료: ${CERTS_DIR}"
ls -la "${CERTS_DIR}"
