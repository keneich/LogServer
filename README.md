<div align="center">

# LogServer

**ELK 스택 기반 중앙화 로그 수집·모니터링 시스템**

[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.17.4-005571?style=flat-square&logo=elasticsearch&logoColor=white)](https://www.elastic.co/elasticsearch/)
[![Logstash](https://img.shields.io/badge/Logstash-8.17.4-005571?style=flat-square&logo=logstash&logoColor=white)](https://www.elastic.co/logstash/)
[![Kibana](https://img.shields.io/badge/Kibana-8.17.4-005571?style=flat-square&logo=kibana&logoColor=white)](https://www.elastic.co/kibana/)
[![Redis](https://img.shields.io/badge/Redis-7.4-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-27.x-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420?style=flat-square&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<br/>

운영 서버 **69대** (Linux RHEL · Windows 2022) 의 시스템·보안·인증 로그를  
중앙에서 수집하고 **1년간 보존**하며 실시간으로 모니터링합니다.

[시작하기](#-빠른-시작) · [문서](#-문서) · [기여하기](#-컨트리뷰션-가이드) · [이슈 제보](../../issues)

</div>

---

## 목차

- [프로젝트 개요](#-프로젝트-개요)
- [아키텍처](#-아키텍처)
- [아키텍처 설계 근거](#-아키텍처-설계-근거)
- [기술 스택](#-기술-스택)
- [사전 요구사항](#-사전-요구사항)
- [빠른 시작](#-빠른-시작)
- [설치 가이드](#-설치-가이드)
- [환경변수](#-환경변수)
- [모노레포 구조](#-모노레포-구조)
- [pnpm 명령어](#-pnpm-명령어)
- [문서](#-문서)
- [컨트리뷰션 가이드](#-컨트리뷰션-가이드)
- [라이선스](#-라이선스)

---

## 📌 프로젝트 개요

### 배경

분산된 운영 서버에서 발생하는 로그를 각 서버에서 개별 관리하면 보안 사고 탐지, 장애 분석, 감사 대응이 어렵습니다. 이 프로젝트는 69대의 이기종 서버에서 생성되는 로그를 단일 플랫폼으로 통합하여 가시성과 대응 속도를 높이는 것을 목표로 합니다.

### 목표

| 목표 | 세부 내용 |
|------|-----------|
| **통합 수집** | ZoneA·B 전 서버의 시스템·보안·인증 로그 중앙화 |
| **안정적 보존** | ILM 4단계 정책으로 1년간 비용 효율적 저장 |
| **실시간 모니터링** | Kibana 대시보드로 이상 징후 즉시 탐지 |
| **유실 방지** | Redis 버퍼로 수집 장애 시에도 로그 유실 Zero |

### 수집 범위

| Zone | 서버 | 대수 | 수집 로그 |
|------|------|------|-----------|
| ZoneA (10.10.184.0/24) | Linux RHEL | 10대 | syslog, secure, audit |
| ZoneA (10.10.184.0/24) | Windows | 2대 | System Event, Security Event |
| ZoneB (10.10.188.0/24) | Linux RHEL | 50대 | syslog, secure, audit |
| ZoneB (10.10.188.0/24) | Windows 2022 | 7대 | System Event, Security Event |

---

## 🏗 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│  ZoneA  10.10.184.0/24                                          │
│                                                                 │
│  [ Linux x10 ]──┐                                              │
│  (Filebeat)     ├──▶ [ Redis 7.4 ] ──▶ [ Logstash 8.17 ]──┐  │
│  [ Windows x2]──┘      Buffer-A            Pipeline         │  │
└─────────────────────────────────────────────────────────────┼──┘
                                                              │
┌─────────────────────────────────────────────────────────────┼──┐
│  ZoneB  10.10.188.0/24                                      │  │
│                                                             ▼  │
│  [ Linux x50 ]──┐                              ┌─────────────┐ │
│  (Filebeat)     ├──▶ [ Redis 7.4 ] ──▶ [ Logstash ] ──▶  │ │ │
│  [ Windows x7 ]─┘      Buffer-B                │  ES Cluster │ │
│                                                │  node1(M)   │ │
│  [ es-node1 ] Elasticsearch Master + Kibana    │  node2(D)   │ │
│  [ es-node2 ] Elasticsearch Data (SSD+HDD)     │  node3(D)   │ │
│  [ es-node3 ] Elasticsearch Data (SSD+HDD)     └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### ILM 저장 정책

```
 0 ────── 30일 ────── 90일 ──────────── 365일 ──▶ 삭제
  [  Hot  ]  [  Warm  ]  [     Cold      ]  [ Delete ]
   NVMe SSD   SATA SSD        HDD
  쓰기·조회  읽기전용·      Frozen Index
             Force-merge
```

---

## 🔍 아키텍처 설계 근거

### 1. Elasticsearch 3노드 클러스터 구축 이유

#### 1.1 고가용성 (High Availability)

단일 노드 장애 시 서비스 중단 없이 운영을 지속하기 위해 클러스터를 구성한다. 노드 1대가 다운되더라도 나머지 2대가 계속 쿼리와 색인 요청을 처리한다.

#### 1.2 Split-Brain 방지를 위한 최소 홀수 구성

Elasticsearch는 마스터 선출 시 과반수(`quorum`) 투표를 요구한다.

| 노드 수 | Quorum | 허용 장애 노드 |
|---------|--------|---------------|
| 2 | 2 | 0 (Split-Brain 위험) |
| **3** | **2** | **1** |
| 5 | 3 | 2 |

3노드가 **비용 대비 안정성 최소 단위**다. 2노드는 Split-Brain(두 노드가 각자 마스터가 되는 현상) 위험이 있어 운영 환경에서 사용하지 않는다.

#### 1.3 역할 분리로 성능 최적화

| 노드 | 역할 | 이유 |
|------|------|------|
| node1 | Master 전용 | 클러스터 상태 관리에만 집중, 데이터 부하 없음 |
| node2 | Data (SSD + HDD) | Hot/Warm 데이터 처리 |
| node3 | Data (SSD + HDD) | Hot/Warm 데이터 처리, 부하 분산 |

Master 노드에 데이터 역할을 겸하면 GC(Garbage Collection) 부하 시 마스터 선출이 흔들려 클러스터 전체가 불안정해진다.

#### 1.4 샤드 복제 및 데이터 안전성

`number_of_replicas: 1` 설정으로 각 샤드가 2노드에 복제된다. 데이터 노드 1대 장애 시에도 데이터 유실 없이 서비스를 유지한다.

---

### 2. Redis 버퍼 서버 구축 이유

#### 2.1 로그 폭주(Burst) 흡수

운영 서버 69대에서 동시에 로그가 쏟아질 때(점검, 배포, 보안 이벤트 등) Elasticsearch가 직접 수신하면 **색인 큐 포화 → OOM → 클러스터 장애**로 이어진다. Redis가 중간에서 임시 저장 후 Logstash가 일정 속도로 꺼내 처리한다.

```
Beats (69대) → Redis (버퍼) → Logstash → Elasticsearch
               ↑ 초당 수만 건 받아도 OK    ↑ 처리 가능한 속도로만 전달
```

#### 2.2 Logstash 장애 시 로그 유실 방지

Logstash 재시작·업그레이드 시간 동안 Beats는 계속 Redis에 쌓는다. Logstash가 복구되면 밀린 로그를 순서대로 처리한다. Beats가 Elasticsearch에 직접 전송하면 이 시간 동안의 로그는 유실된다.

#### 2.3 Zone 분리를 통한 네트워크 격리

| 버퍼 서버 | 담당 Zone | 서버 수 |
|-----------|-----------|---------|
| Buffer-A | ZoneA (10.10.184.0/24) | 12대 |
| Buffer-B | ZoneB (10.10.188.0/24) | 57대 |

Zone별 독립 버퍼를 두어 한 Zone의 장애가 다른 Zone으로 전파되지 않도록 격리한다.

#### 2.4 Redis를 선택한 이유

| 비교 항목 | Redis | Kafka |
|-----------|-------|-------|
| 구축 난이도 | 낮음 (단일 프로세스) | 높음 (ZooKeeper/KRaft 필요) |
| 운영 복잡도 | 낮음 | 높음 |
| 적합 규모 | 중소 (69대) | 대규모 (수백~수천 대) |
| Logstash 연동 | 기본 플러그인 지원 | 기본 플러그인 지원 |

69대 규모에서 Kafka는 과도한 오버엔지니어링이다. Redis List의 `LPUSH`/`BRPOP` 패턴으로 충분한 처리량을 확보하면서 운영 부담을 최소화한다.

---

### 3. 중앙 로그 서버로 ELK를 사용하는 이유

#### 3.1 E-L-K 각 컴포넌트의 역할

```
Filebeat/Winlogbeat  →  Logstash  →  Elasticsearch  →  Kibana
(수집·전송)             (파싱·정제)    (저장·색인)         (시각화·검색)
```

단일 목적의 컴포넌트를 조합하여 각 단계를 독립적으로 스케일 아웃하거나 교체할 수 있다.

#### 3.2 이기종 OS 통합 수집

본 프로젝트는 **Linux(RHEL 60대)** 와 **Windows 2022(9대)** 가 혼재한다. ELK는 운영체제별 전용 에이전트를 제공한다.

| 에이전트 | 대상 | 수집 로그 |
|----------|------|-----------|
| Filebeat | Linux RHEL | syslog, auth, audit |
| Winlogbeat | Windows 2022 | Security Event Log (4624, 4625 등) |

두 에이전트 모두 동일한 Redis → Logstash → ES 파이프라인으로 통합된다.

#### 3.3 비정형 로그 파싱 (Logstash Grok)

시스템 로그는 JSON이 아닌 비정형 텍스트다. Logstash의 Grok 필터가 정규식 기반으로 구조화하여 ES에 색인한다. 수집 후 파싱이 아닌 **수집 시점 파싱**으로 Kibana에서 즉시 필드 검색이 가능하다.

#### 3.4 ILM으로 1년 보존 자동화

| 단계 | 기간 | 스토리지 전략 |
|------|------|--------------|
| Hot | 0~30일 | SSD, 빠른 읽기/쓰기 |
| Warm | 30~90일 | SSD, 압축·병합 후 읽기 전용 |
| Cold | 90~365일 | HDD, Freeze 상태 |
| Delete | 365일+ | 자동 삭제 |

수동 개입 없이 보존 정책이 자동 실행된다.

#### 3.5 대안 대비 ELK의 장점

| 비교 항목 | ELK Stack | Splunk | Loki+Grafana |
|-----------|-----------|--------|--------------|
| 라이선스 비용 | 무료 (OSS) | 고가 (데이터 볼륨 과금) | 무료 |
| 전문 검색 성능 | 매우 높음 | 높음 | 낮음 (레이블 기반) |
| 비정형 파싱 | Grok (강력) | SPL (강력) | 제한적 |
| 국내 레퍼런스 | 풍부 | 풍부 | 적음 |
| 69대 규모 적합성 | 최적 | 과도한 비용 | 기능 부족 |

---

### 설계 결정 요약

| 설계 결정 | 핵심 이유 |
|-----------|-----------|
| ES 3노드 클러스터 | Split-Brain 방지, 역할 분리, 레플리카 보장 |
| Redis 버퍼 | 로그 폭주 흡수, Logstash 장애 시 유실 방지, Zone 격리 |
| ELK 스택 | 이기종 OS 통합, 비정형 파싱, ILM 자동화, 무료 OSS |

---

## 🛠 기술 스택

### 서버 컴포넌트

| 컴포넌트 | 버전 | 용도 |
|----------|------|------|
| [Elasticsearch](https://www.elastic.co/elasticsearch/) | `8.17.4` | 로그 인덱싱·검색·저장 |
| [Logstash](https://www.elastic.co/logstash/) | `8.17.4` | 로그 파싱·필터링·정규화 |
| [Kibana](https://www.elastic.co/kibana/) | `8.17.4` | 대시보드·시각화·알림 |
| [Redis](https://redis.io/) | `7.4` | 로그 버퍼 큐 (유실 방지) |

### 에이전트

| 컴포넌트 | 버전 | 대상 OS |
|----------|------|---------|
| [Filebeat](https://www.elastic.co/beats/filebeat) | `8.17.4` | Linux (RHEL) |
| [Winlogbeat](https://www.elastic.co/beats/winlogbeat) | `8.17.4` | Windows 2022 |

### 인프라·운영

| 컴포넌트 | 버전 | 용도 |
|----------|------|------|
| [Docker Engine](https://www.docker.com/) | `27.x` | 컨테이너 런타임 |
| [Docker Compose](https://docs.docker.com/compose/) | `v2.29.x` | 컨테이너 오케스트레이션 |
| [Ubuntu](https://ubuntu.com/) | `24.04.2 LTS` | 서버 OS |
| [pnpm](https://pnpm.io/) | `9.x` | 모노레포 패키지 관리 |

---

## ✅ 사전 요구사항

로컬 개발 환경 및 서버에 아래 소프트웨어가 설치되어 있어야 합니다.

| 소프트웨어 | 최소 버전 | 확인 명령 |
|-----------|-----------|-----------|
| Node.js | `20.x` | `node -v` |
| pnpm | `9.x` | `pnpm -v` |
| Docker Engine | `27.x` | `docker -v` |
| Docker Compose | `v2.29.x` | `docker compose version` |
| Git | `2.x` | `git --version` |

> **서버 OS 요구사항**
> - 로그 수집 서버 5대 : Ubuntu 24.04.2 LTS
> - ES Data 노드(node2·3) : NVMe SSD 500 GB + HDD 2 TB
> - 커널 파라미터 : `vm.max_map_count=262144`

---

## ⚡ 빠른 시작

```bash
# 1. 저장소 클론
git clone <repository-url>
cd LogServer

# 2. 의존성 설치
pnpm install

# 3. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 IP·패스워드 등 실제 값으로 수정

# 4. 전체 자동 배포 (인증서 생성 → 클러스터 기동 → ILM 적용 → 버퍼 기동)
bash scripts/deploy.sh

# 5. 헬스체크
pnpm run health
```

> Kibana 접속 : `http://<node1-ip>:5601`

---

## 📖 설치 가이드

### Step 1 — 저장소 클론 및 의존성 설치

```bash
git clone <repository-url>
cd LogServer
pnpm install
```

### Step 2 — 환경변수 구성

루트 `.env` 와 각 패키지별 `.env` 를 설정합니다.

```bash
# 루트
cp .env.example .env

# 각 패키지
cp packages/es-node1/.env.example  packages/es-node1/.env
cp packages/es-node2/.env.example  packages/es-node2/.env
cp packages/es-node3/.env.example  packages/es-node3/.env
cp packages/buffer-a/.env.example  packages/buffer-a/.env
cp packages/buffer-b/.env.example  packages/buffer-b/.env
```

`.env` 에서 반드시 수정해야 할 항목:

```dotenv
ES_NODE1_IP=<실제 node1 IP>
ES_NODE2_IP=<실제 node2 IP>
ES_NODE3_IP=<실제 node3 IP>
BUFFER_A_IP=<실제 Buffer-A IP>
BUFFER_B_IP=<실제 Buffer-B IP>
ELASTIC_PASSWORD=<강력한 패스워드>
REDIS_PASSWORD=<강력한 패스워드>
KIBANA_ENCRYPTION_KEY=<32자 이상 랜덤 문자열>
```

### Step 3 — TLS 인증서 생성

```bash
pnpm --filter shared run gen-certs
```

생성 결과: `packages/shared/certs/` 에 `ca.crt`, `node1~3.crt/key`

### Step 4 — Elasticsearch 클러스터 기동

> 반드시 node1 → node2·3 순서로 기동합니다.

```bash
# node1 (Master + Kibana) 먼저 기동
pnpm run up:node1

# 30초 대기 후 Data 노드 기동
pnpm run up:node2
pnpm run up:node3

# 클러스터 상태 확인 (green 이 될 때까지 대기)
pnpm run health
```

### Step 5 — ILM 정책 및 인덱스 템플릿 적용

```bash
pnpm run setup
```

적용 항목:
- ILM 4단계 정책 (`logs-ilm-policy`)
- 인덱스 템플릿 (`logs-*`)
- 롤오버 별칭 5종 (`logs-syslog`, `logs-auth`, `logs-audit`, `logs-windows_system`, `logs-windows_security`)

### Step 6 — 버퍼 서버 기동

```bash
pnpm run up:buffer-b   # ZoneB 먼저
pnpm run up:buffer-a   # ZoneA
```

### Step 7 — 에이전트 배포

**Linux (RHEL)**

```bash
# 대상 서버에서 실행
cd packages/agent-linux
REDIS_HOST=10.10.184.100 \
REDIS_PASSWORD=<패스워드> \
ZONE=ZoneA \
bash install.sh
```

**Windows 2022**

```powershell
# 관리자 PowerShell 에서 실행
cd packages\agent-windows
.\install.ps1 `
  -RedisHost     10.10.188.100 `
  -RedisPassword <패스워드> `
  -Zone          ZoneB
```

### Step 8 — 수집 확인

```bash
# 클러스터 + Redis 헬스체크
pnpm run health

# Kibana Discover 에서 logs-* 인덱스 데이터 유입 확인
open http://<node1-ip>:5601
```

---

## 🔧 환경변수

### 루트 `.env`

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `ES_VERSION` | Elasticsearch 버전 | `8.17.4` |
| `ES_CLUSTER_NAME` | 클러스터 이름 | `logserver-cluster` |
| `ES_NODE1_IP` | node1 서버 IP | `10.10.188.10` |
| `ES_NODE2_IP` | node2 서버 IP | `10.10.188.11` |
| `ES_NODE3_IP` | node3 서버 IP | `10.10.188.12` |
| `ELASTIC_PASSWORD` | elastic 계정 패스워드 | _(필수 변경)_ |
| `BUFFER_A_IP` | Buffer-A 서버 IP | `10.10.184.100` |
| `BUFFER_B_IP` | Buffer-B 서버 IP | `10.10.188.100` |
| `REDIS_PASSWORD` | Redis 인증 패스워드 | _(필수 변경)_ |
| `KIBANA_ENCRYPTION_KEY` | Kibana 암호화 키 (32자+) | _(필수 변경)_ |

> 보안상 `.env` 파일은 절대 Git에 커밋하지 마세요. `.gitignore` 에 등록되어 있습니다.

---

## 📁 모노레포 구조

```
LogServer/
├── package.json                    ← 루트 (전체 명령 진입점)
├── pnpm-workspace.yaml
├── .env.example
│
├── packages/
│   ├── buffer-a/                   ← ZoneA 버퍼 서버 (Redis + Logstash)
│   │   ├── docker-compose.yml
│   │   ├── logstash/
│   │   │   ├── config/logstash.yml
│   │   │   └── pipeline/logstash.conf
│   │   └── redis/redis.conf
│   │
│   ├── buffer-b/                   ← ZoneB 버퍼 서버 (Redis + Logstash)
│   │
│   ├── es-node1/                   ← Elasticsearch Master + Kibana
│   │   ├── docker-compose.yml
│   │   ├── elasticsearch/config/elasticsearch.yml
│   │   └── kibana/config/kibana.yml
│   │
│   ├── es-node2/                   ← Elasticsearch Data Node
│   ├── es-node3/                   ← Elasticsearch Data Node
│   │
│   ├── agent-linux/                ← Filebeat (RHEL 배포용)
│   │   ├── filebeat.yml
│   │   ├── modules.d/
│   │   └── install.sh
│   │
│   ├── agent-windows/              ← Winlogbeat (Windows 2022 배포용)
│   │   ├── winlogbeat.yml
│   │   └── install.ps1
│   │
│   └── shared/                     ← 공통 리소스
│       ├── certs/                  ← TLS 인증서
│       ├── ilm/policy.json         ← ILM 4단계 정책
│       ├── index-templates/        ← ES 인덱스 템플릿
│       └── scripts/                ← ES 초기 설정 스크립트
│
└── scripts/
    ├── deploy.sh                   ← 전체 자동 배포
    └── health-check.mjs            ← 헬스체크
```

---

## 💻 pnpm 명령어

### 전체 서비스 관리

| 명령 | 설명 |
|------|------|
| `pnpm run up:all` | 전체 서비스 기동 |
| `pnpm run down:all` | 전체 서비스 중단 |
| `pnpm run ps:all` | 전체 컨테이너 상태 확인 |
| `pnpm run health` | 클러스터 + Redis 헬스체크 |

### 개별 서비스 관리

| 명령 | 설명 |
|------|------|
| `pnpm run up:cluster` | ES 클러스터 (node1·2·3) 기동 |
| `pnpm run up:buffers` | 버퍼 서버 (buffer-a·b) 기동 |
| `pnpm run up:node1` | node1 단독 기동 |
| `pnpm run up:buffer-b` | Buffer-B 단독 기동 |

### 설정 적용

| 명령 | 설명 |
|------|------|
| `pnpm run setup` | ILM 정책·인덱스 템플릿 ES에 적용 |
| `pnpm --filter shared run gen-certs` | TLS 인증서 생성 |
| `pnpm --filter shared run apply-ilm` | ILM 정책 재적용 |

### 로그 확인

| 명령 | 설명 |
|------|------|
| `pnpm --filter es-node1 run logs:kibana` | Kibana 로그 스트림 |
| `pnpm --filter buffer-b run logs:logstash` | Logstash 로그 스트림 |
| `pnpm --filter buffer-a run logs:redis` | Redis 로그 스트림 |

### 에이전트 배포

| 명령 | 설명 |
|------|------|
| `pnpm run deploy:agent:linux` | Filebeat 설치 스크립트 실행 |
| `pnpm run deploy:agent:windows` | Winlogbeat PowerShell 설치 |

---

## 📚 문서

| 문서 | 설명 |
|------|------|
| [README01.md](README01.md) | 아키텍처·서버 스펙·기술 스택·ILM 정책 전체 설명 |
| [WBS.md](WBS.md) | 2개월 프로젝트 WBS (77개 태스크) |

---

## 🤝 컨트리뷰션 가이드

### 브랜치 전략

```
main          ← 운영 배포본 (직접 push 금지)
develop       ← 통합 개발 브랜치
feat/<name>   ← 신규 기능 개발
fix/<name>    ← 버그 수정
hotfix/<name> ← 운영 긴급 수정
docs/<name>   ← 문서 수정
```

### 커밋 메시지 규칙

[Conventional Commits](https://www.conventionalcommits.org/) 형식을 따릅니다.

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

| type | 사용 시점 |
|------|-----------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `conf` | 설정 파일 변경 (docker-compose, logstash.conf 등) |
| `refactor` | 코드 리팩터링 (기능 변경 없음) |
| `test` | 테스트 추가·수정 |
| `chore` | 빌드·패키지 관련 변경 |

**예시**

```bash
feat(pipeline): add windows security event id filter
fix(logstash): correct grok pattern for audit log timestamp
conf(es-node2): increase JVM heap to 32g
docs(readme): update installation guide
```

### Pull Request 절차

1. **`develop` 브랜치에서 작업 브랜치 생성**

    ```bash
    git checkout develop
    git pull origin develop
    git checkout -b feat/logstash-grok-pattern
    ```

2. **작업 및 커밋**

    ```bash
    git add packages/buffer-a/logstash/pipeline/logstash.conf
    git commit -m "feat(pipeline): improve syslog grok pattern for RHEL 9"
    ```

3. **원격 브랜치 푸시 및 PR 생성**

    ```bash
    git push origin feat/logstash-grok-pattern
    # GitHub 에서 develop ← feat/... PR 생성
    ```

4. **PR 체크리스트**

    ```
    [ ] 변경 목적이 PR 설명에 명확히 기술되어 있다
    [ ] 설정 변경 시 .env.example 도 함께 업데이트했다
    [ ] 패스워드·IP 등 민감정보가 포함되지 않았다
    [ ] 로컬에서 docker compose up 으로 동작을 확인했다
    [ ] 관련 문서(README01.md 등)를 업데이트했다
    ```

5. **코드 리뷰 후 `develop` 머지**

    > `main` 머지는 검수 완료 후 OPS 담당자가 진행합니다.

### 이슈 등록

버그 리포트 또는 기능 요청은 [Issues](../../issues) 탭을 이용해 주세요.

| 이슈 유형 | 라벨 | 설명 |
|-----------|------|------|
| 버그 | `bug` | 잘못된 동작, 에러 발생 |
| 기능 요청 | `enhancement` | 새로운 기능 제안 |
| 문서 | `documentation` | 문서 오류·보완 |
| 질문 | `question` | 사용법 문의 |

### 개발 환경 설정

```bash
# 저장소 포크 후 클론
git clone https://github.com/<your-id>/LogServer.git
cd LogServer

# 의존성 설치
pnpm install

# 개발용 환경변수 설정
cp .env.example .env
# 로컬 IP 및 테스트용 패스워드로 수정

# 변경 전 헬스체크
pnpm run health
```

---

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE) 를 따릅니다.

---

<div align="center">

**문의 및 이슈** : [Issues](../../issues) 탭을 이용해 주세요.

</div>
