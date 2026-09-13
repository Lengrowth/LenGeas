# Phase 01 AWS server

The Phase 01 server is an explicitly authorized, non-production EC2 host. The
developer workstation never installs or runs Docker. `phase-01-user-data.sh`
installs Docker Engine and Compose v2 on the server, clones `main`, generates
the server-only `.env`, runs the pinned Compose stack, and configures Caddy for
`games.lengrowth.com`.

## Network boundary

- Only TCP 80 and 443 are public ingress.
- SSH is restricted to the operator's current `/32` address at provisioning.
- Compose services bind to `127.0.0.1`; MongoDB, Valkey, RabbitMQ, Redpanda,
  MinIO, Mailpit, Jaeger, OpenTelemetry, Prometheus, Grafana, and the API shell
  are not directly exposed by the security group.
- Caddy is the only public reverse proxy and forwards to the API shell on
  `127.0.0.1:8000`.

## DNS

Create or update the exact `A` record `games.lengrowth.com` to the instance's
public IPv4 address. Keep the record DNS-only while Caddy obtains its
certificate, then enable the Cloudflare proxy only after HTTPS has been
verified end to end.

## Operator verification

```sh
sudo cat /var/lib/lengeas-phase-01-ready
sudo docker compose --project-name lengeas-local --env-file /opt/lengeas/.env --file /opt/lengeas/compose.yaml ps
curl --fail https://games.lengrowth.com/health
curl --fail https://games.lengrowth.com/version
```
