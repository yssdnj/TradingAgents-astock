import time

from web.auth import create_remember_token, verify_remember_token


def test_remember_token_round_trip_for_known_user():
    users = {"alice": {"password": "secret", "role": "admin"}}

    token = create_remember_token("alice", "admin", "signing-secret", now=1000, ttl_seconds=60)

    assert verify_remember_token(token, users, "signing-secret", now=1010) == {
        "username": "alice",
        "role": "admin",
    }


def test_remember_token_rejects_expired_token():
    users = {"alice": {"password": "secret", "role": "admin"}}
    token = create_remember_token("alice", "admin", "signing-secret", now=1000, ttl_seconds=60)

    assert verify_remember_token(token, users, "signing-secret", now=1061) is None


def test_remember_token_rejects_tampering():
    users = {"alice": {"password": "secret", "role": "admin"}}
    token = create_remember_token("alice", "admin", "signing-secret", now=time.time(), ttl_seconds=60)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    assert verify_remember_token(tampered, users, "signing-secret") is None


def test_remember_token_rejects_changed_user_role():
    token = create_remember_token("alice", "admin", "signing-secret", now=1000, ttl_seconds=60)
    users = {"alice": {"password": "secret", "role": "viewer"}}

    assert verify_remember_token(token, users, "signing-secret", now=1010) is None
