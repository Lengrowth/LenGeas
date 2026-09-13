# Cloudflare origin protection

Cloudflare is the only public edge. The AWS ALB accepts Cloudflare source ranges and a rotating authenticated origin header; its DNS name is not advertised.

## Verify

Probe the public hostname through Cloudflare, then probe the direct ALB name from an authorized network. The direct-origin request must fail closed. Record status, request ID, source class, and rule version without recording tokens or headers.

## Rotate

Create the new empty secret container, deploy the Worker and origin rule using the new version, verify a synthetic request, then revoke the old value. Roll back to the prior version if authenticated traffic fails. Do not retire the Phase 01 DNS-only endpoint until the owner authorizes cutover after replacement verification.
