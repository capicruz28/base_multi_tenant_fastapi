"""CfgSequenceStore — persistencia cfg_codigo_secuencia."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codigo.enums import CodePolicy, ScopeType
from app.core.codigo.platform_initial_policy import platform_initial_generation_policy
from app.core.codigo.scope_key import ScopeKey
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.database.tables import CfgCodigoSecuenciaTable


@dataclass(frozen=True, slots=True)
class CfgSequenceRow:
    secuencia_id: UUID
    cliente_id: UUID
    sequence_key: str
    scope_type: str
    scope_fingerprint: str
    empresa_id: UUID | None
    almacen_id: UUID | None
    punto_venta_id: UUID | None
    prefijo: str
    separador: str
    longitud_numero: int
    ultimo_numero: int
    numero_inicial: int
    es_activo: bool
    generation_policy: CodePolicy = CodePolicy.AUTO_DEFAULT

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> CfgSequenceRow:
        return cls(
            secuencia_id=UUID(str(row["secuencia_id"])),
            cliente_id=UUID(str(row["cliente_id"])),
            sequence_key=str(row["sequence_key"]),
            scope_type=str(row["scope_type"]),
            scope_fingerprint=str(row["scope_fingerprint"]),
            empresa_id=UUID(str(row["empresa_id"])) if row.get("empresa_id") else None,
            almacen_id=UUID(str(row["almacen_id"])) if row.get("almacen_id") else None,
            punto_venta_id=UUID(str(row["punto_venta_id"])) if row.get("punto_venta_id") else None,
            prefijo=str(row["prefijo"]),
            separador=str(row.get("separador") or ""),
            longitud_numero=int(row["longitud_numero"]),
            ultimo_numero=int(row["ultimo_numero"]),
            numero_inicial=int(row.get("numero_inicial", 1)),
            es_activo=bool(row.get("es_activo", True)),
            generation_policy=CodePolicy(
                str(row.get("generation_policy", CodePolicy.AUTO_DEFAULT.value))
            ),
        )


def _row_to_dict(result) -> dict[str, Any] | None:
    row = result.fetchone()
    if not row:
        return None
    return dict(zip(result.keys(), row))


class CfgSequenceStore:
    @staticmethod
    def _scope_columns(scope_key: ScopeKey) -> dict[str, UUID | None]:
        if scope_key.scope_type == ScopeType.TENANT:
            return {"empresa_id": None, "almacen_id": None, "punto_venta_id": None}
        if scope_key.scope_type == ScopeType.EMPRESA:
            return {
                "empresa_id": scope_key.empresa_id,
                "almacen_id": None,
                "punto_venta_id": None,
            }
        if scope_key.scope_type == ScopeType.ALMACEN:
            return {
                "empresa_id": scope_key.empresa_id,
                "almacen_id": scope_key.almacen_id,
                "punto_venta_id": None,
            }
        if scope_key.scope_type == ScopeType.PUNTO_VENTA:
            return {
                "empresa_id": scope_key.empresa_id,
                "almacen_id": None,
                "punto_venta_id": scope_key.punto_venta_id,
            }
        raise ValueError("SERIE_FISCAL no usa cfg store")

    @classmethod
    async def get_by_scope(
        cls,
        session: AsyncSession,
        scope_key: ScopeKey,
    ) -> CfgSequenceRow | None:
        fingerprint = scope_key.fingerprint
        stmt = select(CfgCodigoSecuenciaTable).where(
            and_(
                CfgCodigoSecuenciaTable.c.cliente_id == scope_key.client_id,
                CfgCodigoSecuenciaTable.c.sequence_key == scope_key.sequence_key,
                CfgCodigoSecuenciaTable.c.scope_fingerprint == fingerprint,
            )
        )
        result = await session.execute(stmt)
        row = _row_to_dict(result)
        return CfgSequenceRow.from_dict(row) if row else None

    @classmethod
    async def ensure_row(
        cls,
        session: AsyncSession,
        scope_key: ScopeKey,
        defn: SequenceDefinition,
    ) -> CfgSequenceRow:
        existing = await cls.get_by_scope(session, scope_key)
        if existing:
            if not existing.es_activo:
                raise ConflictError(
                    detail="La secuencia está inactiva.",
                    internal_code="SEQUENCE_INACTIVE",
                )
            return existing

        dims = cls._scope_columns(scope_key)
        values = {
            "secuencia_id": uuid4(),
            "cliente_id": scope_key.client_id,
            "sequence_key": defn.sequence_key,
            "scope_type": scope_key.scope_type.value,
            "scope_fingerprint": scope_key.fingerprint,
            "empresa_id": dims["empresa_id"],
            "almacen_id": dims["almacen_id"],
            "punto_venta_id": dims["punto_venta_id"],
            "prefijo": defn.default_prefix,
            "separador": defn.default_separator,
            "longitud_numero": defn.default_padding,
            "ultimo_numero": 0,
            "numero_inicial": defn.numero_inicial,
            "es_activo": True,
            "generation_policy": platform_initial_generation_policy().value,
        }
        if defn.default_prefix == "":
            values["prefijo"] = "0"
        await session.execute(insert(CfgCodigoSecuenciaTable).values(**values))
        created = await cls.get_by_scope(session, scope_key)
        if not created:
            raise NotFoundError(detail="No se pudo crear la fila de secuencia.")
        return created

    @classmethod
    async def read_for_preview(
        cls,
        session: AsyncSession,
        scope_key: ScopeKey,
        defn: SequenceDefinition,
    ) -> CfgSequenceRow:
        row = await cls.get_by_scope(session, scope_key)
        if row:
            return row
        return CfgSequenceRow(
            secuencia_id=uuid4(),
            cliente_id=scope_key.client_id,
            sequence_key=defn.sequence_key,
            scope_type=scope_key.scope_type.value,
            scope_fingerprint=scope_key.fingerprint,
            empresa_id=scope_key.empresa_id,
            almacen_id=scope_key.almacen_id,
            punto_venta_id=scope_key.punto_venta_id,
            prefijo=defn.default_prefix,
            separador=defn.default_separator,
            longitud_numero=defn.default_padding,
            ultimo_numero=0,
            numero_inicial=defn.numero_inicial,
            es_activo=True,
        )

    @classmethod
    async def increment_and_get(
        cls,
        session: AsyncSession,
        scope_key: ScopeKey,
        defn: SequenceDefinition,
    ) -> tuple[CfgSequenceRow, int]:
        row = await cls.ensure_row(session, scope_key, defn)
        nuevo = max(row.ultimo_numero, row.numero_inicial - 1) + 1
        stmt = (
            update(CfgCodigoSecuenciaTable)
            .where(CfgCodigoSecuenciaTable.c.secuencia_id == row.secuencia_id)
            .values(ultimo_numero=nuevo)
        )
        await session.execute(stmt)
        updated = await cls.get_by_scope(session, scope_key)
        if not updated:
            raise NotFoundError(detail="Secuencia no encontrada tras incremento.")
        return updated, nuevo

    @classmethod
    async def align_counter(
        cls,
        session: AsyncSession,
        scope_key: ScopeKey,
        defn: SequenceDefinition,
        candidate_numeric: int,
    ) -> int:
        row = await cls.ensure_row(session, scope_key, defn)
        if candidate_numeric <= row.ultimo_numero:
            return row.ultimo_numero
        stmt = (
            update(CfgCodigoSecuenciaTable)
            .where(CfgCodigoSecuenciaTable.c.secuencia_id == row.secuencia_id)
            .values(ultimo_numero=candidate_numeric)
        )
        await session.execute(stmt)
        return candidate_numeric
