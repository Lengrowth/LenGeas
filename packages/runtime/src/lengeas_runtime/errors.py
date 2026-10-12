"""Stable, deterministic runtime failures."""

from __future__ import annotations


class RuntimeErrorCode(ValueError):
    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}
