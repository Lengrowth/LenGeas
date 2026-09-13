"""Cross-platform lifecycle and authentic smoke checks for the local platform."""

from __future__ import annotations

import base64
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "compose.yaml"
ENV_FILE = ROOT / ".env"
PROJECT = "lengeas-local"
COMPOSE = [
    "docker",
    "compose",
    "--project-name",
    PROJECT,
    "--env-file",
    str(ENV_FILE),
    "--file",
    str(COMPOSE_FILE),
]


class LocalStackError(RuntimeError):
    """An actionable local-stack failure."""


def _compose(
    *args: str, capture: bool = False, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [*COMPOSE, *args],
        cwd=ROOT,
        check=False,
        text=True,
        input=input_text,
        capture_output=capture,
    )


def _run(
    command: list[str], *, capture: bool = False, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        command,
        cwd=ROOT,
        check=False,
        text=True,
        input=input_text,
        capture_output=capture,
    )


def _require_docker() -> None:
    unavailable = ["docker version", "docker compose version"]
    if shutil.which("docker") is None:
        raise LocalStackError(
            "Docker is unavailable. Exact unavailable commands: " + "; ".join(unavailable)
        )
    probes = [("docker", "version"), ("docker", "compose", "version")]
    failures: list[str] = []
    for probe in probes:
        result = _run(list(probe), capture=True)
        if result.returncode:
            failures.append(" ".join(probe))
    if failures:
        raise LocalStackError(
            "Docker is unavailable. Exact unavailable commands: " + "; ".join(failures)
        )


def _read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_FILE.exists():
        for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value
    return values


def _ensure_env() -> dict[str, str]:
    values = _read_env()
    generated = {
        "RABBITMQ_DEFAULT_USER": "lengeas_local",
        "RABBITMQ_DEFAULT_PASS": secrets.token_urlsafe(24),
        "MINIO_ROOT_USER": "lengeas_local",
        "MINIO_ROOT_PASSWORD": secrets.token_urlsafe(24),
        "MINIO_BUCKET": "lengeas-local",
    }
    changed = False
    for key, value in generated.items():
        if not values.get(key):
            values[key] = value
            changed = True
    if changed or not ENV_FILE.exists():
        lines = [f"{key}={value}" for key, value in sorted(values.items())]
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        try:
            os.chmod(ENV_FILE, 0o600)
        except OSError:
            pass
    return values


def _wait_http(url: str, *, timeout: float = 90.0) -> tuple[int, bytes]:
    deadline = time.monotonic() + timeout
    last_error = "not attempted"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310
                return response.status, response.read()
        except (OSError, urllib.error.URLError) as exc:
            last_error = str(exc)
            time.sleep(1)
    raise LocalStackError(f"Timed out waiting for {url}: {last_error}")


def _wait_exec(service: str, command: list[str], label: str, *, timeout: float = 90.0) -> str:
    deadline = time.monotonic() + timeout
    last_error = "not attempted"
    while time.monotonic() < deadline:
        result = _compose("exec", "-T", service, *command, capture=True)
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"PASS shell: {label} {output.splitlines()[-1] if output else 'ok'}")
            return output
        last_error = result.stderr.strip()
        time.sleep(1)
    raise LocalStackError(f"Timed out waiting for {label}: {last_error}")


def _http_json(
    url: str,
    *,
    method: str = "GET",
    payload: Any = None,
    auth: tuple[str, str] | None = None,
) -> Any:
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)  # noqa: S310
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if auth is not None:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        content = response.read().decode("utf-8")
        return json.loads(content) if content else None


def _wait_one_shot(service: str, *, timeout: float = 90.0) -> None:
    deadline = time.monotonic() + timeout
    container_id = ""
    while time.monotonic() < deadline:
        result = _compose("ps", "-aq", service, capture=True)
        container_id = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
        if container_id:
            break
        time.sleep(1)
    if not container_id:
        raise LocalStackError(f"Compose did not create one-shot service {service}")
    while time.monotonic() < deadline:
        result = _run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Status}} {{.State.ExitCode}}",
                container_id,
            ],
            capture=True,
        )
        if result.returncode:
            time.sleep(1)
            continue
        state = result.stdout.strip().split()
        if state and state[0] == "exited":
            if len(state) > 1 and state[1] == "0":
                print(f"PASS initialized: {service}")
                return
            raise LocalStackError(
                f"One-shot service {service} failed with state: {result.stdout.strip()}"
            )
        time.sleep(1)
    raise LocalStackError(f"Timed out waiting for one-shot service {service}")


def _wait_stack() -> None:
    checks = {
        "api health": "http://127.0.0.1:8000/health",
        "minio health": "http://127.0.0.1:9000/minio/health/live",
        "mailpit health": "http://127.0.0.1:8025/api/v1/info",
        "otel health": "http://127.0.0.1:13133/",
        "prometheus readiness": "http://127.0.0.1:9090/-/ready",
        "grafana health": "http://127.0.0.1:3000/api/health",
        "jaeger health": "http://127.0.0.1:16686/",
    }
    for name, url in checks.items():
        _wait_http(url)
        print(f"PASS ready: {name}")
    _wait_exec("mongo", ["mongosh", "--quiet", "--eval", "db.version()"], "MongoDB version")
    _wait_exec("valkey", ["valkey-cli", "ping"], "Valkey health")
    _wait_exec("valkey", ["valkey-cli", "INFO", "server"], "Valkey version")
    _wait_exec("rabbitmq", ["rabbitmq-diagnostics", "-q", "ping"], "RabbitMQ health")
    _wait_exec("rabbitmq", ["rabbitmqctl", "version"], "RabbitMQ version")
    _wait_exec(
        "redpanda", ["rpk", "cluster", "health", "--api-urls", "127.0.0.1:9644"], "Redpanda health"
    )
    _wait_exec("redpanda", ["rpk", "version"], "Redpanda version")


def _version_shell() -> None:
    health = json.loads(_wait_http("http://127.0.0.1:8000/health")[1])
    version = json.loads(_wait_http("http://127.0.0.1:8000/version")[1])
    expected = {"service": "platform-api", "version": "0.1.0", "status": "ok"}
    if health != expected or version != expected:
        raise LocalStackError(
            f"API health/version shell mismatch: health={health!r} version={version!r}"
        )
    print(f"PASS health/version shell: {health['service']} {health['version']}")


def _mongo_transaction() -> None:
    smoke_id = f"transaction-{uuid.uuid4().hex}"
    script = (
        "const smokeId = "
        + json.dumps(smoke_id)
        + "; const session = db.getMongo().startSession(); "
        "const smokeDb = session.getDatabase('lengeas_smoke'); "
        "try { session.startTransaction(); "
        "smokeDb.transactions.insertOne({_id: smokeId, state: 'created'}); "
        "smokeDb.transactions.updateOne({_id: smokeId}, {$set: {state: 'committed'}}); "
        "session.commitTransaction(); "
        "const result = smokeDb.transactions.findOne({_id: smokeId}); "
        "if (!result || result.state !== 'committed') { quit(2); } "
        "print('committed'); } finally { session.endSession(); }"
    )
    result = _compose("exec", "-T", "mongo", "mongosh", "--quiet", "--eval", script, capture=True)
    if result.returncode or "committed" not in result.stdout:
        raise LocalStackError(f"MongoDB transaction smoke failed: {result.stderr.strip()}")
    print("PASS MongoDB replica-set transaction: insert/update committed")


def _rabbit_publish_consume(values: dict[str, str]) -> None:
    user = values["RABBITMQ_DEFAULT_USER"]
    password = values["RABBITMQ_DEFAULT_PASS"]
    queue = f"lengeas.smoke.{uuid.uuid4().hex}"
    payload = f"rabbit-payload-{uuid.uuid4().hex}"
    encoded_queue = urllib.parse.quote(queue, safe="")
    base = "http://127.0.0.1:15672/api"
    try:
        _http_json(
            f"{base}/queues/%2F/{encoded_queue}",
            method="PUT",
            payload={"durable": False, "auto_delete": True},
            auth=(user, password),
        )
        _http_json(
            f"{base}/exchanges/%2F/amq.default/publish",
            method="POST",
            payload={
                "properties": {},
                "routing_key": queue,
                "payload": payload,
                "payload_encoding": "string",
            },
            auth=(user, password),
        )
        messages = _http_json(
            f"{base}/queues/%2F/{encoded_queue}/get",
            method="POST",
            payload={
                "count": 1,
                "ackmode": "ack_requeue_false",
                "encoding": "auto",
                "truncate": 50000,
            },
            auth=(user, password),
        )
        if not messages or messages[0].get("payload") != payload:
            raise LocalStackError(f"RabbitMQ payload mismatch: {messages!r}")
    finally:
        try:
            _http_json(f"{base}/queues/%2F/{encoded_queue}", method="DELETE", auth=(user, password))
        except (OSError, urllib.error.URLError):
            pass
    print("PASS RabbitMQ publish/consume: management API round trip")


def _redpanda_publish_consume() -> None:
    topic = f"lengeas-smoke-{uuid.uuid4().hex}"
    payload = f"redpanda-payload-{uuid.uuid4().hex}"
    try:
        create = _compose(
            "exec",
            "-T",
            "redpanda",
            "rpk",
            "topic",
            "create",
            topic,
            "--brokers",
            "redpanda:9092",
            capture=True,
        )
        if create.returncode:
            raise LocalStackError(f"Redpanda topic creation failed: {create.stderr.strip()}")
        produce = _compose(
            "exec",
            "-T",
            "redpanda",
            "rpk",
            "topic",
            "produce",
            topic,
            "--brokers",
            "redpanda:9092",
            input_text=payload + "\n",
            capture=True,
        )
        if produce.returncode:
            raise LocalStackError(f"Redpanda publish failed: {produce.stderr.strip()}")
        consume = _compose(
            "exec",
            "-T",
            "redpanda",
            "rpk",
            "topic",
            "consume",
            topic,
            "--brokers",
            "redpanda:9092",
            "--num",
            "1",
            "--format",
            "%v\\n",
            capture=True,
        )
        if consume.returncode or payload not in consume.stdout:
            raise LocalStackError(
                f"Redpanda consume failed: {consume.stderr.strip()} "
                f"output={consume.stdout.strip()!r}"
            )
    finally:
        _compose(
            "exec",
            "-T",
            "redpanda",
            "rpk",
            "topic",
            "delete",
            topic,
            "--brokers",
            "redpanda:9092",
            capture=True,
        )
    print("PASS Redpanda/Kafka publish/consume: topic round trip")


def _s3_put_get(values: dict[str, str]) -> None:
    payload = f"s3-payload-{uuid.uuid4().hex}"
    object_key = f"smoke/{uuid.uuid4().hex}/payload.txt"
    shell = (
        'mc alias set local http://minio:9000 "$MINIO_ROOT_USER" '
        '"$MINIO_ROOT_PASSWORD" >/dev/null; '
        f"printf '%s' {json.dumps(payload)} | mc pipe \"local/$MINIO_BUCKET/{object_key}\"; "
        f'got=$(mc cat "local/$MINIO_BUCKET/{object_key}"); test "$got" = {json.dumps(payload)}'
    )
    result = _compose("run", "--rm", "--no-deps", "minio-init", "sh", "-ec", shell, capture=True)
    if result.returncode:
        raise LocalStackError(f"MinIO S3 put/get failed: {result.stderr.strip()}")
    print("PASS MinIO S3-compatible put/get: object round trip")


def _trace_export() -> None:
    service = "lengeas-local-smoke"
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    now = time.time_ns()
    body = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [{"key": "service.name", "value": {"stringValue": service}}]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "lengeas.local.smoke"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": span_id,
                                "name": "local-platform-smoke",
                                "kind": 1,
                                "startTimeUnixNano": str(now),
                                "endTimeUnixNano": str(now + 1_000_000),
                                "status": {"code": 1},
                            }
                        ],
                    }
                ],
            }
        ]
    }
    request = urllib.request.Request(
        "http://127.0.0.1:4318/v1/traces",
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        if response.status not in (200, 202):
            raise LocalStackError(f"OTLP trace export returned HTTP {response.status}")
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            result = _http_json(f"http://127.0.0.1:16686/api/traces/{trace_id}")
            if result.get("data"):
                print("PASS trace export: OTLP Collector to Jaeger verified")
                return
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            pass
        time.sleep(1)
    raise LocalStackError(f"Trace export not visible in Jaeger for trace {trace_id}")


def up() -> int:
    _ensure_env()
    _require_docker()
    config = _compose("config", "--quiet", capture=True)
    if config.returncode:
        raise LocalStackError(f"Compose configuration failed: {config.stderr.strip()}")
    result = _compose("up", "--detach", "--remove-orphans")
    if result.returncode:
        raise LocalStackError("Compose startup failed")
    _wait_stack()
    _wait_one_shot("mongo-init")
    _wait_one_shot("minio-init")
    print("PASS local platform started: lengeas-local")
    return 0


def smoke() -> int:
    values = _ensure_env()
    _require_docker()
    _wait_stack()
    _version_shell()
    _mongo_transaction()
    _rabbit_publish_consume(values)
    _redpanda_publish_consume()
    _s3_put_get(values)
    _trace_export()
    print("PASS local smoke: all required dependency checks completed")
    return 0


def down() -> int:
    _ensure_env()
    _require_docker()
    result = _compose("down", "--volumes", "--remove-orphans")
    if result.returncode:
        raise LocalStackError("Compose shutdown failed")
    print("PASS local platform stopped and local volumes removed")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"up", "smoke", "down"}:
        print(f"usage: {Path(argv[0]).name} <up|smoke|down>", file=sys.stderr)
        return 2
    try:
        return {"up": up, "smoke": smoke, "down": down}[argv[1]]()
    except LocalStackError as exc:
        print(f"BLOCKED local stack: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
