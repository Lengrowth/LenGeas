"""Health/version shell for the match service."""

from apps.api.app import ShellResponse


def health() -> ShellResponse:
    return {"service": "match-service", "version": "0.1.0", "status": "ok"}


def version() -> ShellResponse:
    return health()
