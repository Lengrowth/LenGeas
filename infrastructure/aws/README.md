# Development AWS server

The Phase 01 server is now the explicitly authorized Phase 02 development foundation. It is a `t3.medium` EC2 host named `LenGeas-Phase01-Server` in `us-east-1a`. It is not a production environment. The
developer workstation never installs or runs Docker. `phase-01-user-data.sh`
installs Docker Engine and Compose v2 on the server, consumes a source archive
of the already-pushed commit, generates the server-only `.env`, runs the pinned
Compose stack, and configures Caddy for `games.lengrowth.com`. The archive
transfer keeps the private GitHub repository credential-free on the host.

## Private source transfer

From a clean checkout, create and upload the exact pushed commit, then upload
the bootstrap script and run it on the server:

```sh
git archive --format=tar --output=lengeas-source.tar HEAD
scp -i ~/.ssh/lenquant.pem lengeas-source.tar ubuntu@SERVER:/opt/lengeas-source.tar
scp -i ~/.ssh/lenquant.pem infrastructure/aws/phase-01-user-data.sh ubuntu@SERVER:/opt/phase-01-user-data.sh
ssh -i ~/.ssh/lenquant.pem ubuntu@SERVER sudo bash /opt/phase-01-user-data.sh
```

The archive is not committed and must be removed from the workstation after the
transfer if it is no longer needed.

## Network boundary

- Only TCP 80 and 443 are public ingress.
- SSH is restricted to the operator's current `/32` address at provisioning.
- Compose services bind to `127.0.0.1`; MongoDB, Valkey, RabbitMQ, Redpanda,
  MinIO, Mailpit, Jaeger, OpenTelemetry, Prometheus, Grafana, and the API shell
  are not directly exposed by the security group.
- Caddy is the only public reverse proxy and forwards to the API shell on
  `127.0.0.1:8000`.

The root EBS volume is currently unencrypted, the instance has no IAM instance profile, and detailed monitoring is disabled. Only synthetic, non-sensitive development data may be stored on the host. These limitations must be resolved by the production activation plan; they must not be hidden or presented as production controls.

## DNS

Create or update the exact `A` record `games.lengrowth.com` to the instance's
public IPv4 address. Keep the record DNS-only while Caddy obtains its
certificate, then enable the Cloudflare proxy only after HTTPS has been
verified end to end. While the record remains DNS-only, clients reach the Caddy
origin directly; this must not be described as Cloudflare-proxied origin
protection.

ADR-0011 keeps this DNS-only behavior for the development stage. Production rollout requires a separately verified Cloudflare-proxied and origin-authenticated path before traffic moves.

## Operator verification

```sh
sudo cat /var/lib/lengeas-phase-01-ready
sudo docker compose --project-name lengeas-local --env-file /opt/lengeas/.env --file /opt/lengeas/compose.yaml ps
curl --fail https://games.lengrowth.com/health
curl --fail https://games.lengrowth.com/version
```
