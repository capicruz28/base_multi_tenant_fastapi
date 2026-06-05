# Implementación — Fix 500 `DELETE /api/v1/roles/{rol_id}/`

**Fecha:** 2026-06-01  
**Referencias:** [ROLE_DEACTIVATE_500_RUNTIME_ROOT_CAUSE.md](./ROLE_DEACTIVATE_500_RUNTIME_ROOT_CAUSE.md)  
**Evidencia JSON:** [ROLE_DEACTIVATE_500_FIX_VALIDATION.json](../../bootstrap_v2/00_manifest/evidence/ROLE_DEACTIVATE_500_FIX_VALIDATION.json)

---

## 1. Cambio aplicado

| Archivo | Cambio |
|---------|--------|
| `app/modules/rbac/application/services/rol_service.py` | Tras `execute_update(DEACTIVATE_ROL)`, retornar rol completo vía `obtener_rol_por_id(rol_id, incluir_inactivos=True)` en lugar de `_normalizar_rol_dict({"rows_affected": 1})` |

```python
rol_desactivado = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True)
if not rol_desactivado:
    raise ServiceError(...)
return rol_desactivado
```

**Alcance:** solo `desactivar_rol`; sin cambios en endpoint, `RolRead`, RBAC, SQL `DEACTIVATE_ROL` ni frontend.

---

## 2. Causa raíz y efecto del fix

| Antes | Después |
|-------|---------|
| Retorno `{"rows_affected": 1}` | Retorno dict con `rol_id`, `nombre`, `fecha_creacion`, `es_activo`, etc. |
| `ResponseValidationError` en serialización | `response_model=RolRead` satisfecho |
| HTTP **500** — `"Error interno al verificar el usuario"` | HTTP **200** + cuerpo `RolRead` |
| UPDATE en BD **sí** ejecutado | Igual (sin cambio de SQL) |

---

## 3. Pruebas ejecutadas

### 3.1 Unit test

| Test | Resultado |
|------|-----------|
| `tests/unit/test_rol_desactivar_returns_full_rol_read.py` | **PASS** (1/1) |

Verifica que, con `execute_update` devolviendo solo `rows_affected`, el servicio hace segunda llamada a `obtener_rol_por_id(..., incluir_inactivos=True)` y devuelve campos completos con `es_activo=False`.

```bash
python -m pytest tests/unit/test_rol_desactivar_returns_full_rol_read.py -q
```

### 3.2 QA HTTP runtime (tenant `t3usr971acefb`)

**Entorno:** Docker `fastapi_backend` — `http://localhost:8000`  
**Timestamp evidencia:** `2026-06-01T08:01:49Z`  
**Script:** `scripts/_run_role_deactivate_fix_qa.py`

| Paso | Resultado |
|------|-----------|
| `POST /api/v1/roles/` (rol QA) | **201** |
| `DELETE /api/v1/roles/{rol_id}/` | **200** |
| Cuerpo `RolRead` (`rol_id`, `nombre`, `es_activo: false`) | **OK** |
| `GET /roles/all-active/` sin el rol | **OK** |
| Sin mensaje `"Error interno al verificar el usuario"` | **OK** |

**Verdict global QA:** `PASS`

### 3.3 Respuesta HTTP ejemplo (200)

```json
{
  "cliente_id": "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8",
  "codigo_rol": null,
  "nombre": "Qa_Del_234971",
  "descripcion": "role deactivate fix QA",
  "es_activo": false,
  "rol_id": "4c7390a4-f4e9-40a6-9782-85ec30cf79d9",
  "fecha_creacion": "2026-06-01T03:01:49.400000",
  "es_eliminado": false
}
```

---

## 4. Evidencia en logs post-fix

Flujo esperado (sin `ResponseValidationError` ni error en `deps.py`):

```text
rol_service - INFO - Intentando desactivar rol ID: 4c7390a4-...
rol_service - INFO - Rol ID 4c7390a4-... desactivado exitosamente
endpoints - INFO - Rol ID 4c7390a4-... desactivado exitosamente en cliente e4c8e906-...
app.main - INFO - [SYSTEM] ... DELETE /api/v1/roles/4c7390a4-.../ 200 ...
```

**Ausente** (pre-fix):

```text
ResponseValidationError ... input: {'rows_affected': 1}
Error inesperado obteniendo usuario activo 'admin'
DELETE ... 500
```

---

## 5. Validación BD / listado

| Verificación | Resultado |
|--------------|-----------|
| `rol.es_activo` tras DELETE | **false** en respuesta 200 |
| Listado activos | Rol **no** en `GET /roles/all-active/` |
| Contrato FE | Sin cambios — mismo `RolRead` |

---

## 6. Regresiones descartadas

| Área | Estado |
|------|--------|
| Frontend | Sin cambios requeridos |
| RBAC `admin.rol.eliminar` | Autorizado (handler ejecutado) |
| Permisos / política desactivación | Sin cambios |
| Rol ya inactivo (idempotente) | Sigue retornando `rol_actual` en L808–810 |

---

## 7. Archivos tocados

| Archivo | Tipo |
|---------|------|
| `app/modules/rbac/application/services/rol_service.py` | Fix producción |
| `tests/unit/test_rol_desactivar_returns_full_rol_read.py` | Regresión unitaria |
| `scripts/_run_role_deactivate_fix_qa.py` | QA runtime |
| `app/bootstrap_v2/00_manifest/evidence/ROLE_DEACTIVATE_500_FIX_VALIDATION.json` | Evidencia JSON |
| `app/docs/auditoria/ROLE_DEACTIVATE_500_FIX_IMPLEMENTATION.md` | Este documento |

**Nota:** `reactivar_rol` conserva el patrón antiguo (`rows_affected`); no formó parte de este incidente Sprint C. Valorar alinear en tarea aparte si se reporta 500 en reactivate.

**Sin commit** (solicitud explícita).
