# Implementación — Fix 500 login usuario sin roles (caso D1)

**Fecha:** 2026-06-01  
**Referencias:** [LOGIN_NO_ROLES_500_ROOT_CAUSE_AUDIT.md](./LOGIN_NO_ROLES_500_ROOT_CAUSE_AUDIT.md)  
**Evidencia JSON:** [LOGIN_NO_ROLES_500_FIX_VALIDATION.json](../../bootstrap_v2/00_manifest/evidence/LOGIN_NO_ROLES_500_FIX_VALIDATION.json)

---

## 1. Cambio aplicado

| Archivo | Cambio |
|---------|--------|
| `app/modules/auth/presentation/endpoints.py` | Import `CustomException`; en `login()` añadir `except CustomException: raise` antes del `except Exception` genérico |

```python
from app.core.exceptions import AuthenticationError, CustomException

    except HTTPException:
        raise
    except CustomException:
        raise
    except Exception as e:
        ...
```

**Alcance:** propagación de excepciones; **sin** cambio en `assert_operational_login_allowed`, mensajes, códigos RBAC ni política D1.

---

## 2. Causa raíz y efecto del fix

| Antes | Después |
|-------|---------|
| `AuthorizationError` (`USER_WITHOUT_COMPANY`) capturada por `except Exception` | `CustomException` re-lanzada al handler global |
| HTTP **500** genérico | HTTP **403** + `error_code: USER_WITHOUT_COMPANY` |
| Log `Error inesperado en /login/` | Log `CustomException: USER_WITHOUT_COMPANY - ...` |

---

## 3. Pruebas ejecutadas

### 3.1 Unit tests

| Test | Resultado |
|------|-----------|
| `tests/unit/test_login_custom_exception_propagation.py` | **PASS** (2/2) |

- `test_login_reraises_custom_exception_for_user_without_company` — no enmascara `AuthorizationError`
- `test_login_still_maps_unexpected_errors_to_500` — errores no previstos siguen en 500

```bash
python -m pytest tests/unit/test_login_custom_exception_propagation.py -q
```

### 3.2 QA HTTP runtime (tenant `t3usr971acefb`)

**Entorno:** Docker `fastapi_backend` — `http://localhost:8000`  
**Timestamp evidencia:** `2026-06-01T07:25:58Z`  
**Script:** `scripts/_run_login_no_roles_fix_qa.py`

| Caso | Escenario | HTTP esperado | HTTP obtenido | Veredicto |
|------|-----------|---------------|---------------|-----------|
| **1** | Usuario sin roles (`qa_login_norole_8c3956`) | **403** | **403** | PASS |
| **2** | `USER_TENANT` asignado | **200** + token | **200** | PASS |
| **3** | `MANAGER_TENANT` asignado | **200** + token | **200** | PASS |
| **4** | `admin` (ADMIN_TENANT) | **200** + token | **200** | PASS |
| **5** | Contraseña incorrecta | **401** | **401** | PASS |

**Verdict global QA:** `PASS`

### 3.3 Respuesta caso 1 (403 — contrato FE)

```json
{
  "detail": "El usuario no tiene empresas asignadas. Contacte al administrador del tenant.",
  "error_code": "USER_WITHOUT_COMPANY"
}
```

`internal_code` preservado vía handler `CustomException` → campo JSON `error_code`.

---

## 4. Evidencia en logs post-fix

Caso sin roles — handler global (no traceback 500):

```text
2026-06-01 07:26:08,342 - auth_service - INFO - [AUTH] Login exitoso: username='qa_login_norole_8c3956' ...
2026-06-01 07:26:08,361 - app.core.exceptions - ERROR - CustomException: USER_WITHOUT_COMPANY - El usuario no tiene empresas asignadas. Contacte al administrador del tenant. | Path: /api/v1/auth/login/ | Method: POST
```

**Ausente** (pre-fix):

```text
endpoints - ERROR - Error inesperado en /login/ ... AuthorizationError
POST /api/v1/auth/login/ 500
```

Caso 5 — credenciales inválidas (sin regresión):

```text
2026-06-01 07:26:11,526 - auth_service - WARNING - [AUTH] Contraseña incorrecta para: username='qa_login_norole_8c3956' ...
```

---

## 5. Roles resueltos en tenant T3 (QA)

| `codigo_rol` | `rol_id` |
|--------------|----------|
| `USER_TENANT` | `8a6c861c-afb3-4afd-afb2-a151c5079bf1` |
| `MANAGER_TENANT` | `826e3965-fed2-4f6d-a342-e05d21585bd5` |
| `ADMIN_TENANT` | `aa3c99e2-f072-48c1-8598-c553be81d591` |

---

## 6. Política RBAC V1 (sin cambios)

| Regla | Estado post-fix |
|-------|-----------------|
| Caso **D1** — operativo sin empresas elegibles | Rechazo login |
| `internal_code` | `USER_WITHOUT_COMPANY` |
| Login con rol scoped (USER / MANAGER) | Permitido (**200**) |
| Admin tenant (`admin`) | Permitido (**200**) |
| Credenciales inválidas | **401** |

No se implementó login sin perfiles (alternativa A de la auditoría).

---

## 7. Archivos tocados

| Archivo | Tipo |
|---------|------|
| `app/modules/auth/presentation/endpoints.py` | Fix producción |
| `tests/unit/test_login_custom_exception_propagation.py` | Regresión unitaria |
| `scripts/_run_login_no_roles_fix_qa.py` | QA runtime |
| `app/bootstrap_v2/00_manifest/evidence/LOGIN_NO_ROLES_500_FIX_VALIDATION.json` | Evidencia JSON |
| `app/docs/auditoria/LOGIN_NO_ROLES_500_FIX_IMPLEMENTATION.md` | Este documento |

**Sin commit** (solicitud explícita).
