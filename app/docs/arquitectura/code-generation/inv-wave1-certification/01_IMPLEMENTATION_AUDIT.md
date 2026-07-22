# 01 — Auditoría técnica de la implementación (Categoría)

**Método:** lectura directa del estado on-disk de cada archivo, contrastado contra ORG Cargo,
Blueprint (`inv-implementation-blueprint/`) y Baseline V1. Sin ejecución de correcciones.

Archivos auditados:

- `app/modules/inv/application/services/inv_codigo_generation_service.py`
- `app/modules/inv/application/services/categoria_service.py`
- `app/infrastructure/database/queries/inv/categoria_queries.py`
- `app/infrastructure/database/queries/inv/__init__.py`
- `app/modules/inv/presentation/schemas.py` (bloque Categoría)
- `app/modules/inv/presentation/endpoints_categorias.py`
- `app/core/codigo/gateway/codigo_generacion_gateway.py`, `generation_context.py`, `sequence_catalog.py` (referencia, congelados)

---

## 1. Arquitectura general

Capas respetadas: `presentation` (endpoints) → `application/services` (`*_servicio`) →
`infrastructure/database/queries/inv`. El adapter vive en `application/services`, igual que ORG.
No hay `domain/` ni Repository pattern. `client_id` siempre desde sesión; `empresa_id` desde
`company_scope`. **Conforme.**

## 2. `InvCodigoGenerationService`

Adapter **delgado**: solo construye `GenerationContext` y delega en `CodigoGeneracionGateway.allocate`.
Sin conocimiento de entidades, sin formato, sin RBAC, sin imports desde `app.modules.org`.
`_normalize_manual_input` idéntico a ORG. Métodos `build_tenant_context` / `build_empresa_context` /
`build_context` / `resolve_codigo_for_create` con firmas idénticas a ORG. **Copia fiel.**

Evidencia (líneas clave):

```96:101:app/modules/inv/application/services/inv_codigo_generation_service.py
        result = await CodigoGeneracionGateway.allocate(
            sequence_key,
            context,
            session,
        )
        return result.code
```

## 3. Queries dual-path

`get_categoria_by_id`, `get_categoria_by_codigo` y `create_categoria` implementan la rama
`session is not None` (usa `session.execute`) y la rama legacy (`execute_query`/`execute_insert`).
`_row_to_dict` idéntico a ORG. `get_categoria_by_codigo` incluye `exclude_id` (paridad con
`get_cargo_by_codigo`, aunque en Categoría aún no se use en Update — reservado). Exportadas en
`queries/inv/__init__.py`. **Conforme.**

## 4. Unit of Work

CREATE abre **una** `get_connection_for_tenant(client_id, OPERATION_CLASS_TENANT_DATA)` y **un**
`session.begin()`; dentro: pre-check UNIQUE (si manual) → `allocate` → INSERT. El consumo del
contador y el INSERT comparten la misma UoW ⇒ rollback atómico (TX-01/TX-03 del diseño F16).
**Conforme.**

```105:137:app/modules/inv/application/services/categoria_service.py
    async with get_connection_for_tenant(
        client_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        async with session.begin():
            if manual_codigo:
                if await get_categoria_by_codigo(... session=session):
                    raise ConflictError(...)
            codigo = await InvCodigoGenerationService.resolve_codigo_for_create(
                _SEQUENCE_KEY, session=session, client_id=client_id,
                empresa_id=empresa_id, manual_code=manual_codigo,
            )
            payload = data.model_dump()
            payload["empresa_id"] = empresa_id
            payload["codigo"] = codigo
            payload = apply_create_audit(payload, usuario_id)
            row = await create_categoria(client_id=client_id, data=payload, session=session)
```

## 5. Session handling

La `session` de la UoW se propaga explícitamente a `get_categoria_by_codigo`, `resolve_codigo_for_create`
y `create_categoria`. Ninguna operación de escritura del CREATE se ejecuta fuera de la sesión
transaccional. **Conforme.**

## 6. `GenerationContext`

Construido exclusivamente dentro del adapter (`build_context`), nunca en el service. Se pasan
`client_id`, `empresa_id`, `manual_code` normalizado y `operation=CREATE`. Coincide con el
dataclass congelado (`generation_context.py`). **Conforme.**

## 7. Uso del Gateway

El único punto de contacto con el motor es `CodigoGeneracionGateway.allocate(sequence_key, context, session)`.
No se invocan coordinadores, stores ni resolvers directamente. `sequence_key = "inv_categoria_producto"`,
presente en `sequence_catalog.py:119` (AUTO_DEFAULT, EMPRESA, F1, CFG, prefijo `CAT`, pad 3, len 20).
**Conforme.**

## 8. Cumplimiento BR-IMM

- `CategoriaUpdate` **no** declara `codigo` (BR-IMM-01). Extras en body ignorados por Pydantic.
- `update_categoria_servicio` hace `model_dump(exclude_unset=True)` y **no** contiene ninguna rama
  de código, ni llamada a `get_categoria_by_codigo` ni al Motor.
- El mixin `_CategoriaWriteMixin` normaliza `codigo` con `check_fields=False`, permitiendo que
  Update herede el mixin sin declarar el campo. **Conforme.**

## 9. Schemas Create / Update / Read

| Schema | `codigo` | Estado |
|--------|----------|--------|
| `CategoriaCreate` | `Optional[str]`, `None` por defecto | ✅ optional (no required) |
| `CategoriaUpdate` | ausente | ✅ BR-IMM |
| `CategoriaRead` | `str` requerido | ✅ intacto |

Coincide exactamente con el contrato del Blueprint (`02_ADAPTER_AND_FLOWS.md §4.1`). **Conforme.**

## 10. OpenAPI vivo esperado

El OpenAPI en runtime reflejará: `CategoriaCreate.codigo` opcional, `CategoriaUpdate` sin `codigo`,
`CategoriaRead.codigo` requerido. `app/docs/openapi_snapshot.json` **no** fue regenerado — correcto
según la instrucción de la fase. **Divergencia esperada** snapshot↔runtime hasta la tarea dedicada
de regeneración. **Conforme con lo instruido.**

## 11. Manejo de excepciones

- **POST** captura `(AuthorizationError, CustomException)` y remapea a `HTTPException(status_code, detail)`
  — idéntico a ORG cargo; cubre `ConflictError` (409), `NotFoundError` (404, cfg missing),
  `ValidationError` (422, manual no permitido). **Conforme.**
- **PUT / DELETE / reactivar / detalle** capturan solo `NotFoundError`. ORG cargo captura
  `(NotFoundError, CustomException)`. ⚠ **Desviación menor D-3** (ver 02): el UPDATE de Categoría
  no genera hoy `ConflictError`/`ValidationError` de dominio, por lo que no hay fuga funcional,
  pero rompe simetría defensiva con ORG. Recomendado alinear (no bloqueante).

## 12. Dedicated DB compatibility

`get_connection_for_tenant` enruta a la conexión dedicada cuando corresponde; el dual-path
`session=` garantiza que INSERT + allocate ocurran en la misma sesión dedicada. **Compatible.**

## 13. Shared DB compatibility

En Shared/Single-DB, `get_connection_for_tenant` provee la sesión con `client_id`; las ramas
legacy (`execute_query`) siguen disponibles para lecturas fuera de UoW (list/get). **Compatible.**

## 14. Compatibilidad con Baseline V1

- Adapter delgado propio por módulo (no reutiliza ORG). ✅
- Queries tocadas **solo** para dual-path y `get_by_codigo` (sin cambiar SQL de negocio). ✅
- Motor/Gateway/Catalog intactos. ✅
- CREATE UoW + BR-IMM Update. ✅
**Conforme.**

## 15–17. Comparaciones

Ver `02_PATTERN_COMPARISON.md` (ORG Cargo, Blueprint, Plan Técnico). Resultado: fiel; 3 desviaciones
(2 justificadas por estándar INV, 1 menor recomendada).

## 18. Calidad de pruebas

Ver `03_TEST_AUDIT.md`. 24 pruebas nuevas verdes; **2 preexistentes rojas** (C-01/C-02) por mocks
sin UoW. Gap de cobertura menor (endpoints, dual-path directo de query).

## 19. Riesgos arquitectónicos

| ID | Riesgo | Sev. | Estado |
|----|--------|------|--------|
| R-1 | Suite de entidad no 100% verde (C-01/C-02) | Alta | Abierto (gate) |
| R-2 | PUT no captura `CustomException` (D-3) | Baja | Abierto |
| R-3 | CREATE sin post-`assert_row_empresa` (D-2) | Baja | Aceptable |
| R-4 | Snapshot OpenAPI desalineado vs runtime | Baja | Esperado (diferido) |
| R-5 | Entorno local sin columna `generation_policy` en `cfg_codigo_secuencia` | Media | Entorno, no código |

## 20. Deuda técnica remanente

- Falta de logging/observabilidad equivalente a `log_org_company_scope` (ORG). Menor.
- `exclude_id` en `get_categoria_by_codigo` sin consumidor actual (reservado). Inocuo.
- Mocks de auditoría (A10/A17) desalineados con el nuevo flujo.

## 21. Oportunidades de simplificación

- Unificar el mapeo de excepciones de todos los endpoints a `(NotFoundError, CustomException)`
  para simetría total con ORG y evitar remapeos por-endpoint.
- Considerar un helper compartido INV para `_normalize_manual_codigo` (hoy duplicado en service y
  adapter `_normalize_manual_input`), como ya ocurre en ORG — mantener por paridad, no urgente.

## 22. Desviaciones respecto a ORG

Ver `02_PATTERN_COMPARISON.md §3`. Resumen: D-1 (audit `usuario_id`, **justificada** por estándar
INV-P0-004), D-2 (sin post-assert en CREATE, **menor/aceptable**), D-3 (PUT sin `CustomException`,
**menor recomendada**).

## 23. Verificación de congelados

- `git diff --name-only -- app/core/codigo/` ⇒ **vacío** (sin cambios rastreados).
- `sequence_catalog.py:119` ya contenía `inv_categoria_producto` **antes** de Fase A — no se editó.
- Ningún archivo bajo `app/modules/org/` fue escrito en Fase A (los diffs ORG en working tree son
  de la Ola 1 ORG previa, no de esta fase).
- Gateway (`codigo_generacion_gateway.py`) sin modificaciones.
**Verificado.**
