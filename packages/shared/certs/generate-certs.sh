#!/usr/bin/env bash
set -euo pipefail

CERTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ES_VERSION="${ES_VERSION:-8.17.4}"
NODE1_IP="${ES_NODE1_IP:-10.10.188.8}"
NODE2_IP="${ES_NODE2_IP:-10.10.191.16}"
NODE3_IP="${ES_NODE3_IP:-10.10.191.17}"

echo "==> TLS 인증서 생성 (Elasticsearch ${ES_VERSION})"

# 이전 실행 잔여 파일 정리
rm -f "${CERTS_DIR}"/*.p12 "${CERTS_DIR}"/*.zip \
       "${CERTS_DIR}"/*.crt "${CERTS_DIR}"/*.key
rm -rf "${CERTS_DIR}"/ca "${CERTS_DIR}"/node1 \
       "${CERTS_DIR}"/node2 "${CERTS_DIR}"/node3

docker run --rm \
  --user root \
  -v "${CERTS_DIR}:/certs" \
  "docker.elastic.co/elasticsearch/elasticsearch:${ES_VERSION}" \
  bash -c "
    set -euo pipefail

    # CA 생성 (PEM → ZIP)
    bin/elasticsearch-certutil ca \
      --out /certs/ca.zip --pass '' --pem
    unzip -o /certs/ca.zip -d /certs
    cp /certs/ca/ca.crt /certs/ca.crt

    # node1
    bin/elasticsearch-certutil cert \
      --ca-cert /certs/ca/ca.crt --ca-key /certs/ca/ca.key \
      --name node1 --dns node1 --ip ${NODE1_IP} \
      --out /certs/node1.zip --pass '' --pem
    unzip -o /certs/node1.zip -d /certs
    mv /certs/node1/node1.crt /certs/node1.crt
    mv /certs/node1/node1.key /certs/node1.key

    # node2
    bin/elasticsearch-certutil cert \
      --ca-cert /certs/ca/ca.crt --ca-key /certs/ca/ca.key \
      --name node2 --dns node2 --ip ${NODE2_IP} \
      --out /certs/node2.zip --pass '' --pem
    unzip -o /certs/node2.zip -d /certs
    mv /certs/node2/node2.crt /certs/node2.crt
    mv /certs/node2/node2.key /certs/node2.key

    # node3
    bin/elasticsearch-certutil cert \
      --ca-cert /certs/ca/ca.crt --ca-key /certs/ca/ca.key \
      --name node3 --dns node3 --ip ${NODE3_IP} \
      --out /certs/node3.zip --pass '' --pem
    unzip -o /certs/node3.zip -d /certs
    mv /certs/node3/node3.crt /certs/node3.crt
    mv /certs/node3/node3.key /certs/node3.key

    # 권한 설정 (ES 컨테이너는 UID 1000으로 실행되므로 key도 644로 설정)
    chmod 644 /certs/*.crt /certs/*.key
    chmod 644 /certs/ca/ca.key
  "

echo "==> 인증서 생성 완료: ${CERTS_DIR}"
ls -la "${CERTS_DIR}"
