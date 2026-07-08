"""Remember-me login token helpers for the Streamlit web UI."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(payload_b64: str, secret: str) -> str:
    return _b64encode(hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest())


def create_remember_token(
    username: str,
    role: str,
    secret: str,
    *,
    now: float | None = None,
    ttl_seconds: int = 30 * 24 * 60 * 60,
) -> str:
    issued_at = int(time.time() if now is None else now)
    payload = {
        "v": 1,
        "username": username,
        "role": role,
        "exp": issued_at + ttl_seconds,
    }
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    return f"{payload_b64}.{_sign(payload_b64, secret)}"


def verify_remember_token(
    token: str,
    users: dict[str, dict[str, str]],
    secret: str,
    *,
    now: float | None = None,
) -> dict[str, str] | None:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None

    expected = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected):
        return None

    try:
        payload: dict[str, Any] = json.loads(_b64decode(payload_b64))
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get("v") != 1:
        return None
    if int(payload.get("exp", 0)) < int(time.time() if now is None else now):
        return None

    username = str(payload.get("username", ""))
    role = str(payload.get("role", ""))
    user = users.get(username)
    if not user or user.get("role") != role:
        return None

    return {"username": username, "role": role}


def remember_secret(users_raw: str, configured_secret: str | None = None) -> str:
    if configured_secret:
        return configured_secret
    return hashlib.sha256(users_raw.encode("utf-8")).hexdigest()
