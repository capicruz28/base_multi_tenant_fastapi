# 01 — Backend AS-IS: Arquitectura General

**Tipo:** Auditoría técnica (estado actual)  
**Fecha:** 2026-06-25  
**Alcance:** Backend FastAPI multi-tenant / multiempresa — preparación para Dedicated Database  
**Restricción:** Documentación descriptiva. Sin propuestas de implementación.

---

## 1. Resumen

El backend CAXIS ERP es una aplicación **FastAPI async** sobre **SQL Server**, con aislamiento de datos por `cliente_id` en una **base de datos compartida** (modelo single-DB activo). La arquitectura combina:

- **Capa de presentación** por módulo (`presentation/`)
- **Servicios de aplicación** (`application/services/`)
- **Infraestructura centralizada** (`app/infrastructure/database/queries/`)
- **Core transversal** (`app/core/`) — tenant, auth, RBAC, excepciones, UoW

Existen **dos familias de módulos**:

| Familia | Módulos | Patrón de datos |
|---------|---------|-----------------|
| **ERP operativo (V4)** | ORG, INV, PUR, SLS, WMS, MFG, … | Query functions + `execute_query`; sin Repository |
| **Platform / IAM** | auth, users, rbac, tenant, superadmin, modulos, menus | Repository legacy + domain en algunos casos |

---

## 2. Estructura del proyecto

```
base_multi_tenant_fastapi/
├── app/
│   ├── api/                    # deps globales + agregador v1
│   │   ├── deps.py             # JWT, usuario activo, RBAC
│   │   ├── deps_auth.py        # contrato de sesión ERP
│   │   └── v1/api.py           # registro central de routers
│   ├── bootstrap_v2/           # DDL y seeds versionados (Flyway-style)
│   ├── core/                   # config, tenant, auth, security, UoW, exceptions
│   ├── docs/                   # documentación canónica backend
│   ├── infrastructure/       # database, redis, cache (compartido)
│   ├── modules/                # 35 módulos de negocio
│   └── shared/                 # paginación ERP, validators, value objects
├── tests/                      # unit, integration, security, smoke
├── scripts/                    # bootstrap, repair, staging
└── docs/                       # specs arquitectura, contratos FE
```

### 2.1 Punto de entrada

| Archivo | Responsabilidad |
|---------|-----------------|
| `app/main.py` | Factory FastAPI, middleware, lifespan, `/health` |
| `app/api/v1/api.py` | `include_router` de ~40 grupos bajo `/api/v1` |
| `app/core/config.py` | Settings (`pydantic-settings`) |

Prefijo API: `settings.API_V1_STR` = `/api/v1`.

### 2.2 Middleware (orden relevante)

1. **CORS**
2. **TenantMiddleware** (`app/core/tenant/middleware.py`) — resuelve tenant desde Host/subdominio
3. **Rate limiting** (condicional, `slowapi`)
4. Handlers de excepciones globales

---

## 3. Módulos (`app/modules/`)

| Código | Módulo | Dominio |
|--------|--------|---------|
| — | auth | Login, JWT, refresh, sesiones IAM V2, SSO, impersonación |
| — | users | CRUD usuarios, admin password reset |
| — | rbac | Roles, permisos, asignaciones |
| — | tenant | Clientes, conexiones BD, onboarding |
| — | superadmin | Usuarios plataforma, auditoría, catálogos globales |
| — | modulos | Catálogo módulos v2, activación por cliente |
| — | menus | Menú legacy (`area_menu`, `menu`) |
| — | catalogos | Catálogos read-only para tenants |
| ORG | org | Empresa, sucursales, departamentos, centros de costo |
| INV | inv | Productos, stock, movimientos, inventario físico |
| PUR | pur | Compras (solicitudes, OC, recepciones) |
| SLS | sls | Ventas (clientes, cotizaciones, pedidos) |
| WMS | wms | Almacenes, ubicaciones, tareas |
| MFG | mfg | BOM, órdenes de producción |
| MRP | mrp | Planificación de materiales |
| MPS | mps | Plan maestro de producción |
| FIN | fin | Contabilidad |
| HCM | hcm | RRHH, planillas, asistencia |
| CRM | crm | Leads, oportunidades |
| LOG | log | Transporte, despachos |
| POS | pos | Punto de venta |
| PRC | prc | Listas de precio, promociones |
| QMS | qms | Calidad, inspecciones |
| INV_BILL | invbill | Facturación electrónica |
| CST | cst | Costeo |
| TAX | tax | Libros electrónicos |
| MNT | mnt | Mantenimiento de activos |
| PM | pm | Proyectos |
| SVC | svc | Órdenes de servicio |
| TKT | tkt | Help desk |
| DMS | dms | Documentos |
| WFL | wfl | Workflow |
| BI | bi | Reportes |
| BDG | bdg | Presupuestos |
| AUD | aud | Auditoría ERP |

---

## 4. Capas y patrón arquitectónico

### 4.1 Patrón ERP V4 (referencia: ORG + INV)

```
HTTP Request
  → presentation/endpoints_*.py
      → Depends(require_erp_session)           [router o endpoint]
      → Depends(get_{cod}_session_client_id)   [solo ORG, INV, RBAC hoy]
      → application/services/*_service.py
          → infrastructure/database/queries/{cod}/*_queries.py
              → queries_async.execute_query / execute_insert / execute_update
                  → get_connection_for_tenant() → AsyncSession
```

**Prohibido en ERP (norma V4):** `domain/` por módulo, `infrastructure/` por módulo, Repository pattern.

### 4.2 Patrón Platform / IAM (legacy + evolución)

```
presentation/endpoints.py
  → application/services/*_service.py
      → infrastructure/repositories/*_repository.py  (auth, users, rbac)
      → queries/auth/*  (sesiones V2, refresh tokens)
      → execute_query(connection_type=ADMIN)
```

Algunos módulos platform mantienen capa `domain/` (auth, users, rbac, tenant).

### 4.3 Infraestructura compartida

| Componente | Ubicación |
|------------|-----------|
| Conexión async | `app/infrastructure/database/connection_async.py` |
| Router tenant | `app/core/tenant/routing.py` |
| Ejecución queries | `app/infrastructure/database/queries_async.py` |
| Filtro tenant | `app/infrastructure/database/query_helpers.py` |
| Tablas SQLAlchemy Core (central) | `app/infrastructure/database/tables.py`, `tables_modulos.py` |
| Queries por módulo | `app/infrastructure/database/queries/{cod}/` (~154 archivos) |
| Redis | `app/infrastructure/redis/` |
| Cache permisos | `app/core/authorization/permission_resolver.py` |

---

## 5. Routers

### 5.1 Registro central

`app/api/v1/api.py` importa routers de cada módulo y los monta con prefijos:

| Prefijo | Módulo |
|---------|--------|
| `/auth`, `/auth-config`, `/sso` | auth |
| `/clientes`, `/conexiones` | tenant |
| `/superadmin/usuarios`, `/superadmin/auditoria` | superadmin |
| `/modulos-v2`, `/cliente-modulo`, … | modulos |
| `/org`, `/inv`, `/pur`, `/sls`, … | ERP operativos |
| `/usuarios`, `/roles`, `/permisos` | users, rbac |

### 5.2 Sub-routers por entidad

Ejemplo ORG (`app/modules/org/presentation/endpoints.py`):

```python
router.include_router(router_empresa, prefix="/empresa", dependencies=[Depends(require_org_tenant_erp_session)])
```

INV monta sub-routers para productos, movimientos, inventario físico, etc., con `require_inv_tenant_erp_session`.

### 5.3 Dependencias globales de presentación

| Archivo | Funciones clave |
|---------|-----------------|
| `app/api/deps.py` | `get_current_user_data`, `get_current_active_user`, `require_permission` |
| `app/api/deps_auth.py` | `require_erp_session`, `require_full_session_payload`, `require_selection_token_payload` |
| `app/modules/org/presentation/org_deps.py` | `get_org_session_client_id` |
| `app/modules/inv/presentation/inv_deps.py` | `get_inv_session_client_id` |
| `app/modules/rbac/presentation/rbac_deps.py` | `get_rbac_session_client_id` |

---

## 6. Services

Convenciones:

- **ERP:** funciones o clases estáticas `*_servicio` / `*_service` en `application/services/`
- **Platform:** clases de servicio con `@BaseService.handle_service_errors`
- **Transacciones multi-paso:** `UnitOfWork` (INV procesos, IAM sessions V2)
- **Transacciones simples:** `execute_insert` / `execute_update` (commit por operación)
- **Onboarding:** `session.begin()` explícito sobre `get_db_connection(ADMIN)`

Servicios transversales críticos:

| Servicio | Módulo | Rol |
|----------|--------|-----|
| `AuthService` | auth | Orquestación login/refresh/logout/cambio empresa |
| `SessionCreationService` | auth | Creación sesión IAM V2 |
| `SessionRotationService` | auth | Rotación refresh V2 |
| `SessionRevocationService` | auth | Revocación sesiones |
| `ImpersonationService` | auth | Impersonación superadmin |
| `ClienteOnboardingService` | tenant | Seed transaccional de tenant |
| `PermissionResolverService` | core/authorization | Cache permisos por usuario/tenant |
| `MenuResolver` | core/authorization | Árbol de menú por permisos |

---

## 7. Repositories

**Uso limitado** a módulos platform/IAM:

| Repository | Módulo |
|------------|--------|
| `BaseRepository` | infrastructure (base) |
| `UsuarioRepository` | auth |
| `UserRepository` | users |
| `RolRepository`, `PermisoRepository` | rbac |
| `CfgCodigoSecuenciaRepository` | infrastructure (compartido onboarding/ERP) |

`BaseRepository` delega a `execute_query` — no es capa ORM independiente.

**ERP:** cero repositories; acceso vía query functions.

---

## 8. Unit of Work

**Archivo:** `app/core/application/unit_of_work.py`

- Context manager async sobre `get_db_connection`
- Commit automático al salir sin excepción; rollback si hay error
- Acepta `client_id` y `connection_type` (DEFAULT | ADMIN)

**Consumidores principales:**

- IAM sessions V2: `session_creation_service`, `session_rotation_service`, `session_revocation_service`
- `session_transaction_core.py` (queries transaccionales auth)
- INV: `movimiento_proceso_service`, `movimiento_service`, inventario físico
- PUR: creación transaccional
- MNT: `orden_trabajo_service`

**Coexistencia:** código legacy sigue usando `execute_*` con commit por llamada.

---

## 9. Queries

- **Ubicación:** `app/infrastructure/database/queries/{codigo_modulo}/`
- **Estilo:** SQLAlchemy Core (`select`, `insert`, `update`) sobre `Table` o DDL inferido
- **Ejecución:** `queries_async.execute_query` aplica `apply_tenant_filter` automáticamente
- **Tablas ERP:** definidas en DDL `V010__tablas_bd_erp_completo.sql`; **no** todas están en `tables.py`
- **Tablas central:** mapeadas en `tables.py` y `tables_modulos.py`

---

## 10. Dependencias (inyección FastAPI)

| Capa | Mecanismo |
|------|-----------|
| Autenticación | `Depends(get_current_active_user)` → JWT + Redis blacklist |
| RBAC | `Depends(require_permission("modulo.recurso.accion"))` |
| Tenant ERP | `Depends(get_{cod}_session_client_id)` → `require_session_cliente_id` |
| Empresa ERP | `require_session_empresa_id()` en services |
| Superadmin | `@require_super_admin()` decorator |
| Conexión BD | **No** se inyecta sesión; services abren su propia conexión vía `execute_*` o UoW |

**No existe `Depends(get_db)`** — patrón atípico respecto a FastAPI estándar.

---

## 11. Mapa de arquitectura

```mermaid
flowchart TB
    subgraph ingress [Ingress]
        CLIENT[Cliente HTTP]
        MW[TenantMiddleware]
        CTX[ContextVar tenant + database_type]
        CLIENT --> MW --> CTX
    end

    subgraph api [API Layer]
        ROUTER[api/v1/api.py]
        DEPS[deps.py / deps_auth.py]
        EP[presentation/endpoints]
        ROUTER --> EP
        EP --> DEPS
    end

    subgraph app [Application]
        SVC[application/services]
        UOW[UnitOfWork]
        SVC --> UOW
    end

    subgraph infra [Infrastructure]
        Q[queries/{cod}]
        QA[queries_async]
        ROUTE[get_connection_for_tenant]
        ENG[AsyncEngine cache]
        Q --> QA --> ROUTE --> ENG
    end

    subgraph platform [Platform Legacy]
        REPO[repositories/]
    end

    CTX --> DEPS
    EP --> SVC
    SVC --> Q
    SVC -.-> REPO
    REPO --> QA

    subgraph external [External]
        SQL[(SQL Server)]
        REDIS[(Redis)]
    end

    ENG --> SQL
    DEPS --> REDIS
```

---

## 12. Modelo de conexión (estado actual)

| Enum | Uso |
|------|-----|
| `DatabaseConnection.ADMIN` | BD central: `cliente`, `usuario`, `rol`, `permiso`, sesiones IAM, catálogo módulos |
| `DatabaseConnection.DEFAULT` | Datos tenant-aware; hoy apunta a BD compartida con filtro `cliente_id` |

El router `get_connection_for_tenant()` ya contempla `database_type = "multi"` leyendo `cliente_conexion`, pero **en operación actual todos los tenants usan single-DB compartida**.

---

## 13. Referencias normativas internas

| Documento | Rol |
|-----------|-----|
| `ERP_BACKEND_STANDARDS_V4.md` | Estándar técnico |
| `ERP_BACKEND_RULES_V4.md` | Reglas completas |
| `ERP_BACKEND_MASTER_PROMPT_V4.md` | Checklist por módulo ERP |
| `bootstrap_v2/00_manifest/BOOTSTRAP_ORDER.md` | Orden DDL/seeds |

---

## 14. Hallazgos documentales (sin propuesta)

1. **Dualidad arquitectónica:** ERP V4 (queries) vs Platform (repositories) conviven.
2. **Session scope parcial:** solo ORG, INV y RBAC tienen `{cod}_deps.py`; otros módulos ERP pueden usar patrones menos seguros bajo impersonación.
3. **Infraestructura multi-DB parcial:** routing y middleware ya cargan `database_type`, pero onboarding y operación diaria asumen BD compartida.
4. **Sin sesión por request:** cada `execute_*` abre/cierra su propia `AsyncSession`.
