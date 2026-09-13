#!/usr/bin/env bash
set -Eeuo pipefail

exec > >(tee -a /var/log/lengeas-phase-01-bootstrap.log) 2>&1

export DEBIAN_FRONTEND=noninteractive
REPO_URL="https://github.com/guerra2fernando/LenGeas.git"
REPO_DIR="/opt/lengeas"

apt-get update
apt-get install -y ca-certificates curl git gnupg openssl python3 rsync

# Install Docker Engine and the Compose v2 plugin on the server only.
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu %s stable\n' \
  "$(dpkg --print-architecture)" "$(. /etc/os-release && printf '%s' "$VERSION_CODENAME")" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
usermod -aG docker ubuntu || true

# Install Caddy from its signed upstream package repository.
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  > /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

install -d -m 0755 /opt
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone --branch main --depth 1 "$REPO_URL" "$REPO_DIR"
else
  git -C "$REPO_DIR" fetch origin main
  if git -C "$REPO_DIR" diff --quiet && git -C "$REPO_DIR" diff --cached --quiet; then
    git -C "$REPO_DIR" pull --ff-only origin main
  else
    echo "Refusing to overwrite a dirty server checkout: $REPO_DIR" >&2
    exit 1
  fi
fi

# Keep the server environment out of Git and out of the public HTTP surface.
install -m 0600 /dev/null "$REPO_DIR/.env"
cat > "$REPO_DIR/.env" <<EOF
APP_ENV=staging
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8000
MONGODB_URI=mongodb://mongo:27017/?replicaSet=rs0
VALKEY_URL=redis://valkey:6379/0
RABBITMQ_URL=amqp://rabbitmq:5672/
RABBITMQ_DEFAULT_USER=lengeas_server
RABBITMQ_DEFAULT_PASS=$(openssl rand -hex 32)
KAFKA_BROKERS=redpanda:9092
S3_ENDPOINT=http://minio:9000
S3_REGION=us-east-1
S3_BUCKET=lengeas-server
MINIO_ROOT_USER=lengeas_server
MINIO_ROOT_PASSWORD=$(openssl rand -hex 32)
MINIO_BUCKET=lengeas-server
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
MAILPIT_SMTP_HOST=mailpit
MAILPIT_SMTP_PORT=1025
EOF
chown -R root:root "$REPO_DIR"
chmod 0600 "$REPO_DIR/.env"

# A small swap file keeps the medium host from OOM-killing the observability stack.
if [ ! -e /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  printf '/swapfile none swap sw 0 0\n' >> /etc/fstab
fi

install -d -m 0755 /etc/caddy
install -m 0644 "$REPO_DIR/infrastructure/aws/Caddyfile" /etc/caddy/Caddyfile
systemctl enable caddy

cd "$REPO_DIR"
docker compose --project-name lengeas-local --env-file .env --file compose.yaml config --quiet
python3 tools/dev/task_runner.py local-up
python3 tools/dev/task_runner.py local-smoke
systemctl restart caddy
systemctl --no-pager --full status caddy

date -u +%Y-%m-%dT%H:%M:%SZ > /var/lib/lengeas-phase-01-ready
