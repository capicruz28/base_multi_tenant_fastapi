"""
Infraestructura ORG reutilizable para CodigoGeneracionGateway (Ola 1.1).

Delegación delgada al motor congelado. Sin conocimiento de entidades concretas
(cargo, sucursal, empresa, etc.) — solo sequence_key y dimensiones de scope.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codigo.enums import GenerationOperation
from app.core.codigo.gateway.codigo_generacion_gateway import CodigoGeneracionGateway
from app.core.codigo.generation_context import GenerationContext


def _normalize_manual_input(manual_code: str | None) -> str | None:
    if manual_code is None:
        return None
    stripped = manual_code.strip()
    return stripped if stripped else None


class OrgCodigoGenerationService:
    """Resuelve códigos de negocio vía CodigoGeneracionGateway para el módulo ORG."""

    @staticmethod
    def build_tenant_context(
        client_id: UUID,
        *,
        manual_code: str | None = None,
        operation: GenerationOperation = GenerationOperation.CREATE,
    ) -> GenerationContext:
        """Contexto scope TENANT (p. ej. secuencias con empresa_id=None en cfg)."""
        return GenerationContext(
            client_id=client_id,
            operation=operation,
            manual_code=_normalize_manual_input(manual_code),
        )

    @staticmethod
    def build_empresa_context(
        client_id: UUID,
        empresa_id: UUID,
        *,
        manual_code: str | None = None,
        operation: GenerationOperation = GenerationOperation.CREATE,
    ) -> GenerationContext:
        """Contexto scope EMPRESA (requiere empresa_id en sesión operativa)."""
        return GenerationContext(
            client_id=client_id,
            empresa_id=empresa_id,
            operation=operation,
            manual_code=_normalize_manual_input(manual_code),
        )

    @staticmethod
    def build_context(
        client_id: UUID,
        *,
        empresa_id: UUID | None = None,
        manual_code: str | None = None,
        operation: GenerationOperation = GenerationOperation.CREATE,
    ) -> GenerationContext:
        """Construye GenerationContext a partir de dimensiones de scope disponibles."""
        return GenerationContext(
            client_id=client_id,
            empresa_id=empresa_id,
            operation=operation,
            manual_code=_normalize_manual_input(manual_code),
        )

    @staticmethod
    async def resolve_codigo_for_create(
        sequence_key: str,
        *,
        session: AsyncSession,
        client_id: UUID,
        empresa_id: UUID | None = None,
        manual_code: str | None = None,
        operation: GenerationOperation = GenerationOperation.CREATE,
    ) -> str:
        """
        Resuelve el código final para un alta (CREATE).

        - manual_code omitido/vacío → allocate AUTO_GENERATE
        - manual_code presente → allocate ACCEPT_MANUAL (según política catálogo)
        """
        context = OrgCodigoGenerationService.build_context(
            client_id,
            empresa_id=empresa_id,
            manual_code=manual_code,
            operation=operation,
        )
        result = await CodigoGeneracionGateway.allocate(
            sequence_key,
            context,
            session,
        )
        return result.code
