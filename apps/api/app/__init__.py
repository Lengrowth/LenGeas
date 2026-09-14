"""FastAPI composition package."""

from typing import Final, TypedDict

from .main import create_app

SERVICE: Final = "platform-api"
VERSION: Final = "0.3.0"


class ShellResponse(TypedDict):
    service: str
    version: str
    status: str


def health() -> ShellResponse:
    return {"service": SERVICE, "version": VERSION, "status": "ok"}


def version() -> ShellResponse:
    return {"service": SERVICE, "version": VERSION, "status": "ok"}


__all__ = ["create_app", "health", "version", "ShellResponse"]
