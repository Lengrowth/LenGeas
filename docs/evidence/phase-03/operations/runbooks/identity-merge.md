# Identity merge

Create a preview before committing. Every profile collision requires `source` or `target`; currencies are never summed. Commit with an idempotency key under trusted tenant scope. The transaction boundary validates all choices before irreversible tombstoning, and repeated keys return the original target without duplicating entitlements.
