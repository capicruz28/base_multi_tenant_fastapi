# Auditoría de compatibilidad UUID — bootstrap plataforma

**Tipo:** Auditoría de repositorio (sin código)  
**Fecha:** 2026-06-05  
**Pregunta:** ¿Es seguro usar `uuid4()` para `rol_id` y `usuario_id` en `bootstrap_platform.py`, manteniendo `cliente_id = SUPERADMIN_CLIENTE_ID`?

**UUIDs históricos D010 (flujo manual validado):**

| Entidad | UUID D010 |
|---------|-----------|
| Cliente plataforma | `00000000-0000-0000-0000-000000000001` |
| Rol `ADMIN_PLATFORM` | `00000000-0000-0000-0000-000000000010` |
| Usuario `superadmin` | `00000000-0000-0000-0000-000000000100` |

**Alcance de búsqueda:** código Python (`app/`, `scripts/`, `tests/`), SQL bootstrap/QA, documentación, evidencias JSON, `.env*`.

---

## 1. Resumen ejecutivo

| UUID | ¿Dependencia runtime real? | ¿Bloquea `uuid4()` en bootstrap? |
|------|:--------------------------:|:--------------------------------:|
| Cliente `…0001` | **Sí** — vía `SUPERADMIN_CLIENTE_ID` (env) | **No** — bootstrap debe usar env, no `uuid4()` |
| Rol `…0010` | **No** | **No** |
| Usuario `…0100` | **No** | **No** |

**Veredicto:** **Aprobado** implementar `bootstrap_platform.py` con:

- `cliente_id` = `settings.SUPERADMIN_CLIENTE_ID` (obligatorio, típicamente `…0001`)
- `rol_id` = `uuid4()` en primera creación, resolución por `codigo_rol + cliente_id`
- `usuario_id` = `uuid4()` en primera creación, resolución por `nombre_usuario + cliente_id`

No existe en el repositorio ninguna dependencia de aplicación que exija los UUID fijos `…0010` o `…0100`.

---

## 2. Referencias directas a UUIDs históricos

### 2.1 Cliente `00000000-0000-0000-0000-000000000001`

#### Código Python con impacto runtime

| Archivo | Uso | Tipo dependencia |
|---------|-----|------------------|
| `app/core/config.py` | `SUPERADMIN_CLIENTE_ID` desde env | **Configuración** — fuente canónica |
| `app/core/tenant/middleware.py` | Fallback dev si env vacío | **Degradación dev** — mismo UUID por convención |
| `app/modules/superadmin/application/services/audit_service.py` | Fallback si contexto tenant nulo | **Fallback operativo** |
| `app/modules/tenant/application/services/legacy_tenant_rbac_repair_service.py` | Excluir cliente plataforma del repair batch | **Convención + env** — añade `…0001` fijo además de env |
| `app/modules/tenant/application/services/platform_rbac_bootstrap_service.py` | `resolve_platform_cliente_id()` | **Solo env** |

#### Tests

| Archivo | Uso |
|---------|-----|
| `tests/unit/test_impersonation_auth.py` | `system_cid` en escenarios impersonación |
| `tests/unit/test_unit_of_work.py` | `test_client_id` genérico |
| `tests/unit/test_cliente_eliminar_execute_update_await.py` | `system_id` — protección delete SYSTEM |
| `tests/unit/test_legacy_modulos_router_removed.py` | URLs de rutas con cliente ejemplo |
| `tests/unit/test_platform_me_lookup.py` | `SYSTEM_ID = UUID(settings.SUPERADMIN_CLIENTE_ID)` — **lee env, no hardcode** |

#### Scripts

| Archivo | Uso |
|---------|-----|
| `scripts/_run_delete_cliente_fix_qa.py` | Default env `SUPERADMIN_CLIENTE_ID` |

#### SQL / QA / documentación

- `D010__seed_bd_central.sql`, `2.- SEED_BD_CENTRAL.sql`, `D030`, `SEED_CLIENTE_MODULO_ACTIVAR_ORG.sql`
- Evidencias JSON (`RC_RUN_REPORT`, `MENU_GRANTS_REPAIR_*`, `SUPERADMIN_AUDITORIA_*`)
- Docs: `PLATFORM_FIRST_BOOT.md`, `DEPLOYMENT_FIRST_INSTALL_GUIDE.md`, `BOOTSTRAP_SYSTEM_AUDIT.md`, etc.
- `.env.docker` — valor configurado

**Conclusión cliente `…0001`:** Es la **convención estándar** alineada con `SUPERADMIN_CLIENTE_ID`. El runtime **no hardcodea** el UUID salvo fallbacks dev/repair. Bootstrap debe continuar usando **env**, no generar otro `cliente_id`.

---

### 2.2 Rol `00000000-0000-0000-0000-000000000010`

#### Código Python (`app/`, `scripts/`)

**Cero referencias.**

#### Tests Python

**Cero referencias.**

#### Resolución runtime de rol plataforma

Todo el código productivo resuelve por **clave lógica**, no por `rol_id` fijo:

| Componente | Mecanismo |
|------------|-----------|
| `PlatformRbacBootstrapService._resolve_admin_platform_rol_id` | `WHERE codigo_rol = 'ADMIN_PLATFORM' AND cliente_id = :cid` |
| `repair_platform_rbac._audit_snapshot` | Idem |
| `platform_user_lookup.resolve_platform_superadmin_flag` | `codigo_rol IN ('SUPER_ADMIN', 'ADMIN_PLATFORM')` + `nivel_acceso >= 5` |
| `user_builder.py` | `codigo_rol == 'ADMIN_PLATFORM'` |
| `auth/endpoints.py` | `'ADMIN_PLATFORM' in codigos_rol` |

#### Únicas apariciones

| Ubicación | Naturaleza |
|-----------|------------|
| `D010__seed_bd_central.sql` (INSERT rol + usuario_rol + sección 7 grants) | QA seed |
| `2.- SEED_BD_CENTRAL.sql` (legacy) | Legacy seed |
| `D010_bd_sistema_saas.tmp.sql` | Copia evidencia staging |
| `PLATFORM_FIRST_BOOT.md` | Documentación operativa manual |

**Conclusión rol `…0010`:** **Sin dependencia runtime.** Seguro usar `uuid4()` con idempotencia por `codigo_rol`.

---

### 2.3 Usuario `00000000-0000-0000-0000-000000000100`

#### Código Python (`app/`, `scripts/`)

**Cero referencias** en código de aplicación y scripts.

#### Tests Python

| Archivo | Uso | ¿Dependencia funcional? |
|---------|-----|:-----------------------:|
| `tests/unit/test_platform_me_lookup.py` | Valor en dict mock `full_row` / `partial` | **No** — prueba completitud de columnas `/me`, no lookup por `usuario_id` |

El test usa `SYSTEM_ID` desde `settings.SUPERADMIN_CLIENTE_ID` para `cliente_id`. El `usuario_id` en el mock es **dato de relleno**; cambiar a cualquier UUID válido no altera la lógica bajo prueba.

#### Resolución runtime de usuario plataforma

| Componente | Mecanismo |
|------------|-----------|
| Login / auth | `nombre_usuario` + `cliente_id` |
| `platform_user_lookup.fetch_platform_usuario_row` | `WHERE nombre_usuario = :username AND cliente_id = :cid` |
| `resolve_platform_superadmin_flag` | Bypass por `username == settings.SUPERADMIN_USERNAME` |
| `impersonation_service._resolver_operador_superadmin` | `settings.SUPERADMIN_USERNAME` |

#### Únicas apariciones adicionales

| Ubicación | Naturaleza |
|-----------|------------|
| `D010__seed_bd_central.sql` | QA seed |
| `2.- SEED_BD_CENTRAL.sql` | Legacy |
| `D010_bd_sistema_saas.tmp.sql` | Evidencia |
| `SUPERADMIN_AUDITORIA_ESTADISTICAS_500_FIX_VALIDATION.json` | **Snapshot** de entorno post-D010 (no contrato API) |
| `PLATFORM_FIRST_BOOT.md` | Documentación |

**Conclusión usuario `…0100`:** **Sin dependencia runtime.** Seguro usar `uuid4()` con idempotencia por `nombre_usuario + cliente_id`.

---

## 3. Tests, scripts, smoke y validaciones

### 3.1 Tests unitarios / integración

| Test / área | UUID hardcodeado | Impacto si bootstrap usa uuid4 |
|-------------|------------------|-------------------------------|
| `test_platform_me_lookup.py` | `…0100` en mock | **Ninguno** — no assert sobre ID específico |
| `test_impersonation_auth.py` | `…0001` cliente | **Ninguno** — usa cliente SYSTEM, no rol/usuario ID |
| `test_platform_rbac_bootstrap.py` | Ninguno | **Ninguno** |
| Resto tests con `…0001` | Cliente genérico | **Ninguno** para rol/usuario |

### 3.2 Scripts operativos

| Script | Dependencia UUID |
|--------|------------------|
| `repair_platform_rbac.py` | Solo `codigo_rol` + `SUPERADMIN_CLIENTE_ID` |
| `http_smoke_platform_rbac.py` | Login por `superadmin` + password — **sin usuario_id** |
| `run_*_integration.py` | Credenciales username/password |
| `_run_delete_cliente_fix_qa.py` | `SUPERADMIN_CLIENTE_ID` default `…0001` |

**Ningún script smoke o repair depende de `rol_id …0010` ni `usuario_id …0100`.**

### 3.3 Validaciones / evidencias JSON

Archivos en `app/bootstrap_v2/00_manifest/evidence/` contienen UUIDs capturados de ejecuciones con D010. Son **artefactos históricos**, no fixtures consumidos por tests automatizados ni por runtime.

---

## 4. SQL, documentación y fixtures

### 4.1 SQL con UUIDs fijos

| Archivo | UUIDs | Rol |
|---------|-------|-----|
| `D010__seed_bd_central.sql` | `…0001`, `…0010`, `…0100`, `…0020`, `…0030`, … | QA demo — **no runtime** |
| `2.- SEED_BD_CENTRAL.sql` | Idem | Legacy |
| `D030__cliente_modulo_activar_org.sql` | `…0001` cliente | QA módulo ORG demo |
| `SEED_CLIENTE_MODULO_ACTIVAR_ORG.sql` | `…0001` | Legacy |

`bootstrap_platform.py` **no ejecutará** estos scripts. Cambios futuros en D010 **no afectan** bootstrap Python.

### 4.2 Documentación

Referencias en `PLATFORM_FIRST_BOOT.md`, `DEPLOYMENT_FIRST_INSTALL_GUIDE.md`, `BOOTSTRAP_PLATFORM_IMPLEMENTATION_PLAN.md` documentan el flujo manual histórico. Deben actualizarse post-implementación para indicar que rol/usuario ID son **asignados en runtime** (no fijos).

### 4.3 Fixtures

No existen fixtures pytest (`conftest.py`, factories) que fijen `rol_id …0010` o `usuario_id …0100`.

---

## 5. ¿Es seguro migrar `rol_id` y `usuario_id` a `uuid4()`?

### 5.1 Instalación nueva (caso objetivo)

| Criterio | Evaluación |
|----------|------------|
| Login superadmin | ✅ Por `SUPERADMIN_USERNAME` + password |
| JWT / `/auth/me` | ✅ Por username + `cliente_id` env |
| RBAC grants | ✅ Por `codigo_rol` + `permiso_id` |
| Menú plataforma | ✅ Por `is_super_admin` + `cliente_modulo` |
| Onboarding `POST /clientes/` | ✅ Por permiso `tenant.cliente.crear` en `rol_permiso` |
| Impersonación | ✅ Por `SUPERADMIN_USERNAME` lookup |

**Seguro al 100 %** para install limpia con bootstrap_platform.

### 5.2 Entorno ya provisionado con D010 manual

| Escenario | Comportamiento bootstrap idempotente |
|-----------|--------------------------------------|
| Cliente `…0001` ya existe | Skip INSERT cliente |
| Rol `ADMIN_PLATFORM` ya existe (cualquier `rol_id`) | Skip INSERT rol — lookup por `codigo_rol` |
| Usuario `superadmin` ya existe (cualquier `usuario_id`) | Skip INSERT — **password intacta** |
| usuario_rol ya existe | Skip |
| RBAC ya aplicado | Inserts solo faltantes vía `PlatformRbacBootstrapService` |

**No hay migración destructiva.** Bootstrap con `uuid4()` solo aplica en BD **vacía** de identidad plataforma.

### 5.3 Entorno con `SUPERADMIN_CLIENTE_ID` distinto de `…0001`

| Componente | Comportamiento |
|------------|----------------|
| Bootstrap | Crea cliente con UUID del env |
| `legacy_tenant_rbac_repair` | Sigue excluyendo `…0001` fijo **y** env |
| Middleware / platform services | Usan env |

Rol/usuario con `uuid4()` funcionan igual — sin acoplamiento a `…0010`/`…0100`.

---

## 6. ¿Conviene mantener UUIDs determinísticos (D010)?

### Opción A — `uuid4()` en creación (plan actual)

| Pros | Contras |
|------|---------|
| Desacople total de D010 | IDs distintos vs install manual D010 |
| Idempotencia natural por claves lógicas | Docs/evidencias históricas muestran otros IDs |
| Menos constantes mágicas | Comparación manual SQL dumps menos trivial |

### Opción B — UUIDs fijos D010 en `platform_bootstrap_constants.py`

| Pros | Contras |
|------|---------|
| Paridad byte-a-byte con flujo manual validado | Acoplamiento semántico a QA seed |
| Dumps SQL comparables con D010 | Si `SUPERADMIN_CLIENTE_ID` ≠ `…0001`, rol/usuario fijos quedan incoherentes |
| Tests mock podrían alinear | Falsa sensación de que D010 es contrato prod |

### Opción C — UUID5 determinístico desde `cliente_id` + namespace

| Pros | Contras |
|------|---------|
| Reproducible por entorno sin copiar D010 | Complejidad innecesaria |
| Independiente de cambios D010 | Distinto de UUIDs históricos validados |

### Evaluación

| Opción | Recomendación |
|--------|---------------|
| A — `uuid4()` | **Recomendada** — sin dependencia runtime demostrada |
| B — UUIDs D010 fijos | **Opcional** — solo conveniencia operativa, no requisito |
| C — UUID5 | **No recomendada** — over-engineering |

---

## 7. Recomendación final

### Decisión aprobada para implementación

```text
cliente_id  → settings.SUPERADMIN_CLIENTE_ID     (env; típicamente …0001)
rol_id      → uuid4() si no existe                  (lookup: codigo_rol + cliente_id)
usuario_id  → uuid4() si no existe                  (lookup: nombre_usuario + cliente_id)
```

### Justificación

1. **Auditoría completa:** cero referencias en código Python de aplicación a `…0010` o `…0100`.
2. **Runtime resuelve por claves lógicas** (`ADMIN_PLATFORM`, `superadmin`, `SUPERADMIN_CLIENTE_ID`) — patrón ya usado por `PlatformRbacBootstrapService` y auth.
3. **Tests y smoke no bloquean** — única aparición `…0100` es mock cosmético.
4. **Idempotencia** protege entornos ya provisionados con D010 (no recrea ni cambia IDs existentes).
5. **Desacople de D010** cumple restricción arquitectónica: cambios futuros en QA seed no impactan prod bootstrap.

### Acciones post-implementación (documentación, no código bloqueante)

| Acción | Prioridad |
|--------|-----------|
| Actualizar `PLATFORM_FIRST_BOOT.md` — rol/usuario ID ya no fijos | Media |
| Nota en `D010` cabecera: identidad prod vía `bootstrap_platform.py` | Baja |
| Opcional: usar `uuid4()` también en mock `test_platform_me_lookup` | Baja |

### No requerido

- Mantener UUIDs D010 `…0010` / `…0100` en bootstrap por compatibilidad runtime — **no hay dependencia**.
- Migración de datos en BD existente — bootstrap idempotente no altera filas existentes.

---

## 8. Matriz de veredicto

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 1 | ¿Referencias directas a UUIDs D010? | Cliente `…0001`: sí (env/fallback/docs). Rol `…0010` y usuario `…0100`: **solo SQL/docs/evidencia** |
| 2 | ¿Tests/scripts/smoke dependen de ellos? | **No** para rol/usuario. Cliente vía env `SUPERADMIN_CLIENTE_ID` |
| 3 | ¿SQL/docs/fixtures? | Sí en D010/legacy/docs — **no consumidos por bootstrap Python** |
| 4 | ¿Seguro `uuid4()` rol/usuario? | **Sí** |
| 5 | ¿Conviene UUIDs determinísticos D010? | **Opcional**, no necesario |
| 6 | Recomendación final | **`uuid4()` + lookup idempotente** — **implementación aprobada** |

---

*Auditoría de compatibilidad UUID. Sin código. Sin commits.*
