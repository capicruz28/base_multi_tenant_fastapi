# 02 — Plan de alineación de tests (C-01 / C-02)

Responde las preguntas 4–14 del encargo. Guía de pasos: `03_IMPLEMENTATION_GUIDE.md`.

---

## 4. Qué objetos deben mockearse

Mockear **en el namespace del service** (`categoria_service.*`), nunca el módulo real del Motor.

| Objeto | Tipo de mock | Valor / comportamiento |
|--------|--------------|------------------------|
| `enforce_body_empresa_matches_session` | sync `return_value=EMPRESA_ID` | Evita dependencia frágil de ContextVar |
| `ensure_empresa_in_tenant` | `AsyncMock()` | Sin I/O |
| `get_connection_for_tenant` | retorna async CM que yield `session` | UoW aislada |
| `session` (`_make_uow_session`) | `AsyncMock` + `begin()` CM no-op | Observar un solo `begin()` |
| `get_categoria_by_codigo` | `AsyncMock(return_value=None)` | Camino feliz (no 409); A10/A17 usan código manual |
| `InvCodigoGenerationService.resolve_codigo_for_create` | `AsyncMock(return_value=<codigo>)` | Sustituye Gateway sin ejecutarlo |
| `create_categoria` | `AsyncMock(return_value=row)` | Captura payload de auditoría |

Patrón de referencia: `tests/unit/test_inv_categoria_motor_integration.py` (Golden de mocks UoW).

---

## 5. Qué objetos NO deben mockearse

| Objeto | Motivo |
|--------|--------|
| `apply_create_audit` | **Es parte del SUT** de auditoría; mockearlo vaciaría el test |
| `create_categoria_servicio` | Es la función bajo prueba |
| `CodigoGeneracionGateway` / stores / catalog | Fuera de alcance; se aíslan mockeando el **adapter** |
| `CategoriaCreate` / Pydantic | Comportamiento real del contrato |
| SQLAlchemy / `execute_query` | No se alcanzan si los mocks UoW están bien |

**Regla:** mockear el **borde** (conexión, adapter, query de dup, INSERT), no el **núcleo**
(`apply_create_audit`).

---

## 6. Qué asserts deben permanecer exactamente iguales

| Test | Assert (inmutable) |
|------|--------------------|
| A10 | `payload = mock_create.await_args.kwargs["data"]` |
| A10 | `assert payload["usuario_creacion_id"] == USUARIO_ID` |
| A17 | llamada **sin** `usuario_id=` |
| A17 | `assert payload["usuario_creacion_id"] is None` |

Sin estos asserts, el test deja de validar INV-P0-004.

---

## 7. Qué asserts deben adaptarse / añadirse

| Assert nuevo | Propósito | Evita |
|--------------|-----------|-------|
| `mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)` | UoW con routing correcto | Omitir UoW y “pasar” por accidente |
| `session.begin.assert_called_once()` | Una sola transacción | Doble begin / fuga |
| `mock_resolve.assert_awaited_once_with("inv_categoria_producto", session=session, client_id=..., empresa_id=..., manual_code=...)` | Adapter llamado con args correctos; Gateway **no** ejecutado | Falso positivo si se bypasea el motor |
| `mock_create.await_args.kwargs["session"] is session` | INSERT en la misma UoW | INSERT fuera de TX |
| `payload["codigo"] == <codigo resuelto>` | El código del INSERT es el del adapter | Payload con código “fantasma” distinto |

Los asserts UoW son **complementarios**, no sustituyen el assert de auditoría.

---

## 8. Cómo mantener el mismo nivel de cobertura funcional

| Dimensión INV-P0-004 | Cómo se preserva |
|----------------------|------------------|
| Asigna `usuario_creacion_id` desde `usuario_id` | Assert A10 intacto |
| Sin `usuario_id` → `None` | Assert A17 intacto |
| No lee el body para auditoría | Implícito: body no trae `usuario_creacion_id`; `apply_create_audit` real se ejecuta |

La cobertura de Motor (auto/manual/dup/cfg) **no** es responsabilidad de A10/A17; ya está en
`test_inv_categoria_motor_integration.py`. No duplicar esos escenarios aquí.

---

## 9. Cómo evitar falsos positivos

| Riesgo de falso positivo | Mitigación |
|--------------------------|------------|
| Mockear `apply_create_audit` y “hardcodear” el payload | **Prohibido** |
| Devolver `row` con `usuario_creacion_id` y assertar el row, no el payload de INSERT | Assertar **`mock_create.await_args.kwargs["data"]`**, no el return |
| No observar `resolve_codigo_for_create` | Si el service deja de llamar al adapter, el test debe fallar |
| No observar `session` en `create_categoria` | Si el INSERT sale de la UoW, el test debe fallar |
| Usar `side_effect` que rellene `usuario_creacion_id` en `create_categoria` | El mock solo retorna row; no muta payload |

---

## 10. Cómo garantizar que siguen validando `usuario_creacion_id`

1. Ejecutar `apply_create_audit` real (no mock).
2. Capturar el dict pasado a `create_categoria`.
3. Assertar el campo **antes** de cualquier transformación del mock de INSERT.
4. Mantener dos casos: con `usuario_id` y sin `usuario_id`.

---

## 11. Cómo garantizar que también validan el nuevo flujo UoW

Observar explícitamente:

- apertura de conexión (`get_connection_for_tenant`)
- un `session.begin()`
- propagación de la **misma** `session` al adapter y al INSERT

Sin estos tres, el test solo prueba auditoría en un CREATE “viejo” imaginario.

---

## 12. Cómo garantizar que no oculten errores del Gateway

| Técnica | Efecto |
|---------|--------|
| Mockear `InvCodigoGenerationService.resolve_codigo_for_create`, **no** el Gateway interno | A10/A17 no pretenden probar el Motor |
| Assert de args de `resolve_*` (sequence_key, session, manual_code) | Si alguien elimina la llamada o cambia la key, falla |
| Dejar la suite `test_inv_categoria_motor_integration.py` como dueña del Gateway | Errores reales de Gateway/cfg siguen detectándose allí |
| **No** mockear `CodigoGeneracionGateway.allocate` “por debajo” además del adapter | Evita doble capa confusa; un solo borde |

Si el adapter se rompe (firma incorrecta), A10/A17 fallan por `assert_awaited_once_with`.
Si el Gateway se rompe, fallan los tests de motor / adapter unitarios — no A10/A17.

---

## 13. Riesgos de modificar demasiado los tests

| Riesgo | Consecuencia |
|--------|--------------|
| Convertir A10/A17 en copia de la suite Motor | Pierden foco INV-P0-004; ruido |
| Añadir escenarios auto/dup/cfg aquí | Fuera de alcance; acoplamiento |
| Mockear `apply_create_audit` | Falso positivo total |
| Cambiar el assert de `usuario_creacion_id` a otro campo | Regresión silenciosa de auditoría |
| “Arreglar” también producto/movimiento/IF en el mismo PR sin aprobación | Expande alcance; mezcla gates |

---

## 14. Riesgos de modificar demasiado poco

| Riesgo | Consecuencia |
|--------|--------------|
| Solo mockear `get_connection_for_tenant` sin el adapter | Sigue llamando Gateway real → rojo o flaky |
| Solo mockear el adapter sin UoW | Puede fallar al entrar a `async with get_connection...` |
| No mockear `get_categoria_by_codigo` con código manual | Pre-check puede ir a BD |
| No añadir asserts UoW | Test verde pero ciego a regresiones del nuevo flujo |
| Dejar ContextVar sin `enforce_*` mockeado y sin `_set_empresa_ctx` | Flaky por sesión empresa |

---

## Matriz de decisión

| Opción | ¿Aceptable? |
|--------|-------------|
| Solo adaptar mocks + asserts UoW mínimos en A10/A17 | ✅ **Plan oficial** |
| Cambiar código productivo de Categoría | ❌ Innecesario |
| Cambiar Gateway / Motor | ❌ Prohibido |
| Eliminar A10/A17 | ❌ Pierde cobertura INV-P0-004 |
| Reescribir A10/A17 como tests de Motor | ❌ Fuera de propósito |
