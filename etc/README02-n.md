# ELK 스택 기반 중앙화 로그 수집·모니터링 시스템

## 1. 배경

서버에서 발생하는 로그를 각 서버에서 개별 관리하면 보안 사고 탐지, 장애 분석, 감사 대응이 어렵습니다.

약 70대의 이기종 서버에서 생성되는 로그를 단일 플랫폼으로 통합하여 가시성과 대응 속도를 높이는 것을 목표로 합니다.

## 2. 목표

| 목표 | 세부 내용 |
|------|-----------|
| **통합 수집** | 업무망·인터넷망 전 서버의 시스템·보안·인증 로그 중앙화 |
| **안정적 보존** | ILM 4단계 정책으로 1년간 비용 효율적 저장 |
| **실시간 모니터링** | Kibana 대시보드로 상황별 로그 모니터링 |
| **유실 방지** | Redis 버퍼로 수집 장애 시에도 로그 유실 Zero |

## ILM 저장 정책

| 단계 | 기간 | 상태 |
|------|------|------|
| Hot | 0 ~ 30일 | 읽기/쓰기 |
| Warm | 31 ~ 90일 | 읽기 전용 |
| Cold | 91 ~ 365일 | 저장 |
| Delete | 365일 이상 | 삭제 |

## 3. 기술 스택

### 서버 컴포넌트

| 컴포넌트 | 버전 | 용도 |
|----------|------|------|
| Elasticsearch | 8.17.4 | 로그 인덱싱·검색·저장 |
| Logstash | 8.17.4 | 로그 파싱·필터링·정규화 |
| Kibana | 8.17.4 | 대시보드·시각화·알림 |
| Redis | 7.4 | 로그 버퍼 큐 (유실 방지) |

### 에이전트

| 컴포넌트 | 버전 | 대상 OS |
|----------|------|---------|
| Filebeat | 8.17.4 | Linux (RHEL) |
| Winlogbeat | 8.17.4 | Windows 2022 |

## 4. 서버 스펙

### 로그 발생량 추정

| 구분 | 대수 | 서버당/일 | 소계/일 |
|------|------|-----------|---------|
| Linux RHEL | 60대 | 80 MB | 4,800 MB |
| Windows | 9대 | 200 MB | 1,800 MB |
| **원본 합계** | **69대** | | **≈ 6.6 GB/일** |
| ES 저장량 (압축 50% + 레플리카 1) | | | **≈ 6.6 GB/일** |
| **연간 총 저장량** | | | **≈ 2.4 TB** |

### 서버별 스펙

#### Buffer 서버 (ZoneA · ZoneB 각 1대)

| 항목 | 스펙 |
|------|------|
| OS | Ubuntu 24.04.2 LTS |
| CPU | 8 core |
| RAM | 16 GB (Redis 4 GB + Logstash 8 GB + OS 4 GB) |
| SSD | 300 GB (OS 50 GB + Logstash PQ 50 GB + Redis AOF 10 GB + 여유) |
| 컨테이너 | Redis + Logstash (docker-compose) |

#### es-node1 (Elasticsearch Master + Kibana)

| 항목 | 스펙 |
|------|------|
| OS | Ubuntu 24.04.2 LTS |
| CPU | 8 core |
| RAM | 32 GB (ES JVM 8 GB + Kibana 4 GB + OS 나머지) |
| SSD | 500 GB (마스터 상태·로그 전용, 데이터 저장 없음) |
| 컨테이너 | Elasticsearch Master + Kibana (docker-compose) |

#### es-node2 · es-node3 (Elasticsearch Data Node × 2)

| 항목 | 스펙 |
|------|------|
| OS | Ubuntu 24.04.2 LTS |
| CPU | 16 core |
| RAM | 64 GB (ES JVM 32 GB + OS Page Cache 32 GB) |
| NVMe SSD | 500 GB (Hot · Warm 티어) |
| HDD | 2 TB (Cold 티어) |
| 네트워크 | 10 Gbps (클러스터 내부 통신) |
| 컨테이너 | Elasticsearch Data (docker-compose) |

### 전체 서버 요약

| 서버 | Zone | CPU | RAM | SSD | HDD | 역할 |
|------|------|-----|-----|-----|-----|------|
| Buffer-A | A | 8c | 16 GB | 300 GB | - | Redis + Logstash |
| Buffer-B | B | 8c | 16 GB | 300 GB | - | Redis + Logstash |
| node1 | B | 8c | 32 GB | 500 GB | - | ES Master + Kibana |
| node2 | B | 16c | 64 GB | 500 GB | 2 TB | ES Data |
| node3 | B | 16c | 64 GB | 500 GB | 2 TB | ES Data |

## 5. 구축 일정 (8주)

| 단계 | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1. 프로젝트 준비 | ● | | | | | | | |
| 2. 서버 기반 환경 구성 | ● | ● | | | | | | |
| 3. TLS 인증서 생성 | | ● | | | | | | |
| 4. Elasticsearch 클러스터 구축 | | ● | ● | | | | | |
| 5. Redis + Logstash 버퍼 서버 구축 | | | ● | | | | | |
| 6. Logstash 파이프라인 개발 | | | ● | ● | | | | |
| 7. Elasticsearch 인덱스 관리 설정 | | | | ● | | | | |
| 8. 에이전트 배포 | | | | ● | ● | | | |
| 9. 수집 현황 대시보드 구축 | | | | | ● | ● | | |
| 10. 인프라 모니터링 대시보드 구축 | | | | | | ● | ● | |
| 11. 알림 설정 | | | | | | | ● | |
| 12. 통합 테스트 | | | | | | | ● | |
| 13. 성능 튜닝 | | | | | | | ● | ● |
| 14. 운영 이관 | | | | | | | | ● |
