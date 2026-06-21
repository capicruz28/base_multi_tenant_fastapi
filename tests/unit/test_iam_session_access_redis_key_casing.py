"""IAM-BE-TOKEN-ID-CASING-PATCH-01: clave Redis canónica para session access mapping."""
from uuid import UUID

from app.modules.auth.application.services.refresh_token_service import (
    RefreshTokenService,
    SESSION_ACCESS_JTI_PREFIX,
)

TOKEN_UUID = UUID("f8ee8bfe-276d-45da-ae0e-1fadfcbc2ed4")
TOKEN_UPPER_STR = "F8EE8BFE-276D-45DA-AE0E-1FADFCBC2ED4"
CANONICAL_KEY = (
    f"{SESSION_ACCESS_JTI_PREFIX}f8ee8bfe-276d-45da-ae0e-1fadfcbc2ed4"
)


def test_session_access_redis_key_uuid_lowercase():
    assert (
        RefreshTokenService._session_access_redis_key(TOKEN_UUID)
        == CANONICAL_KEY
    )


def test_session_access_redis_key_uppercase_string():
    assert (
        RefreshTokenService._session_access_redis_key(TOKEN_UPPER_STR)
        == CANONICAL_KEY
    )


def test_session_access_redis_key_uuid_and_string_equivalent():
    assert RefreshTokenService._session_access_redis_key(
        TOKEN_UUID
    ) == RefreshTokenService._session_access_redis_key(TOKEN_UPPER_STR)
