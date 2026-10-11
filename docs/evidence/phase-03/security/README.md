# Phase 03 security evidence

The security layer covers forged tenant scopes, cross-studio access, expired support grants, operator MFA bypass, guest replay, device credential rotation reuse, and provider JWT claim/signature failures. No high or critical Phase 03 finding is open.

The CodeQL information-exposure finding in the idempotency response path is remediated: clients receive the stable `idempotency_conflict` code and fixed safe message. A regression test verifies that exception text is not returned. The PyMongo lock entry was also updated from 4.14.1 to 4.18.3 after hosted dependency review flagged GHSA-vp6j-j7w5-5xjj and GHSA-v4x9-3549-crwv. Hosted CodeQL and dependency-review verification remain pending.
