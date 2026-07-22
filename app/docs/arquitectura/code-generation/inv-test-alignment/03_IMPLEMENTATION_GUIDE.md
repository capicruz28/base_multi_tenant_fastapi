# 03 — Guía de implementación (post-aprobación)

**Condición:** este documento se ejecuta **solo** tras aprobación explícita del plan.
**Alcance de archivos:** únicamente `tests/unit/test_inv_audit_usuario.py` (helpers + A10 + A17).
**Prohibido:** código productivo, Motor, Gateway, SequenceCatalog, ORG, otros tests del archivo
salvo que se apruebe un alcance ampliado.

---

## 0. Conclusión previa a la implementación

| Pregunta | Respuesta |
|----------|-----------|
| ¿Adaptar mocks existentes? | **Sí — única corrección necesaria** |
| ¿Hay problema real en código productivo? | **No** |

---

## 1. Plan exacto de implementación (pasos)

### Paso 1 — Helpers compartidos (mismo archivo)

Añadir (si no existen) al inicio del módulo de test, junto a imports:

```python
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
```

```python
def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session
    return _cm()


def _make_uow_session():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    return session
```

**Nota:** idénticos al patrón de `test_inv_categoria_motor_integration.py`.

### Paso 2 — Alinear `test_a10` (C-01)

1. Crear `session = _make_uow_session()` antes del `with patch(...)`.
2. Cadena de patches (orden sugerido):

| # | Target | Config |
|---|--------|--------|
| 1 | `...categoria_service.enforce_body_empresa_matches_session` | `return_value=EMPRESA_ID` |
| 2 | `...categoria_service.ensure_empresa_in_tenant` | `AsyncMock()` |
| 3 | `...categoria_service.get_connection_for_tenant` | `return_value=_session_context_manager(session)` → `mock_get_conn` |
| 4 | `...categoria_service.get_categoria_by_codigo` | `AsyncMock(return_value=None)` |
| 5 | `...categoria_service.InvCodigoGenerationService.resolve_codigo_for_create` | `AsyncMock(return_value="CAT-AUD")` → `mock_resolve` |
| 6 | `...categoria_service.create_categoria` | `AsyncMock(return_value=row)` → `mock_create` |

3. Invocación (sin cambio de contrato):

```python
await categoria_service.create_categoria_servicio(
    client_id=CLIENT_ID,
    data=data,
    usuario_id=USUARIO_ID,
)
```

4. Asserts **obligatorios**:

```python
payload = mock_create.await_args.kwargs["data"]
assert payload["usuario_creacion_id"] == USUARIO_ID          # INVARIANTE
mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)
session.begin.assert_called_once()
mock_resolve.assert_awaited_once_with(
    "inv_categoria_producto",
    session=session,
    client_id=CLIENT_ID,
    empresa_id=EMPRESA_ID,
    manual_code="CAT-AUD",
)
assert mock_create.await_args.kwargs["session"] is session
assert payload["codigo"] == "CAT-AUD"
```

5. Conservar `try/finally` con `_set_empresa_ctx` / `reset_current_empresa_id`.

### Paso 3 — Alinear `test_a17` (C-02)

Igual que A10, con estas diferencias:

| Elemento | Valor |
|----------|-------|
| `codigo` / return del resolve | `"CAT-NULL"` |
| `row["usuario_creacion_id"]` | `None` |
| Llamada al service | **sin** `usuario_id=` |
| Assert auditoría | `assert payload["usuario_creacion_id"] is None` |
| `manual_code` en resolve | `"CAT-NULL"` |

### Paso 4 — Verificación

```bash
python -m pytest \
  tests/unit/test_inv_audit_usuario.py::test_a10_create_categoria_servicio_persiste_usuario_creacion_id \
  tests/unit/test_inv_audit_usuario.py::test_a17_create_categoria_servicio_sin_usuario_id_deja_usuario_creacion_none \
  -q --tb=short

python -m pytest \
  tests/unit/test_inv_codigo_generation_service.py \
  tests/unit/test_inv_categoria_motor_integration.py \
  tests/unit/test_inv_categoria_br_imm_update.py \
  -q --tb=short
```

Gate verde:

- A10 + A17 → 2 passed
- Suite Fase A Categoría → 24 passed

### Paso 5 — Checklist anti-regresión

- [ ] No se mockeó `apply_create_audit`
- [ ] Assert de `usuario_creacion_id` intacto en ambos tests
- [ ] Adapter mockeado (no Gateway directo)
- [ ] `session` propagada a resolve + create
- [ ] No se modificó `categoria_service.py` ni Motor/ORG
- [ ] Alcance de diff limitado a A10/A17 + helpers (no otras entidades del archivo)

### Paso 6 — Re-certificación

Tras verde, solicitar actualización del dictamen en
`inv-wave1-certification/` (gate de suite) → **A) Golden Reference INV**.

---

## 2. Pseudocódigo de A10 (referencia)

```python
async def test_a10_...():
    token = _set_empresa_ctx(EMPRESA_ID)
    data = CategoriaCreate(empresa_id=EMPRESA_ID, codigo="CAT-AUD", nombre="...")
    row = {..., "usuario_creacion_id": USUARIO_ID}
    session = _make_uow_session()
    try:
        with patches(...UoW + resolve + create...):
            await create_categoria_servicio(..., usuario_id=USUARIO_ID)
            payload = mock_create.await_args.kwargs["data"]
            assert payload["usuario_creacion_id"] == USUARIO_ID
            # + asserts UoW / resolve / session
    finally:
        reset_current_empresa_id(token)
```

---

## 3. Nota sobre el working tree actual

Al redactar este plan, el archivo en disco ya contiene una alineación **no commitada** de
A10/A17 (y posiblemente otros tests del mismo archivo fuera de alcance). Tras aprobar el plan:

1. Revisar el diff vs HEAD.
2. **Conservar solo** helpers + cambios de A10/A17 si se desea un PR quirúrgico.
3. Revertir o diferir cambios de producto/movimiento/IF hasta su propia ola.
4. Ejecutar el Paso 4 de verificación.

Si el diff de A10/A17 ya coincide literalmente con este guía, la “implementación” se reduce a
**validar + acotar el diff + re-certificar**, sin reescribir de cero.

---

## 4. Criterio de aceptación

| Criterio | OK |
|----------|----|
| Causa raíz = mocks obsoletos, no bug productivo | ✅ |
| Solo `test_inv_audit_usuario.py` (A10/A17 + helpers) | ✅ |
| Asserts INV-P0-004 preservados | ✅ |
| Asserts UoW mínimos presentes | ✅ |
| Gateway no ejecutado en A10/A17 | ✅ |
| Suite Categoría Fase A verde | ✅ |
| Dictamen A desbloqueado | Tras re-auditoría |
