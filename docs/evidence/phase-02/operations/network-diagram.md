# Network topology evidence

## Current development path

```text
Developer / synthetic probe
  -> Cloudflare authoritative DNS (DNS-only)
  -> public Caddy on LenGeas-Phase01-Server, us-east-1a
  -> API on 127.0.0.1:8000
  -> loopback-only Compose dependencies
```

TCP 80/443 are public for the development endpoint. TCP 22 is restricted to the operator's current `/32`. MongoDB, Valkey, RabbitMQ, Redpanda, MinIO, Mailpit, Jaeger, OpenTelemetry, Prometheus, Grafana, and the API origin port are not intended to be directly public.

The three-AZ ALB/ECS/PrivateLink topology is a disabled production target, not current Phase 02 infrastructure.
