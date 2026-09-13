"""Health/version shell for the realtime gateway."""

from apps.api.app import ShellResponse


def health() -> ShellResponse:
    return {"service": "realtime-gateway", "version": "0.1.0", "status": "ok"}


def version() -> ShellResponse:
    return health()

