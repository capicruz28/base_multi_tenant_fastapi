"""ScopeResolver — traduce contexto a ScopeKey canónico (F16 `13`)."""

from __future__ import annotations

from uuid import UUID

from app.core.codigo.enums import ScopeType
from app.core.codigo.generation_context import GenerationContext
from app.core.codigo.scope_key import ScopeKey
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.exceptions import ValidationError


class ScopeResolver:
    @staticmethod
    def resolve(defn: SequenceDefinition, context: GenerationContext) -> ScopeKey:
        client_id = context.client_id
        scope = defn.scope_type

        if scope == ScopeType.TENANT:
            return ScopeKey(
                sequence_key=defn.sequence_key,
                scope_type=scope,
                client_id=client_id,
            )

        if scope == ScopeType.EMPRESA:
            empresa_id = context.empresa_id
            if empresa_id is None:
                raise ValidationError(
                    detail="Sesión incompleta: empresa_id requerido para scope EMPRESA.",
                    internal_code="SCOPE_EMPRESA_REQUIRED",
                )
            return ScopeKey(
                sequence_key=defn.sequence_key,
                scope_type=scope,
                client_id=client_id,
                empresa_id=empresa_id,
            )

        if scope == ScopeType.ALMACEN:
            almacen_id = context.almacen_id
            if almacen_id is None:
                raise ValidationError(
                    detail="Contexto incompleto: almacen_id requerido para scope ALMACEN.",
                    internal_code="SCOPE_ALMACEN_REQUIRED",
                )
            return ScopeKey(
                sequence_key=defn.sequence_key,
                scope_type=scope,
                client_id=client_id,
                almacen_id=almacen_id,
                empresa_id=context.empresa_id,
            )

        if scope == ScopeType.PUNTO_VENTA:
            if context.empresa_id is None or context.punto_venta_id is None:
                raise ValidationError(
                    detail="Contexto incompleto: empresa_id y punto_venta_id requeridos.",
                    internal_code="SCOPE_PV_REQUIRED",
                )
            return ScopeKey(
                sequence_key=defn.sequence_key,
                scope_type=scope,
                client_id=client_id,
                empresa_id=context.empresa_id,
                punto_venta_id=context.punto_venta_id,
            )

        if scope == ScopeType.SERIE_FISCAL:
            if context.empresa_id is None or context.serie_id is None:
                raise ValidationError(
                    detail="Contexto incompleto: empresa_id y serie_id requeridos para emisión fiscal.",
                    internal_code="SCOPE_SERIE_FISCAL_REQUIRED",
                )
            return ScopeKey(
                sequence_key=defn.sequence_key,
                scope_type=scope,
                client_id=client_id,
                empresa_id=context.empresa_id,
                serie_id=context.serie_id,
            )

        raise ValidationError(
            detail=f"scope_type no soportado: {scope}",
            internal_code="SCOPE_TYPE_INVALID",
        )

    @staticmethod
    def cfg_row_dimensions(scope_key: ScopeKey) -> dict[str, UUID | None]:
        """Dimensiones persistidas en cfg_codigo_secuencia."""
        return {
            "empresa_id": scope_key.empresa_id if scope_key.scope_type != ScopeType.ALMACEN else scope_key.empresa_id,
            "almacen_id": scope_key.almacen_id,
            "punto_venta_id": scope_key.punto_venta_id,
        }
