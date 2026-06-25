"""Tipos de dominio ligero IAM Session Management V2 (C19)."""
from app.modules.auth.application.session.replay_detection_result import ReplayDetectionResult
from app.modules.auth.application.session.revoke_result import RevokeResult
from app.modules.auth.application.session.revoked_reason import RevokedReason, V1_LEGACY_REVOKED_REASONS
from app.modules.auth.application.session.revoked_reason_mappers import (
    to_family_reason,
    to_session_reason,
    to_token_reason,
)
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult
from app.modules.auth.application.session.session_creation_result import SessionCreationResult
from app.modules.auth.application.session.session_probe_result import SessionProbeResult
from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled
from app.modules.auth.application.session.token_context import TokenContext

__all__ = [
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
]
