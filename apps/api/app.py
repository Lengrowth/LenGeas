"""Health/version shell for the API composition root."""

from typing import Final, TypedDict

SERVICE: Final = "platform-api"
VERSION: Final = "0.1.0"


class ShellResponse(TypedDict):
    service: str
    version: str
    status: str


def health() -> ShellResponse:
    return {"service": SERVICE, "version": VERSION, "status": "ok"}


def version() -> ShellResponse:
    return {"service": SERVICE, "version": VERSION, "status": "ok"}
