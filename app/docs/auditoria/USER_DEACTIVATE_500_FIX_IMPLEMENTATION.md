# Implementación — Fix 500 `DELETE /api/v1/usuarios/{usuario_id}/`

**Fecha:** 2026-06-01  
**Referencias:** [USER_DEACTIVATE_500_RUNTIME_ROOT_CAUSE.md](./USER_DEACTIVATE_500_RUNTIME_ROOT_CAUSE.md)  
**Evidencia JSON:** [USER_DEACTIVATE_500_FIX_VALIDATION.json](../../bootstrap_v2/00_manifest/evidence/USER_DEACTIVATE_500_FIX_VALIDATION.json)

---

## 1. Cambio aplicado

| Archivo | Línea | Cambio |
|---------|-------|--------|
| `app/modules/users/application/services/user_service.py` | **1021** | `result = execute_update(...)` → `result = await execute_update(...)` |

```python
result = await execute_update(update_query, (cliente_id, usuario_id))
```

**Alcance:** una línea en `eliminar_usuario`; sin cambios en presentation, schemas, SQL, frontend ni RBAC.

---

## 2. Causa raíz (confirmada)

| Antes | Después |
|-------|---------|
| `TypeError: 'coroutine' object is not subscriptable` en L1053 | `execute_update` devuelve `dict` con `OUTPUT` SQL |
| `RuntimeWarning: coroutine 'execute_update' was never awaited` | Sin warning en logs post-fix |
| HTTP **500** — UPDATE `usuario` no ejecutado; `usuario_rol` sí desactivado | HTTP **200** — soft-delete y roles en orden correcto |

---

## 3. Pruebas ejecutadas

### 3.1 Unit test (regresión await)

| Test | Resultado |
|------|-----------|
| `tests/unit/test_user_deactivate_execute_update_await.py` | **PASS** (1/1) |

Verifica que `eliminar_usuario` hace `await` en `execute_update` del soft-delete y construye la respuesta con `result['usuario_id']` / `result['es_eliminado']`.

```bash
python -m pytest tests/unit/test_user_deactivate_execute_update_await.py -q
```

### 3.2 QA HTTP runtime (tenant `t3usr971acefb`)

**Entorno:** Docker `fastapi_backend` — `http://localhost:8000`  
**Timestamp evidencia:** `2026-06-01T07:09:54Z`  
**Script:** `scripts/_run_user_deactivate_fix_qa.py`

| # | Caso | Método / ruta | Resultado |
|---|------|---------------|-----------|
| 1 | Login admin | `POST /api/v1/auth/login/` | **200** |
| 2 | Crear usuario QA | `POST /api/v1/usuarios/` | **201** (`c0afe5fc-…`) |
| 3 | Asignar rol Usuario | `POST /api/v1/usuarios/{id}/roles/{rol_id}/` | **201** |
| 4 | **DELETE desactivar** | `DELETE /api/v1/usuarios/{id}/` | **200** |
| 5 | Soft-delete en respuesta | body `es_eliminado: true` | **OK** |
| 6 | Roles desactivados | `GET …/roles/` → `activos: 0` | **OK** |

**Verdict global QA:** `PASS`

---

## 4. Evidencia en logs post-fix

Tras el fix, el contenedor registra el flujo completo (sin `ERROR` ni `RuntimeWarning`):

```text
2026-06-01 07:07:59,252 - user_service - INFO - Intentando eliminar usuario ID: 3776279d-fa47-4a5c-b518-f2cb688a6051 ...
2026-06-01 07:07:59,280 - user_service - INFO - Roles desactivados para usuario eliminado ID 3776279d-...
2026-06-01 07:07:59,281 - user_service - INFO - Usuario ID 3776279d-... eliminado lógicamente exitosamente ...
2026-06-01 07:07:59,281 - endpoints - INFO - Usuario ID 3776279d-... eliminado lógicamente exitosamente ...
2026-06-01 07:07:59,281 - app.main - INFO - [SYSTEM] ... DELETE /api/v1/usuarios/3776279d-.../ 200 91.1ms
```

**Ausente** (comparado con pre-fix en auditoría):

```text
TypeError: 'coroutine' object is not subscriptable
RuntimeWarning: coroutine 'execute_update' was never awaited
```

**Búsqueda en log actual (`terminals/1.txt`):** `coroutine` / `RuntimeWarning` → **0 coincidencias** tras el despliegue del fix.

---

## 5. Validación de estado (BD / API)

| Verificación | Mecanismo | Resultado |
|--------------|-----------|-----------|
| Soft-delete `usuario` | Respuesta `DELETE` → `es_eliminado: true` | **OK** |
| `usuario.es_activo` | Implícito en UPDATE (`es_activo = 0`) + respuesta exitosa | **OK** |
| `usuario_rol.es_activo` | Log “Roles desactivados…” + `GET …/roles/` → `activos: 0` | **OK** |

**Nota QA:** `GET /api/v1/usuarios/{id}/` sobre usuario ya eliminado devolvió **500** en el script de evidencia (fuera del alcance de este fix; no bloquea DELETE). La validación principal usa la respuesta **200** del DELETE y el listado de roles.

---

## 6. Búsqueda preventiva — `await` faltantes en `user_service.py`

Patrón: `(?<!await )= execute_(update|insert|query)\(` sobre el archivo completo.

| Función async | Asignaciones sin `await` |
|---------------|--------------------------|
| `execute_update` | **0** |
| `execute_insert` | **0** |
| `execute_query` | **0** |

Todas las demás llamadas en el servicio ya usaban `await` (incl. L1038 `deactivate_roles_query`).

---

## 7. Respuesta HTTP QA (DELETE)

```http
DELETE /api/v1/usuarios/c0afe5fc-2dbf-43eb-8c4e-3c3a00546468/
Authorization: Bearer <admin tenant>
Origin: http://t3usr971acefb.app.local:5173
```

**Response (200):**

```json
{
  "message": "Usuario eliminado lógicamente exitosamente",
  "usuario_id": "C0AFE5FC-2DBF-43EB-8C4E-3C3A00546468",
  "es_eliminado": true
}
```

---

## 8. Regresiones descartadas

| Área | Estado |
|------|--------|
| Frontend / payload DELETE | Sin cambios |
| RBAC `admin.usuario.eliminar` | Autorizado (200) |
| Tenant / multiempresa | Sin impacto |
| SQL Server / driver | Sin cambios |
| Presentation `eliminar_usuario(cliente_id, usuario_id)` | Ya correcto |

---

## 9. Archivos tocados

| Archivo | Tipo |
|---------|------|
| `app/modules/users/application/services/user_service.py` | Fix producción |
| `tests/unit/test_user_deactivate_execute_update_await.py` | Regresión unitaria |
| `scripts/_run_user_deactivate_fix_qa.py` | QA runtime (evidencia) |
| `app/bootstrap_v2/00_manifest/evidence/USER_DEACTIVATE_500_FIX_VALIDATION.json` | Evidencia JSON |
| `app/docs/auditoria/USER_DEACTIVATE_500_FIX_IMPLEMENTATION.md` | Este documento |

**Sin commit** (solicitud explícita).
