"""
DedicatedStorageMetadataService — S8 register metadata (PR-F4-09).

Registra ``cliente_conexion`` principal en CP de forma idempotente.
"""
from __future__ import annotations

import logging
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import ConflictError, ValidationError
from app.infrastructure.provisioning.dedicated_storage_metadata_types import (
    DedicatedStorageMetadataRequest,
    DedicatedStorageMetadataResult,
)
from app.modules.tenant.application.services.conexion_service import ConexionService
from app.modules.tenant.presentation.schemas import ConexionCreate, ConexionRead

logger = logging.getLogger(__name__)

# Actor interno saga — ``creado_por_usuario_id`` nullable sin FK en CP.
PROVISIONING_INTERNAL_ACTOR_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class DedicatedStorageMetadataService:
    """Adaptador S8 — ``cliente_conexion`` principal vía ``ConexionService``."""

    async def register_primary_connection(
        self,
        request: DedicatedStorageMetadataRequest,
    ) -> DedicatedStorageMetadataResult:
        existing = await ConexionService.obtener_conexion_principal(request.cliente_id)
        if existing is not None:
            self._assert_metadata_consistent(existing, request)
            logger.info(
                "S8 metadata idempotent skip cliente_id=%s conexion_id=%s",
                request.cliente_id,
                existing.conexion_id,
            )
            return DedicatedStorageMetadataResult(
                conexion_id=existing.conexion_id,
                created=False,
                idempotent=True,
            )

        conexion_data = ConexionCreate(
            cliente_id=request.cliente_id,
            servidor=request.servidor,
            puerto=request.puerto or settings.PROVISIONING_DDL_PORT,
            nombre_bd=request.database_name,
            usuario=request.app_login_name,
            password=request.app_login_password,
            tipo_bd="sqlserver",
            es_conexion_principal=True,
        )

        try:
            created = await ConexionService.crear_conexion(
                conexion_data,
                PROVISIONING_INTERNAL_ACTOR_USER_ID,
            )
        except ConflictError as exc:
            if exc.internal_code != "PRIMARY_CONNECTION_CONFLICT":
                raise
            raced = await ConexionService.obtener_conexion_principal(request.cliente_id)
            if raced is None:
                raise ConflictError(
                    detail="Conflicto de conexión principal sin fila recuperable.",
                    internal_code="PROVISIONING_METADATA_FAILED",
                ) from exc
            self._assert_metadata_consistent(raced, request)
            return DedicatedStorageMetadataResult(
                conexion_id=raced.conexion_id,
                created=False,
                idempotent=True,
            )

        return DedicatedStorageMetadataResult(
            conexion_id=created.conexion_id,
            created=True,
            idempotent=False,
        )

    @staticmethod
    def _assert_metadata_consistent(
        existing: ConexionRead,
        request: DedicatedStorageMetadataRequest,
    ) -> None:
        mismatches: list[str] = []
        if existing.servidor != request.servidor:
            mismatches.append("servidor")
        if existing.nombre_bd != request.database_name:
            mismatches.append("nombre_bd")
        if mismatches:
            raise ConflictError(
                detail=(
                    "Conexión principal existente no coincide con allocation saga: "
                    f"{', '.join(mismatches)}."
                ),
                internal_code="PROVISIONING_METADATA_FAILED",
            )


    async def cleanup_primary_connection(self, cliente_id: UUID) -> bool:
        """
        Compensación S8 — soft-delete conexión principal (idempotente).

        Returns:
            True si se desactivó una conexión activa; False si ya estaba limpia.
        """
        existing = await ConexionService.obtener_conexion_principal(cliente_id)
        if existing is None:
            logger.info(
                "S8 cleanup idempotent skip — sin conexión principal cliente_id=%s",
                cliente_id,
            )
            return False

        try:
            await ConexionService.desactivar_conexion(existing.conexion_id)
        except ValidationError as exc:
            if exc.internal_code == "CONNECTION_ALREADY_INACTIVE":
                return False
            raise

        logger.info(
            "S8 cleanup desactivó conexión principal cliente_id=%s conexion_id=%s",
            cliente_id,
            existing.conexion_id,
        )
        return True


__all__ = [
    "DedicatedStorageMetadataService",
    "PROVISIONING_INTERNAL_ACTOR_USER_ID",
]
