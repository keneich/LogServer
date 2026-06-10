#!/usr/bin/env node
import { execSync } from "node:child_process";

const ES_HOST     = process.env.ES_HOST     || "https://10.10.188.8:9200";
const ES_USER     = process.env.ES_USER     || "elastic";
const ES_PASSWORD = process.env.ES_PASSWORD || "changeme";
const CA_CERT     = process.env.CA_CERT     || "packages/shared/certs/ca.crt";

const BUFFER_A_REDIS  = process.env.BUFFER_A_REDIS  || "10.10.187.11:6379";
const BUFFER_B_REDIS  = process.env.BUFFER_B_REDIS  || "10.10.191.15:6379";
const REDIS_PASSWORD  = process.env.REDIS_PASSWORD  || "changeme";

function curl(url, extra = "") {
  try {
    const out = execSync(
      `curl -sf --cacert ${CA_CERT} -u ${ES_USER}:${ES_PASSWORD} ${extra} "${url}"`,
      { encoding: "utf8" }
    );
    return JSON.parse(out);
  } catch {
    return null;
  }
}

function redisCheck(host) {
  const [h, p] = host.split(":");
  try {
    execSync(`redis-cli -h ${h} -p ${p} -a ${REDIS_PASSWORD} ping`, {
      encoding: "utf8",
      stdio: "pipe",
    });
    return true;
  } catch {
    return false;
  }
}

const GREEN  = "\x1b[32m✓\x1b[0m";
const RED    = "\x1b[31m✗\x1b[0m";
const YELLOW = "\x1b[33m⚠\x1b[0m";

console.log("\n=== LogServer Health Check ===\n");

// Elasticsearch 클러스터
const cluster = curl(`${ES_HOST}/_cluster/health`);
if (cluster) {
  const icon = cluster.status === "green" ? GREEN : cluster.status === "yellow" ? YELLOW : RED;
  console.log(`${icon}  Elasticsearch Cluster : ${cluster.status.toUpperCase()}`);
  console.log(`       nodes=${cluster.number_of_nodes}  active_shards=${cluster.active_shards}`);
} else {
  console.log(`${RED}  Elasticsearch Cluster : 연결 실패`);
}

// 노드별 상태
const nodes = curl(`${ES_HOST}/_cat/nodes?v&h=name,ip,roles,heap.percent,disk.used_percent,master`);
if (nodes) {
  console.log(`\n${GREEN}  노드 목록`);
  console.log(nodes);
}

// ILM 상태
const ilm = curl(`${ES_HOST}/_ilm/status`);
if (ilm) {
  const icon = ilm.operation_mode === "RUNNING" ? GREEN : RED;
  console.log(`${icon}  ILM : ${ilm.operation_mode}`);
}

// Redis Buffer-A
const bufA = redisCheck(BUFFER_A_REDIS);
console.log(`${bufA ? GREEN : RED}  Redis Buffer-A (${BUFFER_A_REDIS})`);

// Redis Buffer-B
const bufB = redisCheck(BUFFER_B_REDIS);
console.log(`${bufB ? GREEN : RED}  Redis Buffer-B (${BUFFER_B_REDIS})`);

console.log();
