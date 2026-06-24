#!/usr/bin/env bash
set -euo pipefail

BEATS_VERSION="8.17.4"
REDIS_HOST="${REDIS_HOST:-10.10.187.11}"
REDIS_PASSWORD="${REDIS_PASSWORD:-changeme}"
ZONE="${ZONE:-ZoneA}"

echo "==> Filebeat ${BEATS_VERSION} 설치 시작 (${ZONE})"

# OS 감지 후 패키지 매니저 분기
if command -v dnf &>/dev/null; then
  # RHEL 8+ / Rocky / AlmaLinux
  rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
  cat > /etc/yum.repos.d/elastic.repo << 'EOF'
[elastic-8.x]
name=Elastic repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF
  dnf install -y filebeat-${BEATS_VERSION}
elif command -v yum &>/dev/null; then
  # RHEL 7 (dnf 미포함)
  rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
  cat > /etc/yum.repos.d/elastic.repo << 'EOF'
[elastic-8.x]
name=Elastic repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF
  yum install -y filebeat-${BEATS_VERSION}
else
  # Ubuntu / Debian
  apt-get install -y gnupg apt-transport-https
  curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch \
    | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] \
https://artifacts.elastic.co/packages/8.x/apt stable main" \
    | tee /etc/apt/sources.list.d/elastic-8.x.list
  apt-get update
  apt-get install -y filebeat=${BEATS_VERSION}
fi

# 설정 파일 복사
cp filebeat.yml /etc/filebeat/filebeat.yml

# 모든 모듈 비활성화 (filebeat.inputs와 중복 모니터링 방지)
for f in /etc/filebeat/modules.d/*.yml; do
  [ -f "$f" ] && mv "$f" "${f}.disabled"
done

# 환경변수 주입
sed -i "s|\${REDIS_HOST:10.10.187.11}|${REDIS_HOST}|g" /etc/filebeat/filebeat.yml
sed -i "s|\${REDIS_PASSWORD}|${REDIS_PASSWORD}|g"        /etc/filebeat/filebeat.yml
sed -i "s|\"ZoneA\"|\"${ZONE}\"|g"                       /etc/filebeat/filebeat.yml

# 설정 유효성 검사
filebeat test config -c /etc/filebeat/filebeat.yml

systemctl daemon-reload
systemctl enable filebeat
systemctl restart filebeat

echo "==> Filebeat 설치 완료"
systemctl status filebeat --no-pager
