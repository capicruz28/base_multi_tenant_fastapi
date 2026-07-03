# F12-G2 — Dedicated Runtime ↔ DDL Alignment Audit

**Fecha:** 2026-06-28  
**Modo:** Solo auditoría arquitectónica — sin correcciones, sin DDL, sin cambios de código  
**Alcance:** Catálogo oficial `dedicated_schema_v2` vs runtime backend actual para tenants `tipo_instalacion = dedicated`  
**Antecedente:** [F12-G1 — Dedicated DDL Root Cause Audit](./F12_G1_DEDICATED_DDL_ROOT_CAUSE.md)

---

## 1. Conclusión ejecutiva

El catálogo DDL Dedicated **no está completamente alineado** con el runtime actual, pero la desalineación **no es homogénea**:

| Área | Estado | Veredicto |
|------|--------|-----------|
| ERP completo (`V010`) | 100 tablas creadas y consumidas en DP | **Alineado** |
| DTSP identidad/RBAC/menú (F4-05b) | 9 tablas + `rol_permiso` creadas; runtime F11 lee réplica local | **Alineado** |
| IAM Session V2/V3 (`user_session`, `token_family`, `refresh_tokens`) | Runtime enruta a **Control Plane** (ADR-002-A); ausencia en DP es **esperada MVP** | **Alineado por diseño** |
| Auditoría auth (`auth_audit_log`) | Runtime inserta en **DP**; catálogo **no crea** la tabla | **Gap crítico (Clase A)** |
| Sync usuarios (`log_sincronizacion_usuario`) | Runtime inserta en DP (conexión implícita DEFAULT); catálogo no crea | **Gap latente (Clase A/C)** |
| Control Plane (`cliente`, provisioning, auth config, …) | Solo CP; runtime usa ADMIN | **Correcto (Clase B)** |

**Respuesta a “¿el catálogo Dedicated está obsoleto?”:** **Sí, parcialmente.** El perfil `dedicated_schema_v2` (PR-F4-05b) refleja correctamente DTSP post-ADR-003-A, pero **quedó congelado antes** de cerrar BL-1.0 (RD-07: `auth_audit_log` = `tenant_data`) y **nunca incorporó** el bloque audit tenant del legacy `TABLAS_BD_DEDICADA.sql`. Los componentes IAM Session V3 (`V031`) **no debían** incorporarse al manifiesto Dedicated mientras RD-11 permanece en CP (ADR-002-A).

El onboarding Dedicated reporta éxito porque `_verify_dtsp_schema` valida solo **10 tablas** (DTSP + `rol_permiso`), no paridad runtime completa.

---

## 2. Metodología

1. **Inventario runtime:** búsqueda en código de referencias SQL / `Table(...)` y resolución de conexión (`DatabaseConnection.DEFAULT` + `client_id` vs `ADMIN`) en módulos auth, IAM, RBAC, menú, tenant, users, superadmin, ORG e impersonación.
2. **Inventario DDL Dedicated:** manifiesto `DEDICATED_SCHEMA_MANIFEST_V2`, scripts `05_dedicated/`, `BootstrapScriptRunner._verify_dtsp_schema`, seeds S6/S7.
3. **Inventario Shared:** `BOOTSTRAP_ORDER.md` Fases 1–4 + migraciones `V031`–`V033` aplicables a CP.
4. **Cruce:** matriz con clasificación obligatoria A / B / C por tabla no trivial.
5. **Evidencia empírica:** probes read-only Docker (F12-G1) sobre tenants `acces` (`erp_cli017`), `acmec` (`erp_cli013`), outlier `acce` (`erp_cli016`).

**No se asume** que todo lo que existe en Shared deba replicarse en Dedicated. El objetivo es el **conjunto mínimo correcto** para soportar el runtime **sin depender del CP** donde BL-1.0 exige `tenant_data` en DP.

---

## 3. Inventario 1 — Tablas utilizadas por el runtime Dedicated

### 3.1 Leyenda de routing runtime

| Patrón | Significado en Dedicated |
|--------|--------------------------|
| **DP** | `DatabaseConnection.DEFAULT` + `client_id` explícito → BD `erp_{codigo}` |
| **CP** | `DatabaseConnection.ADMIN` → BD central (`bd_caxis_saas`) |
| **Redis** | Fuera de SQL (blacklist access tokens) |

### 3.2 IAM / Auth / Session

| Tabla | Routing Dedicated | Módulo / servicio | Evidencia código |
|-------|:-----------------:|-------------------|------------------|
| `user_session` | **CP** | `session_*_queries_core`, `SessionCreationService`, `SessionRotationService`, … | `SESSION_STORE_CONNECTION = DatabaseConnection.ADMIN` (`session_store_connection.py`) |
| `token_family` | **CP** | Idem IAM V2/V3 | Idem |
| `refresh_tokens` | **CP** | `RefreshTokenService`, login/refresh endpoints | Idem |
| `auth_audit_log` | **DP** | `AuditService.registrar_auth_event` ← `SessionAuditEmitter`, `AuthService`, `ImpersonationService`, `RefreshTokenService` | `database_type == "multi"` → `DEFAULT` (`audit_service.py` L130–136) |
| `log_sincronizacion_usuario` | **DP** (implícito) | `AuditService.registrar_log_sincronizacion_usuario` | `execute_insert` sin `connection_type` → DEFAULT |
| `cliente_auth_config` | **CP** | `AuthConfigGateway`, `AuthService` (expiración JWT) | ADR-012 SSOT CP |
| Access token blacklist | **Redis** | `session_redis_bridge`, logout/revoke | No es tabla SQL |

### 3.3 RBAC / Menú / Identity (DTSP)

| Tabla | Routing Dedicated | Módulo / servicio |
|-------|:-----------------:|-------------------|
| `usuario` | **DP** | Auth, users, impersonation (lookup operador) |
| `rol` | **DP** | RBAC, onboarding seed S7 |
| `usuario_rol` | **DP** | Auth JWT claims, RBAC |
| `permiso` | **DP** (réplica) + **CP** (SSOT sync) | `permission_catalog_store` → DEFAULT; `DedicatedPermissionCatalogSyncService` S6 |
| `rol_permiso` | **DP** | `permisos_usuario_service`, `permisos_negocio_service` (grants en DP) |
| `rol_menu_permiso` | **DP** | `MenuResolver`, `modulo_menu_service` |
| `modulo` | **DP** (réplica) | `menu_catalog_store`, seeds S6 |
| `modulo_seccion` | **DP** | Idem |
| `modulo_menu` | **DP** | `MenuResolver`, `/auth/me/menu` |
| `cliente_modulo` | **DP** | Licenciamiento tenant, filtros permiso/menú |
| `modulo_rol_plantilla` | **CP** | `ModuloRolPlantillaService` — solo ADMIN |

### 3.4 Tenant / Platform (Control Plane)

| Tabla | Routing | Uso |
|-------|:-------:|-----|
| `cliente` | **CP** | Routing, superadmin, provisioning |
| `cliente_conexion` | **CP** | Metadata BD dedicada, activation S8–S10 |
| `federacion_identidad` | **CP** | Identidad federada (si aplica) |
| `tenant_provisioning_run` | **CP** | Saga F4 orchestrator |
| `tenant_provisioning_step` | **CP** | Saga F4 steps |

### 3.5 ORG / ERP / SYS_ADMIN

| Grupo | Tablas (~100) | Routing | Servicios |
|-------|---------------|:-------:|-----------|
| Catálogos `cat_*` | 5 | **DP** | Maestros ORG/INV |
| ORG | `org_empresa`, `org_sucursal`, … | **DP** | Session scope ERP, onboarding S7 |
| INV, PUR, SLS, … | Resto `V010` | **DP** | Módulos ERP operativos |
| `cfg_codigo_secuencia` | 1 | **DP** | Secuencias documento; seed S7 |
| SYS_ADMIN | Menú vía DTSP `modulo*` + permisos sync | **DP** réplica | No tabla propia |

### 3.6 Resumen inventario runtime (no-ERP)

**Tablas transversales no-ERP que el runtime toca en contexto Dedicated:**

```
DP obligatorio por código:  auth_audit_log, log_sincronizacion_usuario (insert),
                            usuario, rol, usuario_rol, permiso, rol_permiso,
                            rol_menu_permiso, modulo, modulo_seccion, modulo_menu,
                            cliente_modulo, cfg_codigo_secuencia, org_empresa (+ ERP)

CP por diseño ADR:          user_session, token_family, refresh_tokens,
                            cliente, cliente_conexion, cliente_auth_config,
                            federacion_identidad, tenant_provisioning_*,
                            modulo_rol_plantilla

Híbrido tolerado MVP:       permiso (réplica DP + SSOT CP via S6 sync)
```

---

## 4. Inventario 2 — Tablas creadas por `dedicated_schema_v2`

### 4.1 Manifiesto oficial

Fuente: `app/infrastructure/provisioning/script_manifest.py` → `DEDICATED_SCHEMA_MANIFEST_V2`

| Orden | script_code | Archivo | Tablas creadas |
|------:|-------------|---------|----------------|
| 1 | `apply_schema_erp_v010` | `01_schema/V010__tablas_bd_erp_completo.sql` | **100** tablas ERP (`cat_*`, `org_*`, `inv_*`, …, `cfg_codigo_secuencia`) |
| 2 | `apply_schema_tenant_store_v020` | `05_dedicated/V020__tenant_identity_rbac_store.sql` | **9** tablas DTSP |
| 3 | `apply_schema_rbac_v010` | `05_dedicated/V010__rbac_tablas_dedicated.sql` | `rol_permiso` |

**Total DDL manifiesto:** **110 tablas** (+ `bootstrap_applied` creada por runner).

### 4.2 Tablas DTSP (detalle)

`modulo`, `modulo_seccion`, `modulo_menu`, `permiso`, `rol`, `usuario`, `usuario_rol`, `cliente_modulo`, `rol_menu_permiso`.

### 4.3 Verificación post-bootstrap

`BootstrapScriptRunner._verify_dtsp_schema` exige únicamente:

```text
DTSP_REQUIRED_TABLES ∪ { rol_permiso }   → 10 tablas
```

**No verifica:** ERP individual, `auth_audit_log`, sesiones IAM, `cfg_codigo_secuencia` (solo datos vía S7), `bootstrap_applied`.

### 4.4 Seeds post-DDL (S6 / S7)

| Step | Servicio | Tablas pobladas |
|------|----------|-----------------|
| S6 | `DedicatedCatalogSeedService` + `DedicatedPermissionCatalogSyncService` | `modulo*`, `permiso`, `cliente_modulo`, `rol_menu_permiso` (catálogo) |
| S7 | `DedicatedTenantSeedService` | `rol`, `org_empresa`, `usuario`, `usuario_rol`, `rol_permiso`, `cfg_codigo_secuencia` |

Perfil seed: `tenant_seed_profiles.py` — expectativas de filas incl. `cfg_codigo_secuencia`.

### 4.5 Tablas explícitamente excluidas del catálogo Dedicated

Documentado en DTSP profile y F12-G1:

- Bloque CP: `cliente`, `cliente_conexion`, `cliente_auth_config`, `federacion_identidad`
- Bloque IAM/audit Shared: `user_session`, `token_family`, `refresh_tokens`, `auth_audit_log`, `log_sincronizacion_usuario`
- CP provisioning: `tenant_provisioning_run`, `tenant_provisioning_step`
- CP plantillas: `modulo_rol_plantilla`

---

## 5. Inventario 3 — Tablas Shared (Control Plane) de referencia

Bootstrap central (`BOOTSTRAP_ORDER` Fases 1–4 + migraciones operativas):

| Script | Tablas relevantes adicionales vs Dedicated |
|--------|-------------------------------------------|
| `V010__tablas_bd_erp_completo.sql` | Mismo bloque ERP (co-located en CP Shared) |
| `V020__tablas_bd_central.sql` | CP registry + DTSP-like + **auth/sesión/audit inline** |
| `V030__rbac_tablas_central.sql` | `permiso`, `rol_permiso` (Shared; Dedicated usa DTSP + dedicated RBAC) |
| `V031__iam_session_management_v3.sql` | Evolución IAM Session (CP Shared) |
| `V032__tenant_provisioning_state.sql` | Provisioning saga state |
| `V033__remove_cross_plane_session_fks.sql` | FK cross-plane (CP) |

Shared CP típico post-bootstrap: **~138 tablas** (medición F12-G1).

---

## 6. Matriz Runtime vs DDL

### 6.1 Bloque transversal (auth / IAM / audit / platform)

| Tabla | Runtime usa (Dedicated) | Dedicated crea | Shared crea | Obligatoria DP | Estado | Clase |
|-------|:---------------------:|:--------------:|:-----------:|:--------------:|--------|:-----:|
| `auth_audit_log` | ✅ INSERT DP | ❌ | ✅ V020 | **Sí** (RD-07) | **GAP activo** | **A** |
| `log_sincronizacion_usuario` | ✅ INSERT DP | ❌ | ✅ V020 | **Sí** si sync cross-install | **GAP latente** | **A/C** |
| `user_session` | ✅ CP | ❌ | ✅ V020/V031 | No (ADR-002-A) | Alineado MVP | **B** |
| `token_family` | ✅ CP | ❌ | ✅ V020/V031 | No | Alineado MVP | **B** |
| `refresh_tokens` | ✅ CP | ❌ | ✅ V020/V031 | No | Alineado MVP | **B** |
| `cliente` | ✅ CP read | ❌ | ✅ V020 | No | Alineado | **B** |
| `cliente_conexion` | ✅ CP | ❌ | ✅ V020 | No | Alineado | **B** |
| `cliente_auth_config` | ✅ CP | ❌ | ✅ V020 | No (ADR-012) | Alineado | **B** |
| `federacion_identidad` | ✅ CP | ❌ | ✅ V020 | No | Alineado | **B** |
| `tenant_provisioning_run` | ✅ CP | ❌ | ✅ V032 | No | Alineado | **B** |
| `tenant_provisioning_step` | ✅ CP | ❌ | ✅ V032 | No | Alineado | **B** |
| `modulo_rol_plantilla` | ✅ CP | ❌ | ✅ V020 | No | Alineado | **B** |
| Redis blacklist | ✅ | N/A | N/A | N/A | Fuera DDL | — |

### 6.2 Bloque DTSP / RBAC / menú

| Tabla | Runtime usa (Dedicated) | Dedicated crea | Shared crea | Obligatoria DP | Estado | Clase |
|-------|:---------------------:|:--------------:|:-----------:|:--------------:|--------|:-----:|
| `usuario` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |
| `rol` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |
| `usuario_rol` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |
| `permiso` | ✅ DP (réplica) | ✅ DTSP | ✅ V030 | Sí (réplica local) | Alineado | — |
| `rol_permiso` | ✅ DP | ✅ dedicated V010 | ✅ V030 | Sí | Alineado | — |
| `rol_menu_permiso` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |
| `modulo` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |
| `modulo_seccion` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |
| `modulo_menu` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |
| `cliente_modulo` | ✅ DP | ✅ DTSP | ✅ V020 | Sí | Alineado | — |

### 6.3 ORG / ERP / config

| Tabla / grupo | Runtime usa | Dedicated crea | Shared crea | Obligatoria DP | Estado |
|---------------|:-----------:|:--------------:|:-----------:|:--------------:|--------|
| `org_empresa` + ERP (~99 tablas) | ✅ DP | ✅ V010 | ✅ V010 | Sí | Alineado |
| `cfg_codigo_secuencia` | ✅ DP | ✅ V010 | ✅ V010 | Sí | Alineado (datos S7) |
| `bootstrap_applied` | ✅ (markers) | ✅ runner | ❌ | Sí (provisioning) | Alineado |

### 6.4 Evidencia empírica tenants Dedicated (F12-G1)

| Objeto | `erp_cli017` (acces) | `erp_cli013` (acmec) | `erp_cli016` (acce) outlier |
|--------|:--------------------:|:--------------------:|:---------------------------:|
| DTSP + ERP + `rol_permiso` | ✅ | ✅ | ✅ |
| `auth_audit_log` | ❌ | ❌ | ✅ * |
| IAM session trio | ❌ | ❌ | ❌ |
| `log_sincronizacion_usuario` | ❌ | ❌ | ❌ |

\* Outlier sugiere DDL manual/legacy fuera del manifiesto v2 estándar.

---

## 7. Gaps — detalle por tabla faltante

### 7.1 `auth_audit_log` — **Crítico (activo)**

| Campo | Detalle |
|-------|---------|
| **Módulo** | Auth / IAM / Superadmin |
| **Servicios** | `AuditService`, `SessionAuditEmitter`, `AuthService`, `ImpersonationService`, `RefreshTokenService`, `PasswordChangeService` (vía audit) |
| **Endpoints afectados** | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/sessions/*`, impersonation start/stop, cambio empresa, admin password reset (eventos secundarios) |
| **Impacto** | Inserts fallan en DP (fail-soft: login/ERP siguen; **auditoría auth no persiste**). Superadmin auditoría multi-DB no encuentra logs en DP. Frontend admin seguridad incompleto. |
| **Criticidad** | **P0** — gap confirmado en tenant `acces`; contradice BL-1.0 RD-07 (`tenant_data`) y comentario runtime L123 `audit_service.py`. |
| **Clase** | **A** — debe existir en DP |

### 7.2 `log_sincronizacion_usuario` — **Latente**

| Campo | Detalle |
|-------|---------|
| **Módulo** | Superadmin / sync identidad |
| **Servicios** | `AuditService.registrar_log_sincronizacion_usuario`; lectura `SuperadminAuditoriaService` |
| **Endpoints** | Superadmin auditoría sync (listados paginados) |
| **Impacto** | Sin error hoy si no se ejecuta sync cross-installation en Dedicated. Al activar sync → mismo patrón que `auth_audit_log`. |
| **Criticidad** | **P2** (latente) |
| **Clase** | **A** si producto exige sync en Dedicated; **C** si sync queda CP-only permanentemente |

### 7.3 IAM Session trio — **No es gap (MVP)**

| Campo | Detalle |
|-------|---------|
| **Estado** | Ausentes en DP **por ADR-002-A / RD-11 Closed (MVP)** |
| **Impacto futuro** | BL-PEND-04: opción session store en DP requeriría nuevo perfil manifiesto (`dedicated_schema_v3` + `V031` adaptado) |
| **Clase** | **B** — permanece CP |

---

## 8. Casos latentes similares a `auth_audit_log`

Patrón: *runtime enruta a DP (`DEFAULT` + `client_id`); catálogo Dedicated no crea tabla; fail-soft o flujo no ejecutado aún.*

| # | Tabla | ¿Error hoy? | ¿Cuándo fallaría? | Severidad |
|---|-------|:-----------:|-------------------|-----------|
| 1 | `auth_audit_log` | Sí (logs ERROR) | Login, refresh, logout, impersonation, session admin | **P0** |
| 2 | `log_sincronizacion_usuario` | No (flujo raro) | Sync manual/automático usuarios entre instalaciones | P2 |
| 3 | Lectura auditoría Dedicated | Parcial | Superadmin consulta logs en DP inexistente → vacío/404 | P1 |

**No latentes (falsos positivos):**

- Session store IAM — runtime **no** espera tablas en DP.
- `permiso` — DTSP + S6 sync cubren réplica DP; fallback CP en `permisos_negocio_service` sigue funcionando.
- `cliente_auth_config` — gateway CP explícito; no requiere réplica DP.

---

## 9. Verificación especial — componentes solicitados

| Componente | Runtime Dedicated | DDL Dedicated | Veredicto |
|------------|-------------------|---------------|-----------|
| **IAM Session Mgmt V2** | Servicios session en CP (`SESSION_STORE_CONNECTION=ADMIN`) | No provisionado | **OK MVP** |
| **IAM Session Mgmt V3** | Mismas tablas V031 en CP Shared | No en manifiesto | **OK MVP** |
| **Refresh Tokens** | CP | No en DP | **OK MVP** |
| **User Session** | CP | No en DP | **OK MVP** |
| **Token Family** | CP | No en DP | **OK MVP** |
| **Audit (auth)** | DP insert | **No creado** | **GAP P0** |
| **Impersonation** | Operación funcional; audit → DP gap | N/A | Audit roto; flujo OK |
| **Session Store** | CP SQL + Redis bridge | N/A SQL DP | **OK MVP** |
| **Blacklist** | Redis | N/A | OK |
| **Permission Resolver** | DTSP `permiso`/`rol_permiso` en DP + cache | DTSP ✅ | OK |
| **Menu Resolver** | DTSP `modulo*`/`rol_menu_permiso` en DP | DTSP ✅ | OK |

---

## 10. ¿Catálogo DDL Dedicated obsoleto?

### 10.1 Respuesta: **Sí, parcialmente**

| Versión / hito | Qué incluye | Desalineación |
|----------------|-------------|---------------|
| Legacy `TABLAS_BD_DEDICADA.sql` | ERP + identity + **`auth_audit_log` + `refresh_tokens`** | Referencia histórica; **no cableada** a F4 |
| `dedicated_schema_v1` | V010 ERP + `rol_permiso` | Sin DTSP; obsoleto para F11 |
| **`dedicated_schema_v2` (actual)** | V010 + DTSP + `rol_permiso` | Correcto DTSP; **omitió audit tenant** |
| Shared post-V031 | IAM Session v3 en CP | Runtime MVP no exige en DP |
| BL-1.0 RD-07 | `auth_audit_log` = `tenant_data` | **No reflejado en manifiesto v2** |

### 10.2 Desde qué versión quedó desalineado

1. **F4-05b / `dedicated_schema_v2`:** introdujo DTSP (2026) alineando identidad/RBAC con F11, pero **deliberadamente excluyó** tablas CP — incluido audit.
2. **IAM Session V2/V3:** runtime adoptó ADR-002-A (sesiones CP) — ausencia en DP es coherente; no es obsolescencia del catálogo sino decisión MVP.
3. **BL-1.0 freeze (2026-06-25):** cerró `auth_audit_log` como `tenant_data` — **DDL Dedicated no actualizado** → desalineación normativa activa.

### 10.3 Componentes nuevos nunca incorporados al manifiesto Dedicated

| Componente | ¿Debería estar en DP? |
|------------|----------------------|
| `auth_audit_log` DDL | **Sí** (RD-07) |
| `log_sincronizacion_usuario` DDL | Decisión pendiente (A o C) |
| `V031` session tables | **No** en MVP (ADR-002-A) |
| `V033` FK policy | N/A (CP session refs) |

### 10.4 Impacto futuro

- Nuevos flujos IAM que emitan auditoría → más eventos perdidos en DP.
- Compliance / SOC2 tenant-isolated audit → **bloqueante** sin `auth_audit_log` DP.
- Activación sync identidad en Dedicated → segundo gap inmediato.
- Post-MVP session store en DP → requiere **nuevo perfil manifiesto**, no patch ad hoc.

---

## 11. Clasificación A / B / C (tablas Shared ausentes en Dedicated)

| Tabla | Clase | Justificación |
|-------|:-----:|---------------|
| `auth_audit_log` | **A** | RD-07 BL-1.0: `tenant_data`; runtime inserta en DP; fail-soft enmascara el gap |
| `log_sincronizacion_usuario` | **A/C** | Runtime insert DEFAULT; si sync es feature Dedicated → A; si CP-only → C + fix routing |
| `user_session` | **B** | ADR-002-A: session store CP MVP; runtime `SESSION_STORE_CONNECTION=ADMIN` |
| `token_family` | **B** | Idem |
| `refresh_tokens` | **B** | Idem |
| `cliente` | **B** | Tenant registry CP; routing via `cliente_conexion` |
| `cliente_conexion` | **B** | Storage metadata CP |
| `cliente_auth_config` | **B** | ADR-012 SSOT CP |
| `federacion_identidad` | **B** | Platform identity federation |
| `tenant_provisioning_*` | **B** | Saga state CP |
| `modulo_rol_plantilla` | **B** | Catálogo plantillas rol; solo servicios CP ADMIN |
| Resto CP-only en V020 | **B** | No referenciadas con DEFAULT en flujos Dedicated |

**Ninguna tabla ERP de V010 requiere reclasificación** — ya provisionadas.

---

## 12. Riesgos

| ID | Riesgo | Prob. | Impacto |
|----|--------|:-----:|:-------:|
| R-G2-01 | Auditoría auth silenciosamente vacía en Dedicated | Alta | Alto |
| R-G2-02 | Onboarding “READY” con schema incompleto vs runtime | Alta | Medio |
| R-G2-03 | Outliers (`acce`) enmascaran ausencia sistemática | Media | Medio |
| R-G2-04 | Superadmin auditoría inconsistente multi-DB | Media | Alto |
| R-G2-05 | Futuro session-in-DP sin manifiesto versionado | Baja | Alto |
| R-G2-06 | Confusión legacy `TABLAS_BD_DEDICADA.sql` vs v2 | Media | Medio |

---

## 13. Plan de alineamiento (solo diseño — NO implementar)

### Fase 1 — Crítico (P0): Audit tenant en DP

1. Decisión arquitectónica formal: confirmar RD-07 (`auth_audit_log` en DP) vs enmienda routing a CP.
2. Si **A (recomendado por BL-1.0):**
   - Nuevo script `05_dedicated/V0xx__auth_audit_log_dedicated.sql` (paridad columnas V020).
   - Registrar en `DEDICATED_SCHEMA_MANIFEST_V3` (o v2.1 con checksum update autorizado).
   - Extender `_verify_dtsp_schema` o gate dedicado `TENANT_RUNTIME_REQUIRED_TABLES`.
   - Documentar en DTSP profile + `BOOTSTRAP_ORDER` Fase 6.
3. Validar inserts post-provisioning en tenant piloto (`acces`-like).
4. **No tocar** session tables en esta fase.

### Fase 2 — Medio (P1–P2): Integridad gates + gaps secundarios

1. Definir `DEDICATED_RUNTIME_VERIFICATION_TABLES` = DTSP ∪ `{ auth_audit_log, cfg_codigo_secuencia }` mínimo.
2. Decidir `log_sincronizacion_usuario`: Clase A (DDL DP) o C (routing CP + doc).
3. Alinear documentación runtime (`audit_service` comentarios) con decisión BL-1.0.
4. Inventario outliers (`acce`); política: reprovision vs repair utility documentada (sin ejecutar en esta auditoría).
5. Tests contrato provisioning: tenant READY implica tablas runtime P0.

### Fase 3 — Evolución (post-MVP): Session store opcional en DP

1. Reevaluar BL-PEND-04 / ADR-002-A.
2. Si session-in-DP: perfil `dedicated_schema_v3` + adaptación `V031` sin FK cross-plane (patrón V033).
3. Migración tenants existentes orchestrada; **no** mezclar con Fase 1 audit.
4. Permission/menu: mantener réplica DTSP; no duplicar CP registry.

---

## 14. Referencias

| Documento / código | Rol |
|--------------------|-----|
| `F12_G1_DEDICATED_DDL_ROOT_CAUSE.md` | Causa raíz `auth_audit_log` |
| `script_manifest.py` | Manifiesto `dedicated_schema_v2` |
| `bootstrap_script_runner.py` | Verificación DTSP |
| `DTSP_DEDICATED_TENANT_STORE_PROFILE.md` | Perfil normativo DTSP |
| `03_RUNTIME_DECISION_STATUS.md` | RD-07, RD-11 BL-1.0 |
| `session_store_connection.py` | ADR-002-A enforcement |
| `audit_service.py` | Routing audit Dedicated |
| `permission_catalog_store.py` / `menu_catalog_store.py` | F11 DP réplica |

---

## 15. Veredicto final

| Pregunta | Respuesta |
|----------|-----------|
| ¿Catálogo Dedicated soporta runtime ERP + DTSP? | **Sí** |
| ¿Soporta runtime IAM Session MVP? | **Sí** (vía CP — by design) |
| ¿Soporta runtime audit auth? | **No** — gap Clase A confirmado |
| ¿Hay más gaps latentes? | **Sí** — `log_sincronizacion_usuario`; lectura auditoría |
| ¿Conjunto mínimo correcto = copiar Shared? | **No** — mínimo = DTSP + ERP + **`auth_audit_log`** (+ decisión sync) |
| ¿Onboarding engaña sobre completitud? | **Sí** — gate 10 tablas vs runtime ~15 transversales DP |

**Acción recomendada prioritaria:** Fase 1 — alinear DDL Dedicated con RD-07 para `auth_audit_log` **o** enmendar normativa y routing (mutuamente excluyentes). El resto del catálogo v2 es coherente con arquitectura híbrida MVP vigente.
