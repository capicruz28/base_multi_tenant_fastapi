# Implementación — Fix 500 `PUT /api/v1/usuarios/{usuario_id}/`

**Fecha:** 2026-06-01  
**Referencias:** [USER_UPDATE_500_RUNTIME_ROOT_CAUSE.md](./USER_UPDATE_500_RUNTIME_ROOT_CAUSE.md)  
**Evidencia JSON:** [USER_UPDATE_500_FIX_VALIDATION.json](../../bootstrap_v2/00_manifest/evidence/USER_UPDATE_500_FIX_VALIDATION.json)

---

## 1. Cambio aplicado

| Archivo | Cambio |
|---------|--------|
| `app/modules/users/presentation/endpoints.py` L358–362 | `update_data=update_data` → `usuario_data=update_data` |

```python
updated_usuario = await UsuarioService.actualizar_usuario(
    cliente_id=current_user.cliente_id,
    usuario_id=usuario_id,
    usuario_data=update_data,
)
```

**Alcance:** una línea; sin cambios en servicio, schemas, SQL ni frontend.

---

## 2. Causa raíz (confirmada)

| Antes | Después |
|-------|---------|
| `TypeError: unexpected keyword argument 'update_data'` | Llamada alineada con firma `usuario_data: Dict` |
| 500 genérico vía `@handle_service_errors` | Flujo normal de actualización |

---

## 3. Pruebas ejecutadas

### 3.1 Unit test (regresión contrato)

| Test | Resultado |
|------|-----------|
| `tests/unit/test_user_update_endpoint_kwargs.py` | **PASS** (1/1) |

Verifica que `actualizar_usuario` del endpoint invoca el servicio con `usuario_data` y **sin** `update_data`.

```bash
python -m pytest tests/unit/test_user_update_endpoint_kwargs.py -q
```

### 3.2 QA HTTP runtime (tenant `t3usr971acefb`)

**Entorno:** Docker `fastapi_backend` en `http://localhost:8000`  
**Timestamp evidencia:** `2026-06-01T06:57:50Z`  
**Admin:** `admin` / credenciales onboarding T3 (evidencia T3)

| # | Caso | Método / ruta | Resultado | Evidencia |
|---|------|---------------|-----------|-----------|
| 1 | **Actualización usuario** (caso QA original) | `PUT /api/v1/usuarios/102fca1b-000f-42d6-8183-e5bd72ff607b/` | **200** | `nombre: "Supervisor"`, `correo` persistido |
| 2 | **Creación usuario** | `POST /api/v1/usuarios/` | **201** | `usuario_id` generado |
| 3 | **Asignación rol** | `POST /api/v1/usuarios/{id}/roles/{rol_id}/` | **201** | Rol `Usuario` (`8a6c861c-…`) |
| 4 | **Revocación rol** | `DELETE /api/v1/usuarios/{id}/roles/{rol_id}/` | **200** | Revoke OK |
| 5 | **Login admin** | `POST /api/v1/auth/login/` | **200** | Token obtenido |
| 6 | **Login user** | `POST /api/v1/auth/login/` (`qa_user_*` + rol Usuario) | **200** | Token obtenido |
| 7 | **Login manager** | `POST /api/v1/auth/login/` (`mgr_qa_*` + rol Supervisor) | **200** | Token obtenido |

**Verdict global QA:** `PASS`

**Nota roles en tenant T3:** `GET /roles/all-active/` devuelve `nombre` (`Administrador`, `Supervisor`, `Usuario`) con `codigo_rol: null` en API; assign/revoke usó `rol_id` del rol **Usuario** / **Supervisor** (equivalente USER_TENANT / MANAGER_TENANT en UI).

---

## 4. Evidencia en logs post-fix

Tras el fix, el contenedor registra actualización real (sin `ERROR INESPERADO`):

```text
2026-06-01 06:57:56,105 - app.modules.users.application.services.user_service - INFO -
  Usuario ID 102fca1b-000f-42d6-8183-e5bd72ff607b actualizado exitosamente en cliente e4c8e906-...
2026-06-01 06:57:56,105 - app.modules.users.presentation.endpoints - INFO -
  Usuario ID 102fca1b-000f-42d6-8183-e5bd72ff607b actualizado exitosamente: 'super'
```

**Ausente** (comparado con fallo pre-fix):

```text
ERROR INESPERADO en actualizar_usuario: ... unexpected keyword argument 'update_data'
```

---

## 5. Payload QA reproducido

**Request:**

```http
PUT /api/v1/usuarios/102fca1b-000f-42d6-8183-e5bd72ff607b/
Content-Type: application/json

{
  "correo": "supers@gmail.com",
  "nombre": "Supervisor",
  "apellido": "Super",
  "es_activo": true
}
```

**Response (200):** cuerpo `UsuarioRead` con `nombre: "Supervisor"` y demás campos del `OUTPUT` SQL.

---

## 6. Regresiones descartadas

| Área | Estado en QA |
|------|----------------|
| Frontend / payload | Sin cambios requeridos |
| RBAC `admin.usuario.actualizar` | Autorizado (200 en PUT) |
| SQL `UPDATE dbo.usuario` | Ejecutado (log servicio) |
| Tenant / multiempresa | Sin impacto (mismo tenant T3) |
| Create / assign / revoke / logins | PASS en suite §3.2 |

---

## 7. Resumen

| Ítem | Estado |
|------|--------|
| Fix implementado | ✅ |
| Unit test regresión | ✅ PASS |
| QA actualización (caso original) | ✅ HTTP 200 |
| QA creación / roles / logins | ✅ PASS |
| Evidencia JSON | ✅ `USER_UPDATE_500_FIX_VALIDATION.json` |
| Commit | Pendiente (no solicitado) |

---

*Implementación y validación completadas 2026-06-01.*
