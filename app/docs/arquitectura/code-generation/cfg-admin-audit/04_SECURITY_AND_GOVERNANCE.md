# Seguridad y gobernanza

**Paquete:** `cfg-admin-audit`  
**Fecha:** 2026-07-17

---

## 1. Estado AS-IS de seguridad CFG admin

| Control | Estado |
|---------|--------|
| Endpoints `/cfg/*` | ❌ Inexistentes → superficie de ataque admin = **cero** (y capacidad admin = cero) |
| Permisos `cfg.secuencias.*` | ❌ No sembrados en RBAC |
| Filtro `cliente_id` en Motor | ✅ Store/Repo usan tenant en lookups/writes |
| Impersonación-safe session deps CFG | ❌ `cfg_deps.py` no existe |
| Soft delete físico | N/A — se usa `es_activo`; sin DELETE físico previsto |

Hoy la gobernanza de cfg es **solo vía onboarding + runtime Motor**, no vía Tenant Admin.

---

## 2. Modelo RBAC propuesto (diseño, no implementado)

Fuente: `codigo-generation-admin/06_SECURITY_RBAC_AND_FRONTEND.md`.

| Permiso | Operaciones |
|---------|-------------|
| `cfg.secuencias.consultar` | List, detail, preview, validate-manual |
| `cfg.secuencias.actualizar` | PATCH B-fields, activar/desactivar |
| `cfg.secuencias.mantener` | `align_counter` |
| `cfg.secuencias.diagnosticar` | Diagnóstico / drift |

**Separación crítica:** `mantener` no debe heredarse de `actualizar` (align es operación de implantación).

**Gates ERP V4 esperados:**

- Router padre: `require_erp_session`
- `cliente_id` operativo: `get_cfg_session_client_id` (patrón ORG/INV)
- Cross-tenant / cross-scope: **404**, no 403
- Prohibido autorizar con `cliente_id` en body

---

## 3. Relaciones tenant / cliente / empresa

| Dimensión | Gobernanza |
|-----------|------------|
| **Tenant (`cliente_id`)** | Dueño de todas las filas cfg; filtro obligatorio en toda query admin |
| **Cliente (tabla `cliente`)** | FK CASCADE en DDL; borrado tenant implica cascada (platform) |
| **Empresa** | Campo A; filtro de listado; no reasignable; no confundir con autorización primaria |
| **Almacén / PV** | Scopes lazy; admin puede listar filas cuando existan |

Identidad autenticada ≠ contexto operativo ERP (STANDARDS §3.7): mismo riesgo de impersonación que ORG/INV si se usa `current_user.cliente_id` incorrectamente.

---

## 4. Auditoría

### AS-IS en tabla

| Campo | Uso |
|-------|-----|
| `fecha_creacion` | Insert |
| `fecha_actualizacion` | Previsto en updates |
| `usuario_actualizacion_id` | Previsto en updates admin |

`CfgCodigoSecuenciaRepository.update_secuencia` **hoy no setea** `fecha_actualizacion` ni `usuario_actualizacion_id` en el `.values(...)` — gap de auditoría en el método existente.

### Diseño admin

| Evento | Mínimo |
|--------|--------|
| PATCH config | diff + usuario + timestamp |
| align | before/after `ultimo_numero` + motivo |
| activar/desactivar | nuevo `es_activo` |

Persistencia futura: columnas cfg + posible `auth_audit_log` / log aplicación.

---

## 5. Superficies peligrosas (si se implementa mal)

| Riesgo | Mitigación normativa |
|--------|----------------------|
| PATCH `ultimo_numero` | Prohibido; solo Gateway.align |
| Cambiar `generation_policy` desde UI | Prohibido (clase C) |
| Cambiar `sequence_key` / fingerprint | Prohibido (clase A) |
| Escritura Dedicated sin session tenant | ADJ-03 / Conflict o error interno |
| Bypass Gateway en preview/align | Reimplementación = divergencia; usar Gateway |
| Permiso `actualizar` demasiado amplio | Separar `mantener` |

---

## 6. Compatibilidad Shared / Dedicated (seguridad)

Misma política de autorización; diferencia solo en conexión:

- Shared: sesión DEFAULT con `client_id`
- Dedicated: `get_connection_for_tenant` + session obligatoria en writes

Admin debe seguir el mismo patrón UoW que ORG/INV CREATE con Motor.

---

## 7. Conclusión de gobernanza

La seguridad del **Motor** ya aísla por tenant en runtime. La seguridad del **Administrador** aún no existe porque el módulo no existe. El diseño RBAC de cuatro acciones es adecuado y debe sembrarse **antes** o **junto** a Fase A (al menos `consultar`).
