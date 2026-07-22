# 01 — Análisis de causa raíz (C-01 / C-02)

**Tests:**
- **C-01** `test_a10_create_categoria_servicio_persiste_usuario_creacion_id`
- **C-02** `test_a17_create_categoria_servicio_sin_usuario_id_deja_usuario_creacion_none`

**Archivo:** `tests/unit/test_inv_audit_usuario.py`
**Referencia productiva:** `create_categoria_servicio` en `categoria_service.py`
**Evidencia de certificación:** `inv-wave1-certification/03_TEST_AUDIT.md`

---

## 1. Qué asumían originalmente estos tests

Propósito INV-P0-004 (Etapa 5): verificar que el CREATE de categoría **inyecta
`usuario_creacion_id` desde sesión**, no desde el body.

### 1.1 Modelo mental AS-IS (pre-Motor)

```text
create_categoria_servicio(client_id, data, usuario_id?)
  → enforce_body_empresa_matches_session(data.empresa_id)   # usa ContextVar
  → ensure_empresa_in_tenant(...)
  → payload = data.model_dump()
  → payload = apply_create_audit(payload, usuario_id)
  → create_categoria(client_id, data=payload)               # sin session=
```

### 1.2 Mocks originales (HEAD commit `ecb640d`)

| Mock | Motivo |
|------|--------|
| `ensure_empresa_in_tenant` | Evitar I/O de validación de empresa |
| `create_categoria` | Capturar el `data=` del INSERT sin BD |

**No mockeaban:** `get_connection_for_tenant`, `session.begin`, adapter/Gateway,
`get_categoria_by_codigo`. Tampoco necesitaban hacerlo: esas llamadas **no existían**.

### 1.3 Asserts originales (contrato de auditoría)

| Test | Assert invariante |
|------|-------------------|
| A10 | `payload["usuario_creacion_id"] == USUARIO_ID` |
| A17 | `payload["usuario_creacion_id"] is None` (llamada sin `usuario_id`) |

Estos asserts son el **núcleo funcional** del test y deben permanecer.

---

## 2. Qué cambió en el flujo CREATE (Fase A)

```text
create_categoria_servicio(client_id, data, usuario_id?)
  → enforce_body_empresa_matches_session
  → ensure_empresa_in_tenant
  → manual_codigo = normalize(data.codigo)
  → async with get_connection_for_tenant(client_id, TENANT_DATA) as session:
       async with session.begin():
         → [si manual] get_categoria_by_codigo(..., session=session)
              → ConflictError si existe
         → codigo = InvCodigoGenerationService.resolve_codigo_for_create(
                "inv_categoria_producto", session=session, ...)
         → payload = model_dump(); payload["codigo"] = codigo
         → payload = apply_create_audit(payload, usuario_id)   # INTACTO
         → create_categoria(..., session=session)
```

Puntos críticos respecto a los tests:

1. **UoW obligatorio** antes del INSERT → sin mock de `get_connection_for_tenant`, se abre
   sesión **real** (Dedicated/Shared routing).
2. **Gateway vía adapter** antes del INSERT → sin mock de `resolve_codigo_for_create`, se
   ejecuta `CodigoGeneracionGateway.allocate` real contra `cfg_codigo_secuencia`.
3. Con código manual (`CAT-AUD` / `CAT-NULL`) hay **pre-check** `get_categoria_by_codigo`
   dentro de la misma sesión.
4. `apply_create_audit` **no cambió** — la responsabilidad de auditoría es la misma.

---

## 3. Por qué dejaron de ser válidos

| Paso del test | Pre-Motor | Post-Motor (sin alinear mocks) |
|---------------|-----------|--------------------------------|
| Llega a `apply_create_audit` | Sí | Nunca: falla antes en allocate/BD |
| Mock de `create_categoria` se invoca | Sí | No (excepción previa) |
| Assert `usuario_creacion_id` | Evalúa payload | No se alcanza |

El fallo observado en certificación:

```text
ProgrammingError: Invalid column name 'generation_policy'
  ← CfgSequenceStore.get_by_scope
  ← CodigoGeneracionGateway.allocate
  ← InvCodigoGenerationService.resolve_codigo_for_create
  ← create_categoria_servicio
```

Eso **no** indica un bug de auditoría ni de Categoría: indica que el test **escapó del
aislamiento unitario** y golpeó el Motor real / esquema local incompleto.

---

## 4. Qué mocks faltan actualmente (estado HEAD / pre-alineación)

Respecto al HEAD versionado (antes del diff local):

| Mock faltante | Efecto si falta |
|---------------|-----------------|
| `get_connection_for_tenant` | Abre conexión real |
| Sesión fake con `begin()` | No hay UoW controlada |
| `InvCodigoGenerationService.resolve_codigo_for_create` | Ejecuta Gateway real |
| `get_categoria_by_codigo` (A10/A17 usan código manual) | Puede golpear BD en pre-check |
| `enforce_body_empresa_matches_session` (recomendado) | Depende de ContextVar; frágil si el contexto falla |

---

## 5. Diagnóstico definitivo

| Hipótesis | ¿Sostenible? |
|-----------|--------------|
| `apply_create_audit` dejó de asignar `usuario_creacion_id` | **No** — el código productivo aún lo llama con el mismo contrato |
| Gateway exige cambios en el test de auditoría | **No** — el Gateway no es el SUT de A10/A17 |
| Los mocks quedaron obsoletos frente al nuevo CREATE | **Sí** — causa raíz única |
| Hay que tocar código productivo para pasar A10/A17 | **No** |

**Conclusión:** C-01/C-02 son **falsos negativos de fixture**, no defectos de producto.
