"""Unit tests for Argon2 password hashing and JWT RBAC authentication."""

from __future__ import annotations

import uuid
import pytest

from app.domain.enums import UserRole
from app.domain.exceptions import AuthenticationError
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_api_key,
    hash_password,
    verify_password,
)


def test_argon2_password_hashing() -> None:
    """Test Argon2 hash and verification."""
    password = "super_secure_demo_password"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2")
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_access_token_lifecycle() -> None:
    """Test generating and decoding JWT access tokens."""
    uid = uuid.uuid4()
    username = "test_analyst"
    role = UserRole.ANALYST

    token = create_access_token(uid, username, role)
    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == str(uid)
    assert payload["username"] == username
    assert payload["role"] == "analyst"
    assert payload["type"] == "access"


def test_jwt_token_type_mismatch() -> None:
    """Test that decoding a refresh token as an access token raises AuthenticationError."""
    uid = uuid.uuid4()
    refresh_tok = create_refresh_token(uid, "test_admin", UserRole.ADMIN)

    with pytest.raises(AuthenticationError):
        decode_token(refresh_tok, expected_type="access")


def test_api_key_hashing() -> None:
    """Test deterministic API key SHA-256 hash."""
    key = "sentinelchain-demo-api-key"
    h1 = hash_api_key(key)
    h2 = hash_api_key(key)
    assert h1 == h2
    assert len(h1) == 64
