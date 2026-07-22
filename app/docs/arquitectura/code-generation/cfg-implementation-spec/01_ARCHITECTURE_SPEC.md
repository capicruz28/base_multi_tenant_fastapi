# Arquitectura — especificación oficial v1.0

**Paquete:** `cfg-implementation-spec`  
**Versión:** 1.0

---

## 1. Posicionamiento

```text
Platform (onboarding)     → seed cfg_codigo_secuencia (fuera de este MVP HTTP)
Módulo ERP cfg (este MVP) → administrar filas cfg del tenant
app/core/codigo (Motor)   → Gateway.preview / Catalog enrich (no modificar)
ORG / INV                 → consumidores allocate (no modificar)
```

**Regla:** Platform provisiona; `cfg` parametriza; Motor ejecuta generación.

---

## 2. Estructura de carpetas (obligatoria)

```text
app/modules/cfg/
├── __init__.py
├── presentation/
│   ├── __init__.py
│   ├── router.py
│   ├── cfg_deps.py
│   ├── schemas.py
│   └── endpoints_codigo_secuencia.py
└── application/
    ├── __init__.py
    └── services/
        ├── __init__.py
        └── codigo_secuencia_admin_servicio.py
            # validator / enricher / preview context como funciones
            # en el mismo módulo o un solo archivo support auxiliar

app/infrastructure/database/queries/cfg/
├── __init__.py
└── codigo_secuencia_queries.py
```

**Prohibido:**

- `domain/`, `infrastructure/` dentro del módulo
- Extender `CfgCodigoSecuenciaRepository` en este MVP (**G-06**)
- Modificar `app/core/codigo/**`, `app/modules/org/**`, `app/modules/inv/**`

**Montaje:** `api_router.include_router(..., prefix="/cfg", tags=["CFG - Secuencias de código"])`.

---

## 3. Session y dependencias

| Dependency | Rol |
|------------|-----|
| `require_cfg_tenant_erp_session` | Gate router padre; policy TENANT (no exige `empresa_id`) |
| `get_cfg_session_client_id` | `cliente_id` operativo via `require_session_cliente_id` (impersonación-safe) |
| `require_permission(...)` | RBAC por endpoint |
| Usuario auditoría | Desde sesión (mismo patrón ORG) → `usuario_actualizacion_id` |

**Prohibido:** `current_user.cliente_id` para filtrar datos; `cliente_id` en body/query como autorización.

---

## 4. Capas y responsabilidades

| Capa | Responsabilidad |
|------|-----------------|
| Endpoints | HTTP, deps, propagar `CustomException` |
| Services `*_servicio` | Orquestación, reglas, enrich, UoW |
| Queries `queries/cfg` | SQL list/get/update/soft-activo con `session` obligatoria en writes |
| Gateway | Solo `preview` |
| SequenceCatalog | Solo enrich read-only |

---

## 5. Persistencia y topologías

| Topología | Comportamiento |
|-----------|----------------|
| Shared | `get_connection_for_tenant` → session + filtro `cliente_id` |
| Dedicated | Misma API de servicio → session BD dedicada |

**Toda** I/O del admin HTTP usa session tenant.  
**Prohibido:** Path A `DatabaseConnection.ADMIN` del Repo para este módulo.

Mutaciones:

```text
async with get_connection_for_tenant(cliente_id=...) as session:
    async with session.begin():
        ...
```

---

## 6. Integración Motor

| API | Uso MVP |
|-----|---------|
| `CodigoGeneracionGateway.preview` | POST preview |
| `CodigoGeneracionGateway.allocate` | **Nunca** |
| `CodigoGeneracionGateway.align_counter` | **Nunca** (post-MVP) |
| `SequenceCatalog.get` / `contains` | Enrich Read |
| `CfgSequenceStore` | Solo indirecto vía Gateway.preview |

`GenerationContext` para preview: `client_id` + `operation=PREVIEW` + `empresa_id` / `almacen_id` / `punto_venta_id` **desde la fila cfg** (no body).

---

## 7. Queries canónicas

| Función | Uso |
|---------|-----|
| `list_codigo_secuencias` | Filtros SQL nativos (sin page SQL — ver API G-04) |
| `get_codigo_secuencia_by_id` | `secuencia_id` + `cliente_id` |
| `update_codigo_secuencia_config` | Campos B + audit; exige session |
| `set_codigo_secuencia_activo` | `es_activo` + audit; exige session |

Filtros SQL nativos: `scope_type`, `sequence_key`, `empresa_id`, `es_activo`, `buscar` (LIKE key/prefijo).

---

## 8. RBAC

| Permiso | Endpoints |
|---------|-----------|
| `cfg.secuencias.consultar` | GET list, GET detail, POST preview |
| `cfg.secuencias.actualizar` | PATCH, DELETE, POST reactivar |

Sembrar ambos en catálogo y otorgar a `ADMIN_TENANT` (y plantillas aplicables).  
**No** sembrar `mantener` / `diagnosticar` en MVP.

---

## 9. Auditoría

En PATCH, DELETE (soft), reactivar:

- `fecha_actualizacion`
- `usuario_actualizacion_id`

Preview: sin audit de negocio obligatorio.
