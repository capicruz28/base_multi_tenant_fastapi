# Login serialization fix — tenants recién creados

**Fecha:** 2026-05-21  
**Incidente E2E:** `POST /api/v1/auth/login/` → HTTP 500 tras onboarding con `razon_social = "E2E Validation Tenant S.A."`

---

## Causa raíz

| Capa | Comportamiento incorrecto |
|------|---------------------------|
| **Onboarding** (`ClienteOnboardingService._insertar_usuario_admin`) | `apellido` se copiaba desde `razon_social` (nombre legal), incluyendo `.`, dígitos y otros caracteres no permitidos. |
| **Login** (`endpoints.login` → `UserDataWithRoles.model_validate`) | Lee `apellido` de BD y valida con `UserDataBase.validar_nombre_apellido` (solo letras, espacios, guiones). |
| **Discrepancia** | La BD acepta cualquier `NVARCHAR`; la **respuesta** auth rechaza el valor al serializar `user_data`. |

No es fallo de JWT, refresh, RBAC ni `permission_sync`. Es **mapping onboarding + validación estricta en DTO de salida**.

### Stacktrace (reproducido)

```
pydantic_core.ValidationError: 1 validation error for UserDataWithRoles
apellido
  Value error, El nombre y apellido solo pueden contener letras, espacios y guiones...
  input_value='E2E Validation Tenant S.A.'
File: app/modules/auth/presentation/endpoints.py, line 428
  "user_data": UserDataWithRoles.model_validate(user_profile),
```

Misma ruta en flujo `empresa_selection_pending` (línea ~380 con `selection_profile`).

---

## Componentes involucrados

| Rol | Archivo / símbolo |
|-----|-------------------|
| Query / INSERT | `cliente_onboarding_service._insertar_usuario_admin` |
| Mapper perfil | `build_user_data_with_roles_dict` |
| Schema / validador | `UserDataBase`, `UserDataWithRoles` |
| Serializer respuesta | `UserDataWithRoles.model_validate` en `endpoints.login` |
| DTO respuesta | `Token.user_data`, `LoginEmpresaSelectionResponse.user_data` |

---

## Corrección (mínima)

1. **`app/shared/validators.py`** — `sanitize_person_name()`: quita caracteres no alfabéticos antes de validar Pydantic.
2. **`build_user_data_with_roles_dict`** — sanitiza `nombre` y `apellido` al armar el dict (compatibilidad con filas legacy en BD).
3. **`cliente_onboarding_service`** — `apellido` desde `contacto_nombre` o `razon_social` **sanitizado**, no copia literal.

**No modificado:** `onboarding_rbac_service`, RBAC, `auth_service` core, validador Pydantic (reglas intactas).

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/shared/validators.py` | `sanitize_person_name()` |
| `app/modules/auth/presentation/schemas.py` | Uso en `build_user_data_with_roles_dict` |
| `app/modules/tenant/application/services/cliente_onboarding_service.py` | Apellido admin sanitizado al insertar |
| `app/core/auth/user_builder.py` | Sanitiza nombre/apellido en `UsuarioReadWithRoles` (`/me`, menú, deps) |
| `tests/unit/test_login_user_data_serialization.py` | Regresión unitaria |
| `app/bootstrap_v2/00_manifest/LOGIN_SERIALIZATION_FIX.md` | Este documento |

---

## Impacto

| Área | Efecto |
|------|--------|
| Login tenant nuevo | **Corregido** — `user_data` serializa sin 500 |
| Tenants legacy con apellido “sucio” en BD | **Corregido** en respuesta (sanitize en mapper); valor en BD sin cambiar |
| Nuevos onboardings | Apellido persistido ya limpio |
| Validación API usuarios | Sin cambio (reglas `UserDataBase` iguales) |
| RBAC / menú / JWT | Sin cambio de lógica |

---

## Validación recomendada

```bash
pytest tests/unit/test_login_user_data_serialization.py -q
```

E2E manual (tenant `e2evalid01`, `razon_social` con `S.A.` en BD):

| Paso | Resultado post-fix |
|------|-------------------|
| `POST /auth/login/` | **200** — `user_data.apellido` = `E E Validation Tenant S A` |
| Refresh token | **OK** — `[STORE-TOKEN]` en logs |
| `empresa_selection_pending` | `null` (0 empresas; admin onboarding sin empresa) |
| JWT `empresa_id` | Ausente hasta crear/seleccionar empresa (esperado) |
| `GET /auth/me/` | **403** «No hay empresa activa…» (regla ERP, no serialización) |
| `GET /auth/menu` | **403** idem — requiere sesión operativa con empresa |

Tras `POST /org/empresa` y selección de empresa, `/me` y `/menu` deben responder 200 (flujo multiempresa estándar).

---

## Riesgos residuales

| Riesgo | Mitigación |
|--------|------------|
| Apellido mostrado distinto al legal (`S.A.` → `S A`) | Esperado; usar `contacto_nombre` en onboarding para etiqueta humana |
| Dígitos en razón social (`E2E` → `E E`) | El validador auth no admite números; `sanitize_person_name` los elimina |
| Solo sanitización en respuesta, BD legacy sin UPDATE | Login OK; opcional job UPDATE `usuario.apellido` |
| `nombre` con caracteres raros | Misma función aplicada en mapper |

---

## Backward compatibility

- Validador Pydantic **sin relajar** (seguridad/consistencia FE).
- Datos existentes en BD **no migrados**; login tolera vía mapper.
- Nuevos inserts **más limpios** sin romper contratos API.
