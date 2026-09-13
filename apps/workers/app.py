"""Health/version shell for background workers."""

from apps.api.app import ShellResponse


def health() -> ShellResponse:
    return {"service": "workers", "version": "0.1.0", "status": "ok"}


def version() -> ShellResponse:
    return health()

