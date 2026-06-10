# CLAUDE.md

이 파일은 Claude Code가 이 프로젝트에서 작업할 때 참조하는 컨텍스트 문서입니다.

---

## 프로젝트 개요

**LogServer** — ELK 스택 기반 중앙화 로그 수집·모니터링 시스템

운영 서버 69대(Linux RHEL 60대, Windows 2022 9대)의 시스템·보안·인증 로그를 수집하여
1년간 보존하고 Kibana 대시보드로 실시간 모니터링한다.

---

## 레포지토리 구조

pnpm workspace 기반 모노레포. 모든 패키지는 `packages/` 하위에 있다.

```
packages/
├── buffer-a/        # ZoneA 버퍼 서버 — Redis 7.4 + Logstash 8.17.4
├── buffer-b/        # ZoneB 버퍼 서버 — Redis 7.4 + Logstash 8.17.4
├── es-node1/        # Elasticsearch 8.17.4 Master + Kibana 8.17.4
├── es-node2/        # Elasticsearch 8.17.4 Data Node (SSD + HDD 멀티패스)
├── es-node3/        # Elasticsearch 8.17.4 Data Node (SSD + HDD 멀티패스)
├── agent-linux/     # Filebeat 8.17.4 — RHEL 배포 설정 및 설치 스크립트
├── agent-windows/   # Winlogbeat 8.17.4 — Windows 2022 배포 설정 및 PowerShell 스크립트
└── shared/          # 공통 리소스 (TLS 인증서, ILM 정책, 인덱스 템플릿, ES 초기 설정)
scripts/
├── deploy.sh        # 전체 순서 자동 배포
└── health-check.mjs # 클러스터·Redis 헬스체크
```

---

## 버전 고정 규칙

> 버전을 임의로 올리거나 최신 버전으로 교체하지 말 것.

| 컴포넌트 | 고정 버전 | 이유 |
|----------|-----------|------|
| Elasticsearch / Logstash / Kibana / Beats | `8.17.4` | 9.x는 운영 검증 미완료, 8.x 안정화 버전 사용 |
| Redis | `7.4` (alpine) | 7.2.x EOL 대체, 7.8+ 검증 부족 |
| Docker Engine | `27.x` | Ubuntu 24.04 검증 완료 버전 |
| Docker Compose | `v2.29.x` | Compose v5 spec 이전 안정 버전 |
| Node.js | `>=20` | package.json engines 필드 참조 |
| pnpm | `>=9` | package.json engines 필드 참조 |

**Elastic Stack 버전 혼용 금지**: ES · Kibana · Logstash · Filebeat · Winlogbeat는 반드시 동일 버전(`8.17.4`)이어야 한다.

---

## 주요 명령어

### 서비스 기동·중단

```bash
pnpm run up:all          # 전체 기동
pnpm run down:all        # 전체 중단
pnpm run ps:all          # 전체 컨테이너 상태
pnpm run health          # 클러스터 + Redis 헬스체크
```

### 개별 패키지 조작

```bash
# 특정 패키지 명령 실행 패턴
pnpm --filter <package-name> run <script>

# 예시
pnpm --filter es-node1  run up
pnpm --filter buffer-b  run logs:logstash
pnpm --filter es-node1  run logs:kibana
```

### 초기 설정

```bash
pnpm --filter shared run gen-certs      # TLS 인증서 생성
pnpm run setup                          # ILM 정책 + 인덱스 템플릿 ES에 적용
pnpm --filter shared run apply-ilm      # ILM 정책만 재적용
pnpm --filter shared run apply-template # 인덱스 템플릿만 재적용
```

### 에이전트 배포

```bash
pnpm run deploy:agent:linux    # Filebeat 설치 스크립트 실행
pnpm run deploy:agent:windows  # Winlogbeat PowerShell 설치
```

---

## 배포 순서 (반드시 지킬 것)

서비스 기동 순서가 잘못되면 클러스터 조인에 실패한다.

```
1. pnpm --filter shared run gen-certs   ← TLS 인증서 먼저
2. pnpm run up:node1                    ← Master 노드 먼저 (30초 대기)
3. pnpm run up:node2 && pnpm run up:node3
4. pnpm run setup                       ← ILM + 템플릿
5. pnpm run up:buffer-b                 ← ZoneB 버퍼
6. pnpm run up:buffer-a                 ← ZoneA 버퍼
7. 에이전트 배포 (agent-linux, agent-windows)
```

---

## 환경변수 처리 규칙

- 모든 패키지는 `.env.example` 을 제공한다. 실제 값은 `.env` 파일에 넣는다.
- `.env` 파일은 `.gitignore` 에 등록되어 있어 절대 커밋하지 않는다.
- 패스워드·IP·인증서 등 민감정보는 코드에 하드코딩하지 않는다.
- `docker-compose.yml` 에서 환경변수는 `${VAR_NAME}` 형식으로 참조한다.

### 반드시 변경해야 할 변수

```
ELASTIC_PASSWORD         # elastic 계정 패스워드
REDIS_PASSWORD           # Redis 인증 패스워드
KIBANA_ENCRYPTION_KEY    # 32자 이상 랜덤 문자열
ES_NODE1_IP / NODE2_IP / NODE3_IP   # 실제 서버 IP
BUFFER_A_IP / BUFFER_B_IP           # 실제 버퍼 서버 IP
```

---

## 파일별 역할 및 수정 지침

### `packages/buffer-*/logstash/pipeline/logstash.conf`

Logstash 파이프라인 정의. buffer-a와 buffer-b는 동일한 파이프라인을 사용한다.
수정 시 두 파일을 모두 업데이트해야 한다.

- **input**: Redis에서 `filebeat` 키(Linux)와 `winlogbeat` 키(Windows)를 별도 읽음
- **filter**: `log_category` 필드로 로그 종류 구분 (syslog · auth · audit · windows_system · windows_security)
- **output**: ILM 롤오버 별칭 `logs-{log_category}` 로 ES에 전송

### `packages/buffer-*/logstash/config/logstash.yml`

- buffer-a: `pipeline.workers: 4`, `queue.max_bytes: 4gb`
- buffer-b: `pipeline.workers: 8`, `queue.max_bytes: 8gb` (ZoneB 부하가 더 높음)
- `queue.type: persisted` — 변경하지 말 것 (유실 방지 필수)

### `packages/es-node1/elasticsearch/config/elasticsearch.yml`

`node.roles: [master]` — 데이터 저장 없음. 역할 변경 금지.

### `packages/es-node2/elasticsearch/config/elasticsearch.yml`
### `packages/es-node3/elasticsearch/config/elasticsearch.yml`

`node.roles: [data, data_hot, data_warm, data_cold, data_content, ingest]`
`path.data: [/data/ssd, /data/hdd]` — SSD(Hot·Warm)와 HDD(Cold) 멀티패스

### `packages/shared/ilm/policy.json`

ILM 4단계 정책 정의.

| 단계 | 기간 | 주요 액션 |
|------|------|-----------|
| hot | 0~30일 | rollover (30d / 50gb) |
| warm | 30~90일 | force_merge(1), shrink(1), readonly |
| cold | 90~365일 | freeze |
| delete | 365일+ | delete |

### `packages/shared/index-templates/logs-template.json`

`logs-*` 패턴 인덱스에 적용. `number_of_shards: 2`, `number_of_replicas: 1`.
필드 매핑 변경 시 기존 인덱스에는 소급 적용되지 않으므로 주의.

### `packages/agent-linux/filebeat.yml`

Redis output 사용. `key: "filebeat"` 고정.
ZoneA 서버에서는 `ZONE=ZoneA`, ZoneB 서버에서는 `ZONE=ZoneB` 로 install.sh 실행.

### `packages/agent-windows/winlogbeat.yml`

Security Event Log에서 수집할 Event ID가 명시적으로 지정되어 있음 (4624, 4625 등).
Event ID 추가·제거 시 Winlogbeat 서비스 재시작 필요.

---

## TLS 인증서

`packages/shared/certs/` 에 저장. `.gitignore` 에 등록되어 있어 Git에 포함되지 않는다.

```
ca.crt           # CA 인증서 (모든 컨테이너에 마운트)
node1.crt/.key   # es-node1 전용
node2.crt/.key   # es-node2 전용
node3.crt/.key   # es-node3 전용
```

`generate-certs.sh` 는 Docker 컨테이너를 임시 실행하여 `elasticsearch-certutil` 로 생성한다.
인증서 재생성 시 클러스터 전체 재시작 필요.

---

## 네트워크 구성

| Zone | IP 대역 | 서버 |
|------|---------|------|
| ZoneA | 10.10.184.0/24 | Linux RHEL 10대, Windows 2대, Buffer-A |
| ZoneB | 10.10.188.0/24 | Linux RHEL 50대, Windows 2022 7대, Buffer-B, ES node1·2·3 |

### 필수 개방 포트

| 포트 | 서비스 | 방향 |
|------|--------|------|
| 6379 | Redis | Beats → Buffer 서버 |
| 9200 | Elasticsearch HTTP | Logstash → ES, Kibana → ES |
| 9300 | Elasticsearch Transport | ES 노드 간 클러스터 통신 |
| 5601 | Kibana | 관리자 브라우저 → node1 |
| 9600 | Logstash Monitoring API | 내부 모니터링 |

---

## 코드·설정 컨벤션

### docker-compose.yml

- `version:` 키 사용하지 않는다 (Compose v2에서 deprecated).
- 이미지 태그는 반드시 명시적 버전(`8.17.4`)으로 고정. `latest` 사용 금지.
- 환경변수는 `environment:` 블록에서 `${VAR}` 형식으로만 참조.
- healthcheck는 모든 주요 서비스에 정의한다.
- `restart: unless-stopped` 를 기본값으로 사용.

### Logstash grok 패턴

- 파싱 실패 시 `tag_on_failure` 를 반드시 지정한다.
- `log_category` 필드는 모든 이벤트에 존재해야 한다 (ES 인덱스 라우팅에 사용됨).
- `@timestamp` 는 원본 로그 시각으로 덮어쓴다 (수집 시각이 아님).
- 한국 시간 처리: `date` 필터에 `timezone => "Asia/Seoul"` 명시.

### 쉘 스크립트

- 모든 쉘 스크립트 첫 줄: `#!/usr/bin/env bash`
- `set -euo pipefail` 을 두 번째 줄에 반드시 추가.
- 환경변수는 기본값과 함께 선언: `VAR="${VAR:-default}"`.

### PowerShell 스크립트

- `#Requires -RunAsAdministrator` 를 첫 줄에 추가.
- `$ErrorActionPreference = "Stop"` 을 초반에 설정.

---

## 커밋 메시지 규칙

Conventional Commits 형식 사용.

```
<type>(<scope>): <subject>
```

| type | 사용 시점 |
|------|-----------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `conf` | 설정 파일 변경 (docker-compose, logstash.conf, elasticsearch.yml 등) |
| `docs` | 문서 수정 |
| `refactor` | 기능 변경 없는 리팩터링 |
| `chore` | 빌드·패키지 관련 |

scope 예시: `pipeline`, `es-node1`, `buffer-b`, `agent-linux`, `ilm`, `certs`, `kibana`

---

## 절대 하지 말아야 할 것

- `.env` 파일을 Git에 커밋하지 않는다.
- `packages/shared/certs/` 의 인증서 파일을 Git에 커밋하지 않는다.
- ES · Kibana · Logstash · Beats 버전을 서로 다르게 설정하지 않는다.
- node1의 `node.roles` 에 `data` 를 추가하지 않는다 (Master 전용).
- Docker 이미지에 `latest` 태그를 사용하지 않는다.
- Logstash `queue.type: persisted` 를 `memory` 로 변경하지 않는다.
- ES JVM Heap을 32 GB 초과로 설정하지 않는다 (Compressed OOPs 비활성화됨).
- node2·node3 보다 node1을 나중에 기동하지 않는다 (클러스터 조인 실패).

---

## 참조 문서

| 파일 | 내용 |
|------|------|
| `README.md` | 전체 설치·운영 가이드 |
| `README01.md` | 아키텍처·서버 스펙·기술 스택·ILM 정책 상세 |
| `WBS.md` | 2개월 프로젝트 WBS (77개 태스크) |
| `.env.example` | 전체 환경변수 목록 |
