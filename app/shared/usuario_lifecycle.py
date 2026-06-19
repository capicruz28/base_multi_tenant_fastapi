"""Invariantes del ciclo de vida de Usuario (IAM-DOMAIN-01 / IAM-BE-02)."""

from app.core.exceptions import ValidationError


def assert_usuario_lifecycle_valid(es_activo: bool, es_eliminado: bool) -> None:
    """
    Garantiza que no persista el estado inválido es_activo=true AND es_eliminado=true.
    """
    if es_activo and es_eliminado:
        raise ValidationError(
            detail=(
                "Estado de usuario inválido: no puede estar activo y eliminado simultáneamente."
            ),
            internal_code="USER_LIFECYCLE_INVALID",
        )


def assert_usuario_deactivate_payload(es_activo: bool) -> None:
    """Desactivar: únicamente es_activo=false (es_eliminado no se modifica)."""
    if es_activo:
        return
    assert_usuario_lifecycle_valid(es_activo=False, es_eliminado=False)


def assert_usuario_delete_state(es_activo: bool, es_eliminado: bool) -> None:
    """Eliminar (soft delete): es_activo=false AND es_eliminado=true."""
    assert_usuario_lifecycle_valid(es_activo, es_eliminado)
    if es_activo or not es_eliminado:
        raise ValidationError(
            detail="Estado post-eliminación inválido.",
            internal_code="USER_DELETE_STATE_INVALID",
        )


def assert_usuario_reactivate_state(es_activo: bool, es_eliminado: bool) -> None:
    """Reactivar: es_activo=true AND es_eliminado=false."""
    assert_usuario_lifecycle_valid(es_activo, es_eliminado)
    if not es_activo or es_eliminado:
        raise ValidationError(
            detail="Estado post-reactivación inválido.",
            internal_code="USER_REACTIVATE_STATE_INVALID",
        )
