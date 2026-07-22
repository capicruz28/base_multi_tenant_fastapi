"""
SSOT seed cfg_codigo_secuencia en onboarding (Bootstrap V2 — Fase 4).

Único bucle de inserción para scope TENANT y EMPRESA resolubles en onboarding.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codigo.enums import ScopeType
from app.core.codigo.onboarding_seed import ONBOARDING_SEQUENCE_SEEDS
from app.infrastructure.database.repositories.cfg_codigo_secuencia_repository import (
    CfgCodigoSecuenciaRepository,
)


async def _seed_cfg_rows(
    session: AsyncSession,
    cliente_id: UUID,
    empresa_id: UUID,
    *,
    scopes: frozenset[ScopeType],
) -> None:
    repo = CfgCodigoSecuenciaRepository()
    for seed in ONBOARDING_SEQUENCE_SEEDS:
        if seed.scope_type not in scopes:
            continue
        eff_empresa = (
            None if seed.scope_type == ScopeType.TENANT else empresa_id
        )
        await repo.insert_secuencia(
            cliente_id=cliente_id,
            sequence_key=seed.sequence_key,
            scope_type=seed.scope_type,
            prefijo=seed.prefijo,
            longitud_numero=seed.longitud_numero,
            separador=seed.separador,
            empresa_id=eff_empresa,
            session=session,
            ultimo_numero=seed.ultimo_numero,
            numero_inicial=seed.numero_inicial,
            generation_policy=seed.generation_policy,
        )


async def seed_cfg_tenant(session: AsyncSession, cliente_id: UUID) -> None:
    await _seed_cfg_rows(
        session,
        cliente_id,
        empresa_id=cliente_id,
        scopes=frozenset({ScopeType.TENANT}),
    )


async def seed_cfg_empresa(
    session: AsyncSession, cliente_id: UUID, empresa_id: UUID
) -> None:
    await _seed_cfg_rows(
        session,
        cliente_id,
        empresa_id,
        scopes=frozenset({ScopeType.EMPRESA}),
    )
