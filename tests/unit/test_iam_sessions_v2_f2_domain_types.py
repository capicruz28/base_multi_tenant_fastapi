"""F2 — tests unitarios tipos de dominio IAM Session V2 (C19)."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.modules.auth.application.session import (
    ReplayDetectionResult,
    RevokeResult,
    RevokedReason,
    RotateOutcome,
    RotateResult,
    SessionCreationResult,
    SessionProbeResult,
    TokenContext,
    V1_LEGACY_REVOKED_REASONS,
    to_family_reason,
    to_session_reason,
    to_token_reason,
)


CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
TOKEN_ID = uuid4()
OLD_TOKEN_ID = uuid4()
NEW_TOKEN_ID = uuid4()
EXPIRES_AT = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        (RevokedReason.USER_LOGOUT, "logout"),
        (RevokedReason.LOGOUT_ALL, "logout"),
        (RevokedReason.ADMIN_REVOKE, "admin_force"),
        (RevokedReason.PASSWORD_CHANGE, "password_reset"),
        (RevokedReason.REPLAY_DETECTED, "security"),
        (RevokedReason.IDLE_TIMEOUT, "expired"),
        (RevokedReason.SESSION_LIMIT, "admin_force"),
        (RevokedReason.USER_DEACTIVATED, "admin_force"),
        (RevokedReason.USER_DELETED, "admin_force"),
        (RevokedReason.ABSOLUTE_TTL, "expired"),
    ],
)
def test_f2_to_session_reason_mapping(reason: RevokedReason, expected: str):
    assert to_session_reason(reason) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        (RevokedReason.USER_LOGOUT, "logout"),
        (RevokedReason.LOGOUT_ALL, "logout"),
        (RevokedReason.ADMIN_REVOKE, "logout"),
        (RevokedReason.PASSWORD_CHANGE, "password_reset"),
        (RevokedReason.REPLAY_DETECTED, "replay_detected"),
        (RevokedReason.IDLE_TIMEOUT, None),
        (RevokedReason.SESSION_LIMIT, "family_compromised"),
        (RevokedReason.USER_DEACTIVATED, "logout"),
        (RevokedReason.USER_DELETED, "logout"),
        (RevokedReason.ABSOLUTE_TTL, None),
    ],
)
def test_f2_to_token_reason_mapping(reason: RevokedReason, expected: str | None):
    assert to_token_reason(reason) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        (RevokedReason.USER_LOGOUT, "session_revoked"),
        (RevokedReason.LOGOUT_ALL, "session_revoked"),
        (RevokedReason.ADMIN_REVOKE, "admin_force"),
        (RevokedReason.PASSWORD_CHANGE, "password_reset"),
        (RevokedReason.REPLAY_DETECTED, "replay_detected"),
        (RevokedReason.IDLE_TIMEOUT, "session_revoked"),
        (RevokedReason.SESSION_LIMIT, "session_revoked"),
        (RevokedReason.USER_DEACTIVATED, "admin_force"),
        (RevokedReason.USER_DELETED, "admin_force"),
        (RevokedReason.ABSOLUTE_TTL, "session_revoked"),
    ],
)
def test_f2_to_family_reason_mapping(reason: RevokedReason, expected: str):
    assert to_family_reason(reason) == expected


@pytest.mark.unit
@pytest.mark.parametrize("legacy", list(V1_LEGACY_REVOKED_REASONS))
def test_f2_legacy_revoked_reasons_raise_on_mappers(legacy: RevokedReason):
    with pytest.raises(ValueError, match="legacy V1"):
        to_session_reason(legacy)
    with pytest.raises(ValueError, match="legacy V1"):
        to_token_reason(legacy)
    with pytest.raises(ValueError, match="legacy V1"):
        to_family_reason(legacy)


@pytest.mark.unit
def test_f2_new_revoked_reason_members_present():
    assert RevokedReason.REPLAY_DETECTED == "REPLAY_DETECTED"
    assert RevokedReason.ABSOLUTE_TTL == "ABSOLUTE_TTL"


@pytest.mark.unit
@pytest.mark.parametrize(
    "outcome",
    [
        RotateOutcome.NOT_FOUND,
        RotateOutcome.EXPIRED,
        RotateOutcome.ALREADY_REVOKED,
        RotateOutcome.ALREADY_ROTATED,
        RotateOutcome.USER_MISMATCH,
        RotateOutcome.IDLE_TIMEOUT,
        RotateOutcome.COMPROMISED,
        RotateOutcome.FAMILY_REVOKED,
        RotateOutcome.SESSION_EXPIRED,
        RotateOutcome.ALREADY_USED,
    ],
)
def test_f2_rotate_result_success_only_on_rotated(outcome: RotateOutcome):
    result = RotateResult(outcome=outcome, cliente_id=CLIENTE_ID)
    assert result.success is False


@pytest.mark.unit
def test_f2_rotate_result_success_true_only_when_rotated():
    result = RotateResult(
        outcome=RotateOutcome.ROTATED,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        old_token_id=OLD_TOKEN_ID,
        new_token_id=NEW_TOKEN_ID,
    )
    assert result.success is True
    assert result.idle_expired is False


@pytest.mark.unit
def test_f2_rotate_result_idle_expired_flag():
    result = RotateResult(outcome=RotateOutcome.IDLE_TIMEOUT, cliente_id=CLIENTE_ID)
    assert result.idle_expired is True


@pytest.mark.unit
def test_f2_rotate_outcome_v2_members_present():
    assert RotateOutcome.COMPROMISED == "compromised"
    assert RotateOutcome.FAMILY_REVOKED == "family_revoked"
    assert RotateOutcome.SESSION_EXPIRED == "session_expired"
    assert RotateOutcome.ALREADY_USED == "already_used"


@pytest.mark.unit
def test_f2_session_creation_result_frozen():
    result = SessionCreationResult(
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=TOKEN_ID,
        expires_at=EXPIRES_AT,
    )
    assert result.session_id == SESSION_ID
    assert result.family_id == FAMILY_ID
    assert result.token_id == TOKEN_ID
    assert result.expires_at == EXPIRES_AT
    with pytest.raises(AttributeError):
        result.session_id = uuid4()  # type: ignore[misc]


@pytest.mark.unit
def test_f2_session_probe_result_defaults_fail_soft():
    probe = SessionProbeResult()
    assert probe.current_session_id is None
    assert probe.current_token_id is None
    assert probe.is_active is False


@pytest.mark.unit
def test_f2_session_probe_result_with_ids():
    probe = SessionProbeResult(
        current_session_id=SESSION_ID,
        current_token_id=TOKEN_ID,
        is_active=True,
    )
    assert probe.is_active is True


@pytest.mark.unit
def test_f2_token_context_aggregate():
    session_row = {"session_id": str(SESSION_ID), "is_active": True}
    family_row = {"family_id": str(FAMILY_ID), "is_compromised": False}
    token_row = {"token_id": str(TOKEN_ID), "is_used": False}
    ctx = TokenContext(
        cliente_id=CLIENTE_ID,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=TOKEN_ID,
        session_row=session_row,
        family_row=family_row,
        token_row=token_row,
    )
    assert ctx.session_row["is_active"] is True
    assert ctx.token_row["is_used"] is False


@pytest.mark.unit
def test_f2_replay_detection_result_fields():
    result = ReplayDetectionResult(
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=TOKEN_ID,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
    )
    assert result.session_id == SESSION_ID


@pytest.mark.unit
def test_f2_revoke_result_idempotent_semantics():
    active = RevokeResult(session_id=SESSION_ID, was_active=True, already_revoked=False)
    idempotent = RevokeResult(session_id=SESSION_ID, was_active=False, already_revoked=True)
    assert active.was_active is True
    assert idempotent.already_revoked is True


@pytest.mark.unit
def test_f2_session_package_exports_all_domain_types():
    from app.modules.auth.application import session as session_pkg

    expected = {
        "ReplayDetectionResult",
        "RevokeResult",
        "RevokedReason",
        "RotateOutcome",
        "RotateResult",
        "SessionCreationResult",
        "SessionProbeResult",
        "TokenContext",
        "V1_LEGACY_REVOKED_REASONS",
        "is_session_v2_enabled",
        "to_family_reason",
        "to_session_reason",
        "to_token_reason",
    }
    assert expected.issubset(set(session_pkg.__all__))
