# Platform Backend — Fase A — Reporte de implementación

**Fecha:** 2026-06-02  
**Alcance:** F-001, F-002, F-004, F-006 (orden mandatorio de cierre)  
**Referencia de auditoría:** `PLATFORM_BACKEND_READY_PHASE_A_AUDIT.md`

---

## Resumen ejecutivo

Se implementaron los cuatro hallazgos P0/P1 confirmados en la re-auditoría, sin endpoints nuevos y preservando esquemas de respuesta existentes. Cada ítem incluye pruebas unitarias de regresión y evidencia JSON bajo `app/bootstrap_v2/00_manifest/evidence/`.

| ID | Título | Estado |
|----|--------|--------|
| F-001 | Reactivación de cliente (`es_activo`) | Completado |
| F-002 | UUID `cliente_id` en Superadmin | Completado |
| F-004 | Paginación correcta de módulos | Completado |
| F-006 | Auth Config alineado a `platform_admin` (LBAC) | Completado |

---

## 1. F-001 — Reactivación de cliente

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/tenant/application/services/cliente_service.py` | `activar_cliente`: `es_activo=1` en UPDATE; `CLIENT_ALREADY_ACTIVE` solo si `es_activo` y `estado_suscripcion=='activo'` |
| `app/modules/tenant/presentation/endpoints_clientes.py` | OpenAPI/descripción de `PUT .../activar/` |
| `tests/unit/test_cliente_activar_restores_es_activo.py` | Nuevo |
| `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F001_CLIENTE_ACTIVAR_VALIDATION.json` | Evidencia QA |

### Cambio contractual / OpenAPI

- **Endpoint:** `PUT /api/v1/clientes/{cliente_id}/activar/`
- **Schema de respuesta:** sin cambios (`ClienteResponse` / `ClienteRead`).
- **Comportamiento:** tras eliminación lógica (`es_activo=0`, `estado_suscripcion=cancelado`), activar restaura operatividad completa del tenant.
- **400 `CLIENT_ALREADY_ACTIVE`:** ahora requiere ambos indicadores activos (antes bloqueaba incorrectamente solo por `estado_suscripcion`).

### Riesgos

- Bajo: clientes con `es_activo=1` y `estado_suscripcion=suspendido` siguen pudiendo activarse (comportamiento deseado).
- Revisar en staging que listados con `solo_activos=true` muestran el cliente reactivado.

### QA ejecutado

```text
python -m pytest tests/unit/test_cliente_activar_restores_es_activo.py -q
→ 3 passed
```

---

## 2. F-002 — UUID `cliente_id` en Superadmin

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/superadmin/presentation/endpoints_usuarios.py` | `list_usuarios_global`: `cliente_id: Optional[UUID]` |
| `app/modules/superadmin/application/services/superadmin_usuario_service.py` | `get_usuarios_globales`: `cliente_id: Optional[UUID]` |
| `app/modules/superadmin/application/services/superadmin_auditoria_service.py` | Filtros `cliente_id`, `usuario_id`, `cliente_origen_id`, `cliente_destino_id` → `UUID` |
| `tests/unit/test_superadmin_cliente_id_uuid_query.py` | Nuevo |
| `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F002_SUPERADMIN_UUID_VALIDATION.json` | Evidencia QA |

### Cambio contractual / OpenAPI

- **Breaking:** no (corrección de tipo erróneo `int` → `UUID`).
- **Efecto:** elimina **422** cuando el cliente envía UUID válido en query (`?cliente_id=...`).
- Endpoints de auditoría en presentación ya declaraban `Optional[UUID]`; servicios quedan alineados.

### Riesgos

- Bajo: consumidores que enviaban enteros ficticios dejarán de ser aceptados (comportamiento correcto vs. modelo BD).

### QA ejecutado

```text
python -m pytest tests/unit/test_superadmin_cliente_id_uuid_query.py -q
→ 3 passed
```

---

## 3. F-004 — Paginación correcta de módulos

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/modulos/application/services/modulo_service.py` | `_condiciones_listado_modulos`, `contar_modulos`; refactor filtros en `obtener_modulos` |
| `app/modules/modulos/presentation/endpoints_modulos.py` | `total = await ModuloService.contar_modulos(...)` |
| `tests/unit/test_modulos_pagination_total.py` | Nuevo |
| `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F004_MODULOS_PAGINATION_VALIDATION.json` | Evidencia QA |

### Cambio contractual / OpenAPI

- **Endpoint:** `GET /api/v1/modulos/`
- **Schema:** sin cambios (`PaginatedModuloResponse`).
- **Comportamiento:** `pagination.total`, `total_pages`, `has_next`, `has_prev` reflejan el conteo real en BD con los mismos filtros (`solo_activos`, `categoria`).

### Riesgos

- Una query COUNT adicional por listado (aceptable para catálogo de módulos de tamaño moderado).

### QA ejecutado

```text
python -m pytest tests/unit/test_modulos_pagination_total.py -q
→ 2 passed
```

---

## 4. F-006 — Auth Config alineado a platform_admin

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/auth/presentation/endpoints_auth_config.py` | `RoleChecker(["SUPER_ADMIN"])` → `@require_super_admin()` (LBAC) + `get_current_active_user` |
| `tests/unit/test_auth_config_lbac_platform_admin.py` | Nuevo |
| `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F006_AUTH_CONFIG_LBAC_VALIDATION.json` | Evidencia QA |

### Cambio contractual / OpenAPI

- **Endpoints:** `GET/PUT /api/v1/auth-config/clientes/{cliente_id}`, `GET /api/v1/auth-config/global`
- **Autorización:** operadores `platform_admin` con `access_level >= 5` (mismo criterio que `/clientes`).
- **OpenAPI:** descripciones actualizadas; código de respuesta **403** documentado explícitamente.
- **No** se exige rol con `nombre == 'SUPER_ADMIN'` (inexistente en seed `ADMIN_PLATFORM`).

### Riesgos

- Usuarios tenant con rol legacy `SuperAdministrador` por nombre siguen admitidos vía LBAC (`has_super_admin_role`).
- Usuarios sin nivel 5 ni flag superadmin seguirán en 403 (correcto).

### QA ejecutado

```text
python -m pytest tests/unit/test_auth_config_lbac_platform_admin.py tests/unit/test_superadmin_cliente_id_uuid_query.py::test_auth_config_uses_lbac_not_role_checker -q
→ 2 passed
```

### QA agregado (suite Fase A)

```text
python -m pytest tests/unit/test_cliente_activar_restores_es_activo.py tests/unit/test_superadmin_cliente_id_uuid_query.py tests/unit/test_modulos_pagination_total.py tests/unit/test_auth_config_lbac_platform_admin.py -q
→ 9 passed
```

---

## Evidencia de validación

| Hallazgo | Archivo evidencia |
|----------|-------------------|
| F-001 | `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F001_CLIENTE_ACTIVAR_VALIDATION.json` |
| F-002 | `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F002_SUPERADMIN_UUID_VALIDATION.json` |
| F-004 | `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F004_MODULOS_PAGINATION_VALIDATION.json` |
| F-006 | `app/bootstrap_v2/00_manifest/evidence/PHASE_A_F006_AUTH_CONFIG_LBAC_VALIDATION.json` |

---

## Commits generados

| Orden | SHA | Mensaje |
|-------|-----|---------|
| 1 | `74fa871` | `fix(tenant): F-001 restore es_activo on cliente activar` |
| 2 | `acaa611` | `fix(superadmin): F-002 UUID filters for cliente_id and audit` |
| 3 | `d4c9611` | `fix(modulos): F-004 correct pagination total via contar_modulos` |
| 4 | `f792087` | `fix(auth-config): F-006 LBAC require_super_admin for platform_admin` |
| 5 | `33830db` | `docs: Platform Backend Phase A implementation report` |

---

## Fuera de alcance (Fase A)

- F-003, F-005, F-010 y demás ítems del cierre integral.
- F-020 documentación de impersonación (`PLATFORM_IMPERSONATION_CONTRACT.md`) — diferido.

---

## Verificación manual recomendada (staging)

1. **F-001:** DELETE cliente → PUT activar → GET listado `solo_activos=true` incluye el tenant.
2. **F-002:** `GET /superadmin/usuarios/global?cliente_id=<uuid>` → 200 (no 422).
3. **F-004:** `GET /modulos/?skip=0&limit=5` → `pagination.total` estable entre páginas.
4. **F-006:** Login `platform_admin` → `GET /auth-config/global` → 200 (antes 403).
