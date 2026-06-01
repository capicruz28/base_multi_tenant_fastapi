# Auditoría — Minimal ERP Tenant Bootstrap

**Fase:** separada de RBAC/platform (congelados).  
**Meta:** tenant ERP mínimamente operativo tras onboarding (una `org_empresa` + vínculo admin).

---

## 1. Problema confirmado

| Hecho | Impacto |
|-------|---------|
| Onboarding crea cliente, roles, admin, `cliente_modulo`, `rol_permiso` | RBAC OK |
| **No** inserta `org_empresa` | Login admin sin `empresa_id` en JWT |
| `usuario.empresa_default_id` = NULL | `get_empresa_activa_para_login` sin empresa activa |
| `usuario_rol.empresa_id` = NULL | Admin “sin empresa”; bypass solo si hay filas en `org_empresa` + selección |

**Síntoma API:** `403` — *No hay empresa activa en la sesión* en `/auth/me`, `/auth/menu`, `/auth/permissions/me` (contrato `require_erp_session`).

---

## 2. Dependencias reales de `org_empresa`

### 2.1 Auth / sesión (crítico)

| Componente | Uso |
|------------|-----|
| `AuthService.get_empresa_activa_para_login` | JOIN `usuario_rol` ↔ `org_empresa`; usa `usuario.empresa_default_id` |
| `create_access_token(empresa_id=...)` | JWT operativo |
| `validate_erp_operational_session` | Exige `empresa_id` salvo `platform_admin` |
| Login admin sin empresas | L383–387: continúa **sin** `empresa_id` (onboarding legacy) |

### 2.2 ORG API

| Endpoint | Permiso | Requiere sesión empresa |
|----------|---------|-------------------------|
| `GET /org/empresa` | `org.empresa.leer` | No (tenant-wide `require_org_tenant_erp_session`) |
| `POST /org/empresa` | `org.empresa.crear` | No |
| Sucursales, CC, etc. | varios | **Sí** (`require_org_company_erp_session`) |

### 2.3 Menú / permisos

| Componente | Dependencia |
|------------|-------------|
| `MenuResolver` | `cliente_modulo` + permisos efectivos |
| `PermissionResolver` | `usuario_rol` + `empresa_id` para scope por empresa |
| Admin con 1 empresa + `empresa_default_id` | Resolución automática, sin `selection_token` |

### 2.4 Fuera de alcance (NO requeridos para smoke mínimo)

- `org_sucursal`, `inv_almacen`, plan contable, tributaria
- Catálogos geo (`cat_pais`, etc.) — nullable en `org_empresa`
- `moneda_base_id` — nullable

---

## 3. DDL mínimo `org_empresa` (V010)

**Obligatorios:** `cliente_id`, `codigo_empresa`, `razon_social`, `ruc`  
**Recomendados:** `nombre_comercial`, `email_principal` (desde contacto cliente)  
**Defaults:** `es_activo=1`, `zona_horaria`, `idioma_sistema`, etc.

---

## 4. Diseño mínimo correcto

### 4.1 Una empresa sede por tenant

| Campo | Origen onboarding |
|-------|-------------------|
| `codigo_empresa` | `EMP001` (primera sede) |
| `razon_social` | `cliente.razon_social` |
| `nombre_comercial` | `cliente.nombre_comercial` o razón social |
| `ruc` | `cliente.ruc` si válido; si no, RUC sintético único 11 dígitos |
| `email_principal` | `contacto_email` |

### 4.2 Vínculo admin (misma transacción)

1. `INSERT org_empresa`
2. `INSERT usuario` con `empresa_default_id = empresa_id`
3. `INSERT usuario_rol` con `empresa_id`, `es_empresa_default = 1`

### 4.3 Idempotencia

- Si ya existe ≥1 `org_empresa` activa para el tenant → reutilizar la primera (repair / re-onboarding).
- Si no existe → crear `EMP001`.

### 4.4 Orden en transacción onboarding

```
cliente → roles → org_empresa → usuario admin → usuario_rol → RBAC → auth_config → cfg_codigo (existente)
```

**No se modifica** `OnboardingRbacService`.

### 4.5 Post-condiciones smoke

| Paso | Esperado |
|------|----------|
| login | 200 + `access_token` con `empresa_id` |
| `/auth/me` | 200 |
| `/auth/menu` | 200, ≥1 módulo |
| `/auth/permissions/me` | 200, grants efectivos |
| `/org/empresa` | 200, count ≥ 1 |

---

## 5. Implementación

| Artefacto | Rol |
|-----------|-----|
| `minimal_erp_tenant_bootstrap_service.py` | `crear_empresa_inicial` + `vincular_admin_empresa` |
| `cliente_onboarding_service.py` | Orquestación (único cambio de flujo) |
| `repair_minimal_erp_tenant.py` | Tenants legacy sin empresa |
| `http_smoke_runner.py` | Validación estricta permisos cuando hay empresa |
| Tests unitarios | Idempotencia + campos mínimos |

---

## 6. Explícitamente NO incluido

- Sucursal, almacén, plan contable, tributaria
- Nuevas secuencias `cfg_codigo_secuencia` (el insert existente en onboarding no se amplía)
- Cambios en RBAC runtime, `permission_sync`, platform repair, JWT, frontend
