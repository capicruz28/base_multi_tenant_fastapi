"""CodigoGeneracionGateway — punto de entrada único del motor (F16 `12`)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codigo.coordinator.allocation_coordinator import AllocationCoordinator
from app.core.codigo.enums import CodePolicy, PolicyMode, ScopeType, StoreType
from app.core.codigo.generation_context import GenerationContext
from app.core.codigo.generation_result import AllocationResult, PreviewResult
from app.core.codigo.resolvers.policy_resolver import PolicyResolver
from app.core.codigo.resolvers.scope_resolver import ScopeResolver
from app.core.codigo.scope_key import ScopeKey
from app.core.codigo.sequence_catalog import SequenceCatalog
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.codigo.services.counter_alignment_service import CounterAlignmentService
from app.core.codigo.services.preview_reader import PreviewReader
from app.core.codigo.stores.cfg_sequence_store import CfgSequenceStore
from app.core.codigo.validator.code_validator import CodeValidator
from app.core.exceptions import ConflictError, NotFoundError, ValidationError


class CodigoGeneracionGateway:
    """Orquestador fino del motor de generación de códigos."""

    @classmethod
    def _get_definition(cls, sequence_key: str) -> SequenceDefinition:
        if not SequenceCatalog.contains(sequence_key):
            raise ValidationError(
                detail=f"sequence_key desconocido: {sequence_key}",
                internal_code="SEQUENCE_KEY_UNKNOWN",
            )
        return SequenceCatalog.get(sequence_key)

    @classmethod
    async def _resolve_generation_policy(
        cls,
        session: AsyncSession,
        defn: SequenceDefinition,
        scope_key: ScopeKey,
    ) -> CodePolicy:
        if defn.store_type == StoreType.FISCAL:
            return defn.policy

        if scope_key.scope_type in (ScopeType.ALMACEN, ScopeType.PUNTO_VENTA):
            row = await CfgSequenceStore.ensure_row(session, scope_key, defn)
            return row.generation_policy

        row = await CfgSequenceStore.get_by_scope(session, scope_key)
        if row is None:
            raise NotFoundError(
                detail="Configuración de secuencia no encontrada para este scope.",
                internal_code="CFG_SEQUENCE_NOT_FOUND",
            )
        if not row.es_activo:
            raise ConflictError(
                detail="La secuencia está inactiva.",
                internal_code="SEQUENCE_INACTIVE",
            )
        return row.generation_policy

    @classmethod
    async def allocate(
        cls,
        sequence_key: str,
        context: GenerationContext,
        session: AsyncSession,
    ) -> AllocationResult:
        defn = cls._get_definition(sequence_key)
        scope_key = ScopeResolver.resolve(defn, context)
        generation_policy = await cls._resolve_generation_policy(session, defn, scope_key)
        mode = PolicyResolver.resolve(generation_policy, context)

        if mode == PolicyMode.REJECT_MANUAL:
            raise ValidationError(
                detail="No se permite código manual para esta entidad.",
                internal_code="MANUAL_NOT_ALLOWED",
            )

        if mode == PolicyMode.AUTO_GENERATE:
            return await AllocationCoordinator.allocate_next(session, defn, scope_key)

        manual = (context.manual_code or "").strip()
        CodeValidator.validate(defn, manual)
        result = AllocationCoordinator.accept_manual(defn, manual)
        if mode in (PolicyMode.ACCEPT_MANUAL, PolicyMode.IMPORT_HISTORICAL):
            row = await CounterAlignmentService.maybe_align(
                session,
                defn,
                scope_key,
                manual,
            )
            if row is not None and defn.align_on_manual:
                pass
        return result

    @classmethod
    async def preview(
        cls,
        sequence_key: str,
        context: GenerationContext,
        session: AsyncSession,
    ) -> PreviewResult:
        defn = cls._get_definition(sequence_key)
        scope_key = ScopeResolver.resolve(defn, context)
        return await PreviewReader.preview(session, defn, scope_key)

    @classmethod
    def _policy_context_for_validate_manual(
        cls,
        context: GenerationContext,
        manual_code: str,
    ) -> GenerationContext:
        """validate_manual recibe el código en argumento explícito, no solo en context."""
        return GenerationContext(
            client_id=context.client_id,
            operation=context.operation,
            empresa_id=context.empresa_id,
            almacen_id=context.almacen_id,
            punto_venta_id=context.punto_venta_id,
            serie_id=context.serie_id,
            manual_code=manual_code,
            idempotency_key=context.idempotency_key,
        )

    @classmethod
    async def validate_manual(
        cls,
        sequence_key: str,
        manual_code: str,
        context: GenerationContext,
        session: AsyncSession,
    ) -> None:
        defn = cls._get_definition(sequence_key)
        scope_key = ScopeResolver.resolve(defn, context)
        generation_policy = await cls._resolve_generation_policy(session, defn, scope_key)
        policy_context = cls._policy_context_for_validate_manual(context, manual_code)
        mode = PolicyResolver.resolve(generation_policy, policy_context)
        if mode == PolicyMode.REJECT_MANUAL:
            raise ValidationError(
                detail="No se permite código manual para esta entidad.",
                internal_code="MANUAL_NOT_ALLOWED",
            )
        CodeValidator.validate(defn, manual_code)

    @classmethod
    async def align_counter(
        cls,
        sequence_key: str,
        context: GenerationContext,
        session: AsyncSession,
        candidate_code: str,
    ) -> int:
        defn = cls._get_definition(sequence_key)
        scope_key = ScopeResolver.resolve(defn, context)
        aligned = await CounterAlignmentService.maybe_align(
            session,
            defn,
            scope_key,
            candidate_code,
        )
        if aligned is None:
            row = await CfgSequenceStore.get_by_scope(session, scope_key)
            return row.ultimo_numero if row else 0
        return aligned
