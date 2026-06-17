# Plan de implementación — `bootstrap_platform.py`

**Tipo:** Diseño técnico definitivo (sin código)  
**Fecha:** 2026-06-05  
**Estado:** Aprobado para implementación  

**Decisiones arquitectónicas confirmadas:**

- Sin cambios en `bootstrap_v2_sql_apply.ps1`, `permission_sync`, startup, onboarding tenant, `ClienteOnboardingService`.
- Canal oficial: CLI `bootstrap_platform.py` dentro de `fastapi_backend`.
- Configuración: mismo mecanismo que `app/core/config.py`; Docker canónico → `.env.docker`.
- Reemplazo funcional: D010 bloques A–E + `repair_platform_rbac.py --apply`.

**Referencias:**

- [`PLATFORM_BOOTSTRAP_AUTOMATION_AUDIT.md`](PLATFORM_BOOTSTRAP_AUTOMATION_AUDIT.md)
- [`PLATFORM_BOOTSTRAP_STRATEGY_DECISION.md`](PLATFORM_BOOTSTRAP_STRATEGY_DECISION.md)
- Flujo validado manualmente por el operador (install limpia + login superadmin).

**Flujo objetivo:**

```text
CREATE DATABASE
→ bootstrap_v2_sql_apply.ps1
→ docker compose up -d
→ docker exec fastapi_backend python scripts/bootstrap_platform.py --apply
→ Login superadmin
```

---

## 1. Servicios actuales a reutilizar exactamente

### 1.1 Reutilización directa (sin modificar contrato público)

| Servicio / utilidad | Método o símbolo | Fase bootstrap |
|---------------------|------------------|----------------|
| `PlatformRbacBootstrapService` | `resolve_platform_cliente_id()` | Resolución UUID plataforma |
| `PlatformRbacBootstrapService` | `bootstrap_platform_rbac(session, …)` | **Fase RBAC completa** (SYS_ADMIN + rol_permiso + reactivar permisos menú) |
| `OnboardingRbacService` | `_validar_catalogo_permiso(session)` | Precondición (ya invocada dentro de `bootstrap_platform_rbac`; no duplicar en orquestador) |
| `OnboardingRbacService` | `activar_modulos_base_cliente(…)` | Indirecto vía `PlatformRbacBootstrapService` |
| `app.core.config.settings` | Instancia global | Toda la configuración |
| `app.core.security.password.get_password_hash` | Hash bcrypt | Creación usuario (solo si no existe) |
| `get_db_connection(DatabaseConnection.ADMIN)` | Sesión async + commit | Misma conexión que repair y onboarding admin |
| Constantes exportadas de `platform_rbac_bootstrap_service` | `ADMIN_PLATFORM_ACCESS`, `CORE_APP_ACCEDER`, `PLATFORM_ADMIN_ROL_CODIGO`, etc. | Audit + tests |

### 1.2 Patrones a copiar (referencia, sin invocar clases de onboarding)

| Origen | Patrón | Uso en identidad plataforma |
|--------|--------|----------------------------|
| `ClienteOnboardingService._insertar_auth_config_si_no_existe` | `IF NOT EXISTS` + `INSERT cliente_auth_config` | Opcional recomendado post-usuario |
| `ClienteOnboardingService._generar_contrasena_segura` | Generación password dev | Solo si `ENVIRONMENT=development` y sin password env |
| `repair_platform_rbac._audit_snapshot` | Snapshot JSON pre/post | Base del módulo audit unificado (extendido) |

### 1.3 Qué NO reutilizar

| Componente | Motivo |
|------------|--------|
| `ClienteOnboardingService.crear_cliente_con_onboarding` | Provisiona tenant ERP completo — prohibido modificar/invocar |
| `OnboardingRbacService.bootstrap_cliente_rbac` | Bundles ADMIN_TENANT / T1/T2/T3 |
| `MinimalErpTenantBootstrapService` | org_empresa — no aplica a plataforma |
| D010 en runtime | Prohibido por decisión arquitectónica |
| `permission_startup` / lifespan | Sin hook automático |

---

## 2. Lógica a extraer de D010 (semántica, no el archivo)

Extraer **solo equivalencia funcional** de bloques A–E validados. **No parsear ni importar** `D010__seed_bd_central.sql`.

### Bloque A — Contexto BD

| D010 | Runtime Python |
|------|----------------|
| `USE bd_hybrid_sistema_central` | **No aplica** — conexión vía `settings.DB_ADMIN_*` / `get_db_connection(ADMIN)` |

### Bloque B — Cliente plataforma (líneas 20–59)

| Campo | Valor runtime | Fuente |
|-------|---------------|--------|
| `cliente_id` | `settings.SUPERADMIN_CLIENTE_ID` | Env obligatorio |
| `codigo_cliente` | `settings.SUPERADMIN_CLIENTE_CODIGO` | Env (default `SYSTEM`; convención actual `SUPERADMIN`) |
| `subdominio` | `settings.SUPERADMIN_SUBDOMINIO` | Env (default `platform`) |
| `razon_social` | Constante o `PLATFORM_BOOTSTRAP_RAZON_SOCIAL` | Env opcional |
| `nombre_comercial` | `"Plataforma Admin"` o derivado | Constante |
| `ruc` | Nullable / constante interna | No crítico login |
| `tipo_instalacion` | `shared` | Constante |
| `modo_autenticacion` | `local` | Constante |
| `color_primario` / `color_secundario` | Defaults D010 o schema default | Constantes simples |
| `tema_personalizado` | **`NULL`** recomendado | Evitar JSON gigante de D010 en código |
| `plan_suscripcion` | `enterprise` | Constante |
| `estado_suscripcion` | `activo` | Constante |
| `contacto_email` | `PLATFORM_BOOTSTRAP_CONTACT_EMAIL` | Env obligatorio si crea cliente |
| `contacto_nombre` / `contacto_telefono` | Nullable | Opcional |
| `es_activo` | `1` | Constante |
| `es_demo` | `0` | Constante — **sin datos demo** |

### Bloque C — Rol ADMIN_PLATFORM (líneas 986–1005)

| Campo | Valor |
|-------|-------|
| `codigo_rol` | `ADMIN_PLATFORM` |
| `nombre` | `Administrador` (alinear D010 validado) |
| `descripcion` | Constante |
| `es_rol_sistema` | `1` |
| `nivel_acceso` | `5` |
| `es_admin_cliente` | `0` (platform ≠ admin ERP tenant) |
| `empresa_id` | `NULL` |
| `rol_id` | **`uuid4()` en creación** — no hardcodear UUID D010 salvo migración legacy documentada |

**Omitir:** roles `SUPPORT_PLATFORM`, `USER_PLATFORM` (líneas 1007–1047).

### Bloque D — Usuario superadmin (líneas 1049–1071)

| Campo | Valor |
|-------|-------|
| `nombre_usuario` | `settings.SUPERADMIN_USERNAME` |
| `contrasena` | `get_password_hash(PLATFORM_BOOTSTRAP_INITIAL_PASSWORD)` **solo en INSERT** |
| `nombre` / `apellido` | `Administrador` / `Sistema` |
| `correo` | `PLATFORM_BOOTSTRAP_CONTACT_EMAIL` o fallback email plataforma |
| `es_activo` | `1` |
| `correo_confirmado` | `1` |
| `requiere_cambio_contrasena` | `1` en prod; `0` opcional dev si se desea paridad exacta D010 |
| `empresa_default_id` | `NULL` |
| `proveedor_autenticacion` | `local` |
| `usuario_id` | **`uuid4()` en creación** |

**Política password:**

| Condición | Acción |
|-----------|--------|
| Usuario ya existe | **No tocar** `contrasena` |
| Usuario no existe + password env | Crear con hash |
| Usuario no existe + sin password + `ENVIRONMENT=development` | Generar aleatoria; log WARNING una vez |
| Usuario no existe + sin password + prod | **Error** `PLATFORM_BOOTSTRAP_PASSWORD_REQUIRED` — no crear usuario |

### Bloque E — usuario_rol (primer registro, líneas 1129–1135)

| Campo | Valor |
|-------|-------|
| `usuario_id` | ID resuelto del superadmin |
| `rol_id` | ID resuelto ADMIN_PLATFORM |
| `cliente_id` | `SUPERADMIN_CLIENTE_ID` |
| `empresa_id` | `NULL` |
| `es_activo` | `1` |

### Equivalente repair (no está en D010 A–E)

Delegado **100 %** a `PlatformRbacBootstrapService.bootstrap_platform_rbac`:

- Reactivar `admin.platform.access`, `admin.tenant.access`
- `cliente_modulo` → SYS_ADMIN
- `rol_permiso` ADMIN_PLATFORM (incluye `tenant.cliente.crear`)

### Extra recomendado (no en D010, no bloqueante login)

| Entidad | Motivo |
|---------|--------|
| `cliente_auth_config` | Paridad con onboarding; auth usa fallback a settings si falta |

---

## 3. Nuevos servicios realmente necesarios

Solo **dos** servicios de aplicación + **un** módulo de auditoría compartido. No crear módulo ERP completo.

### 3.1 `PlatformIdentityBootstrapService` (NUEVO)

**Responsabilidad:** provisión idempotente de identidad plataforma.

Métodos propuestos:

| Método | Descripción |
|--------|-------------|
| `ensure_platform_cliente(session) -> EnsureResult` | INSERT si no existe por `cliente_id`; validar conflictos subdominio/codigo |
| `ensure_admin_platform_rol(session, cliente_id) -> UUID` | Rol ADMIN_PLATFORM |
| `ensure_superadmin_usuario(session, cliente_id, admin_rol_id) -> UUID` | Usuario + usuario_rol |
| `ensure_auth_config(session, cliente_id) -> bool` | IF NOT EXISTS cliente_auth_config |
| `bootstrap_platform_identity(session) -> dict` | Orquesta los cuatro en orden |

**Ubicación recomendada:**  
`app/modules/tenant/application/services/platform_identity_bootstrap_service.py`

*(Misma carpeta que `platform_rbac_bootstrap_service.py` — cohesión SaaS/platform sin nuevo top-level module.)*

### 3.2 `PlatformBootstrapService` (NUEVO — orquestador)

**Responsabilidad:** punto de entrada único CLI/audit.

| Método | Descripción |
|--------|-------------|
| `ensure_platform_ready(session, *, rbac_only=False) -> PlatformBootstrapResult` | Identidad (si no rbac_only) + RBAC |
| `audit_platform_ready(session) -> PlatformBootstrapAudit` | Snapshot completo identidad + RBAC |

**Ubicación:**  
`app/modules/tenant/application/services/platform_bootstrap_service.py`

### 3.3 `platform_bootstrap_audit.py` (NUEVO — utilidad)

**Responsabilidad:** queries de audit compartidas entre CLI y tests.

- Extraer y **extender** lógica de `repair_platform_rbac._audit_snapshot`.
- Añadir checks identidad: cliente, rol, usuario, usuario_rol, `tenant.cliente.crear`.
- Campo agregado: `needs_bootstrap: bool`, `needs_identity: bool`, `needs_rbac: bool`.

**Ubicación:**  
`app/modules/tenant/application/services/platform_bootstrap_audit.py`

### 3.4 Qué NO crear

| Artefacto | Motivo |
|-----------|--------|
| Nuevo módulo `app/modules/platform/` completo | Over-engineering; 3 archivos en `tenant/application/services` bastan |
| Repository dedicado | Patrón del proyecto: SQLAlchemy `text()` en services bootstrap (como repair/onboarding) |
| Duplicar `PlatformRbacBootstrapService` | Ya existe y es idempotente |
| Hook startup | Decisión explícita rechazada |

---

## 4. Archivos nuevos a crear

| # | Archivo | Propósito |
|---|---------|-----------|
| 1 | `app/modules/tenant/application/services/platform_identity_bootstrap_service.py` | Identidad idempotente |
| 2 | `app/modules/tenant/application/services/platform_bootstrap_service.py` | Orquestador |
| 3 | `app/modules/tenant/application/services/platform_bootstrap_audit.py` | Audit snapshot |
| 4 | `app/modules/tenant/application/services/platform_bootstrap_constants.py` | Defaults cliente/rol (desacoplado de D010) |
| 5 | `scripts/bootstrap_platform.py` | CLI oficial |
| 6 | `tests/unit/test_platform_identity_bootstrap.py` | Idempotencia + conflictos (mock session) |
| 7 | `tests/unit/test_platform_bootstrap_audit.py` | needs_bootstrap flags |
| 8 | `tests/unit/test_platform_bootstrap_orchestrator.py` | Orden de fases (mock) |

**Opcional fase 2:** test integración con BD real (staging), smoke en pipeline.

---

## 5. Archivos existentes a modificar

### 5.1 Modificaciones obligarias (mínimas)

| Archivo | Cambio | Justificación |
|---------|--------|---------------|
| `app/core/config.py` | Añadir lectura `PLATFORM_BOOTSTRAP_INITIAL_PASSWORD`, `PLATFORM_BOOTSTRAP_CONTACT_EMAIL`, opcional `PLATFORM_BOOTSTRAP_RAZON_SOCIAL` vía `os.getenv` | Mismo patrón existente; sin cambiar mecanismo load |
| `.env.docker` | Documentar nuevas keys (valores vacíos o placeholder) | Canónico Docker |
| `.env.example` | Mismas keys + comentarios | Plantilla bare-metal |

### 5.2 Modificaciones recomendadas (deuda cero)

| Archivo | Cambio |
|---------|--------|
| `platform_rbac_bootstrap_service.py` | Actualizar mensaje error `PLATFORM_ADMIN_ROLE_NOT_FOUND`: referir `bootstrap_platform.py`, no D010 |
| `scripts/repair_platform_rbac.py` | Deprecación fase 1: docstring + delegación a orquestador (ver §9) |
| `app/docs/PLATFORM_FIRST_BOOT.md` | Marcar obsoleto / redirigir |
| `app/docs/DEPLOYMENT_FIRST_INSTALL_GUIDE.md` | Fase plataforma → `bootstrap_platform.py` |
| `app/bootstrap_v2/00_manifest/PLATFORM_RBAC_GAP_FIX.md` | Nota: repair superseded |

### 5.3 Sin modificar (confirmado)

| Archivo |
|---------|
| `scripts/bootstrap_v2_sql_apply.ps1` |
| `app/core/authorization/permission_startup.py` |
| `app/main.py` (lifespan) |
| `ClienteOnboardingService` |
| `OnboardingRbacService` (excepto uso existente sin cambios) |
| `D010__seed_bd_central.sql` |
| Cualquier script SQL bootstrap_v2 |

---

## 6. Idempotencia total — diseño

### 6.1 Principio

> **Lookup por claves naturales → INSERT condicional → nunca UPDATE destructivo en re-ejecución.**

### 6.2 Por entidad

| Entidad | Lookup | Insert | Re-ejecución |
|---------|--------|--------|--------------|
| `cliente` | `cliente_id = SUPERADMIN_CLIENTE_ID` | Si no existe | No-op |
| Conflicto cliente | Mismo `subdominio`/`codigo_cliente` con **otro** UUID | — | **FAIL** `PLATFORM_CLIENTE_CONFLICT` |
| `rol` | `cliente_id` + `codigo_rol = ADMIN_PLATFORM` | Si no existe | No-op |
| `usuario` | `cliente_id` + `nombre_usuario = SUPERADMIN_USERNAME` | Si no existe | No-op; **password intacta** |
| `usuario_rol` | `usuario_id` + `rol_id` + `empresa_id IS NULL` | Si no existe | No-op |
| `cliente_auth_config` | `cliente_id` | IF NOT EXISTS | No-op |
| `cliente_modulo` | vía `activar_modulos_base_cliente` | INSERT WHERE NOT EXISTS | No-op |
| `rol_permiso` | vía `asignar_permisos_admin_platform` | INSERT SELECT NOT EXISTS | Solo inserts faltantes |

### 6.3 Transacción

```text
async with get_db_connection(ADMIN) as session:
    async with session.begin():          # una transacción
        identity_result = ...
        rbac_result = await PlatformRbacBootstrapService.bootstrap_platform_rbac(
            session, activado_por_usuario_id=usuario_id
        )
    # commit automático al salir de begin()
```

Si falla identidad → rollback RBAC. Si falla RBAC → rollback identidad (install atómico).

### 6.4 Modos CLI

| Flag | Comportamiento |
|------|----------------|
| `--audit-only` | Solo audit JSON; exit 0 si ready, 1 si needs_bootstrap |
| `--dry-run` | Audit before; simula apply sin commit |
| `--apply` | Ejecuta orquestador + commit |
| `--rbac-only` | Solo fase RBAC (compat repair / recovery parcial) |
| `--json-out PATH` | Artefacto evidencia (patrón smoke scripts) |

### 6.5 Criterio `needs_bootstrap`

```text
needs_identity = cliente missing OR rol missing OR usuario missing OR usuario_rol missing
needs_rbac     = cm_sysadmin=0 OR rp_count<5 OR !tenant.cliente.crear OR !admin.platform.access activo
needs_bootstrap = needs_identity OR needs_rbac
```

---

## 7. Evitar duplicar lógica existente

| Regla | Implementación |
|-------|----------------|
| RBAC plataforma | **Una sola implementación:** `PlatformRbacBootstrapService` — orquestador solo llama |
| Validación catálogo permisos | Delegada a RBAC service — no repetir en identity |
| Hash password | `get_password_hash` — no reimplementar bcrypt |
| Conexión BD | `get_db_connection(ADMIN)` — no connection string manual |
| Config | `from app.core.config import settings` — no `load_dotenv` adicional en script |
| Audit RBAC | Mover a `platform_bootstrap_audit.py` — repair y bootstrap importan el mismo módulo |
| Auth config SQL | Un método en identity service — **no** modificar `ClienteOnboardingService` para extraer |

**Anti-patrón prohibido:** copiar el SQL de grants `rol_permiso` fuera de `PlatformRbacBootstrapService`.

---

## 8. Desacoplamiento de D010 futuro

| Medida | Detalle |
|--------|---------|
| **Fuente de verdad** | Constantes Python en `platform_bootstrap_constants.py` + variables `settings` |
| **Cero runtime SQL file** | No leer `D010__seed_bd_central.sql` |
| **D010 permanece QA** | Demo tenants; no referencia en código productivo |
| **Documentación** | `D010` comentario cabecera: "Para plataforma prod usar bootstrap_platform.py" |
| **Tests** | Assert comportamiento contra constants module, no contra contenido D010 |
| **UUIDs** | No hardcodear UUIDs D010 (`000…001`, `000…010`) excepto `cliente_id` desde env — rol/usuario por lookup |
| **Cambios D010** | No afectan prod; solo QA manual si alguien ejecuta D010 completo |

Si D010 cambia passwords demo o añade tenants, **cero impacto** en bootstrap_platform.

---

## 9. Deprecación gradual de `repair_platform_rbac.py`

### Fase 1 — Coexistencia (release N)

| Acción |
|--------|
| Implementar `bootstrap_platform.py` como superset |
| `repair_platform_rbac.py`: docstring `@deprecated Use bootstrap_platform.py` |
| Repair delega: `--apply` → `PlatformBootstrapService.ensure_platform_ready(rbac_only=True)` |
| Audit repair importa `platform_bootstrap_audit` |

### Fase 2 — Redirect (release N+1)

| Acción |
|--------|
| Repair imprime stderr warning al ejecutar |
| Docs solo mencionan `bootstrap_platform.py` |
| Smoke/pipeline usan bootstrap |

### Fase 3 — Eliminación (release N+2)

| Acción |
|--------|
| Eliminar `repair_platform_rbac.py` o dejar stub 5 líneas que exit 1 con mensaje |
| grep repo confirma cero referencias |

**Compatibilidad inmediata:** `bootstrap_platform.py --rbac-only` ≡ `repair_platform_rbac.py --apply` en entornos con identidad ya existente.

---

## 10. Riesgos técnicos de implementación

| # | Riesgo | Severidad | Mitigación |
|---|--------|-----------|------------|
| R1 | Script ejecutado **fuera** del contenedor con `.env` distinto a `.env.docker` | **Alta** | Doc + guard opcional: comparar `DB_DATABASE` log vs warning si `host.docker.internal` expected |
| R2 | `import settings` falla sin `SECRET_KEY` válida | Media | Ya afecta a repair; aceptado — mismo prerequisito que FastAPI |
| R3 | Bootstrap antes de permission_sync (`permiso` vacío) | **Alta** | Error claro `ONBOARDING_PERMISSO_CATALOG_EMPTY` reutilizado; doc paso 3 requiere `/health` OK |
| R4 | `SUPERADMIN_CLIENTE_ID` no coincide con BD legacy | Media | Conflict check subdominio/codigo; fail fast |
| R5 | Password no provista en prod | **Alta** | Validación pre-insert; exit code 2 |
| R6 | Log accidental de password | **Alta** | Nunca loggear env password; dev generated password solo WARNING sin valor en prod |
| R7 | Unique constraint race (doble `--apply` paralelo) | Baja | Transacción + catch IntegrityError → re-fetch idempotente |
| R8 | `PlatformRbacBootstrapService` sigue exigiendo rol preexistente | Media | Orquestador garantiza orden identity → rbac; test integración |
| R9 | Contenedor sin `--force-recreate` tras cambio `.env.docker` | Media | Documentar en runbook |
| R10 | `tema_personalizado` NULL vs D010 JSON | Baja | Login no depende; branding opcional post-install |
| R11 | Mensaje error repair referencia D010 | Baja | Fix en fase implementación |
| R12 | Dependencia import circular | Baja | Identity no importa RBAC; orquestador importa ambos |

---

## 11. Diseño CLI `bootstrap_platform.py`

### 11.1 Estructura (espejo de repair, ampliado)

```text
scripts/bootstrap_platform.py
├── argparse (--audit-only | --dry-run | --apply | --rbac-only)
├── --json-out optional
├── PROJECT_ROOT en sys.path
├── from app.core.config import settings          # dispara load_dotenv + validación
├── asyncio.run(main())
└── delega en PlatformBootstrapService
```

### 11.2 Comando oficial producción Docker

```powershell
docker exec -w /app -e PYTHONPATH=/app fastapi_backend `
  python scripts/bootstrap_platform.py --audit-only

docker exec -w /app -e PYTHONPATH=/app `
  -e PLATFORM_BOOTSTRAP_INITIAL_PASSWORD='<segura>' `
  fastapi_backend python scripts/bootstrap_platform.py --apply
```

Variables persistentes en `.env.docker`:

```env
PLATFORM_BOOTSTRAP_CONTACT_EMAIL=admin@platform.com
# PLATFORM_BOOTSTRAP_INITIAL_PASSWORD=   # preferir -e one-shot en prod
```

### 11.3 Salida JSON esperada (`--apply`)

```json
{
  "dry_run": false,
  "before": { "needs_bootstrap": true, "needs_identity": true, "needs_rbac": true },
  "after": { "needs_bootstrap": false },
  "identity": { "cliente_created": true, "usuario_created": true, ... },
  "rbac": { "grants": { "inserted": 22, "has_tenant_cliente_crear": true } },
  "credentials": { "username": "superadmin", "password_generated": false }
}
```

**Nunca** incluir password en JSON salvo flag explícito dev `--expose-generated-password` (opcional, default off).

---

## 12. Alineación con estándares del proyecto

| Estándar V4 / convención | Cumplimiento |
|--------------------------|:------------:|
| Services en `application/services/` | ✅ |
| SQL vía `text()` + `AsyncSession` en bootstrap ops | ✅ (como repair/onboarding) |
| `DatabaseConnection.ADMIN` para SaaS central | ✅ |
| Excepciones `DatabaseError` con `internal_code` | ✅ |
| Scripts en `scripts/` con `PROJECT_ROOT` path hack | ✅ (patrón repair) |
| Config centralizada `settings` | ✅ |
| Sin modificar onboarding tenant | ✅ |
| Tests unitarios en `tests/unit/` | ✅ |
| Idempotencia INSERT NOT EXISTS | ✅ (patrón onboarding RBAC) |

**Deuda evitada:**

- No hook startup.
- No parse D010.
- No duplicar grants RBAC.
- No nuevo módulo ERP de 4 capas para 3 archivos de servicio.

---

## 13. Orden de implementación recomendado

| Paso | Entregable | Verificación |
|------|------------|--------------|
| 1 | `platform_bootstrap_constants.py` | — |
| 2 | `platform_identity_bootstrap_service.py` + tests unit | mocks |
| 3 | `platform_bootstrap_audit.py` + tests | flags needs_* |
| 4 | `platform_bootstrap_service.py` (orquestador) + tests | mock RBAC |
| 5 | `config.py` + `.env.docker` / `.env.example` | import settings |
| 6 | `scripts/bootstrap_platform.py` | install limpia manual |
| 7 | Ajuste mensaje `platform_rbac_bootstrap_service` | — |
| 8 | Deprecación `repair_platform_rbac.py` fase 1 | `--rbac-only` parity |
| 9 | Actualizar docs install | — |
| 10 | `http_smoke_platform_rbac.py` post-bootstrap | PASS |

---

## 14. Veredicto final

| Pregunta | Respuesta |
|----------|-----------|
| ¿Diseño viable sin deuda técnica? | **Sí** |
| ¿Reutiliza lo existente? | **Sí** — RBAC service intacto |
| ¿Elimina D010 A–E + repair? | **Sí** — un CLI |
| ¿Respeta todas las restricciones? | **Sí** |
| ¿Listo para codificar? | **Sí**, siguiendo §13 |

**Arquitectura definitiva:** dos servicios nuevos (identity + orchestrator), un módulo audit, un script CLI, cambios mínimos en config/env — **sin tocar** startup, SQL bootstrap, ni onboarding tenant.

---

*Plan de implementación. Sin código. Sin commits.*
