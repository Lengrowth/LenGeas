# Negative controls

The production-target negative controls are machine-listed as P02-NEG-001 through P02-NEG-013. Static policy coverage is present. Live rejection evidence is intentionally not claimed because the production topology is not active.

For the current development host, the enforced boundary is synthetic non-sensitive data only, loopback-only dependency ports, public Caddy on 80/443, and SSH restricted to the operator `/32`. The development exceptions cannot satisfy production qualification.
