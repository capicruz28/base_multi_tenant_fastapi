# 03 — Connection Resolution

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** E4 RD-01, RD-07, G-09, G-10  
**Restricción:** Diseño del proceso de resolución. Sin clases nombradas ni pseudocódigo.

---

## 1. Propósito

Especificar **cómo se traduce** Storage Metadata + operation class en un **connection binding** utilizable para obtener engine y sesión SQL — encapsulando toda diferencia Shared/Dedicated.

---

## 2. Definición

**Connection Resolution** es el subproceso del Persistence Gateway que, dado:

- identificador tenant (o SYSTEM para platform)
- operation class (`control_plane` | `tenant_data`)
- Storage Metadata (de 02)

produce un **Connection Binding**: descriptor inmutable para la operación actual que incluye destino almacén, clave engine, y parámetros de conexión.

---

## 3. Inputs y outputs

### 3.1 Inputs

| Input | Origen | Obligatorio |
|-------|--------|-------------|
| Operation class | Caller gateway (implícito en tipo execute) | Sí |
| Tenant identifier | Parámetro explícito o ContextVar | Sí para tenant_data |
| Storage Metadata | Metadata Resolution (02) | Sí para tenant_data |
| Connection metadata override | Parámetro directo (optimización) | No |

### 3.2 Output: Connection Binding

| Campo conceptual | Descripción |
|------------------|-------------|
| Store target | `control_plane_store` \| `tenant_data_store` |
| Engine cache key | Identificador único engine en proceso |
| Connection string components | Server, database, auth (interno L6) |
| Tenant filter mode | `enforce` \| `relaxed` \| `skip` (solo scripts) |
| Installation mode (interno) | Solo logging/metrics; no expuesto L5 |

---

## 4. Árbol de decisión

### 4.1 Operation class = control_plane

```
→ Store target: Control Plane Store
→ Engine cache key: "admin" (fijo por proceso)
→ Connection: settings DB_ADMIN_*
→ Tenant filter: N/A (tablas globales CP)
```

**Casos especiales SYSTEM tenant:** Superadmin host usa ADMIN para lookups platform; coherente con AS-IS `SYSTEM_CLIENT_ID → ADMIN`.

### 4.2 Operation class = tenant_data

```
→ Obtener Installation Mode desde metadata

  IF mode = shared (AS-IS: single):
    → Store target: Tenant Data Store (shared físico)
    → Engine cache key: "tenant_shared" OR "tenant_{id}" según política cache
    → Connection: settings DB_* globales
    → Tenant filter: enforce cliente_id

  IF mode = dedicated (AS-IS: multi):
    → Store target: Tenant Data Store (instancia dedicada)
    → Engine cache key: "tenant_{id}" (único por tenant)
    → Connection: Storage Endpoint Metadata
    → Tenant filter: policy encapsulada (enforce por contrato; aislamiento físico)

  IF mode = dedicated AND metadata missing:
    → ERROR (RI-39) — no fallback

  IF mode = shared/legacy AND metadata missing:
    → Fallback shared (RD-08)
```

---

## 5. Política de engine cache key

| Escenario | Engine key | Motivo |
|-----------|------------|--------|
| ADMIN / control_plane | `admin` | Una instancia CP por worker |
| Shared (todos tenants) | `shared_default` o `tenant_{id}` | **Decisión TD-03** (ver 10) |
| Dedicated per tenant | `tenant_{id}` | Pool aislado por tenant |

**AS-IS actual:** key `tenant_{client_id}` incluso en shared (mismo engine subyacente repetido). **Optimización Etapa 6:** consolidar shared en key única `shared_default` para reducir engines duplicados — requiere validación pool sharing.

---

## 6. Momentos de resolución (RD-01)

| Momento | Comportamiento |
|---------|----------------|
| Cada `execute_*` | Resolución completa salvo L-A cache hit |
| UoW `__aenter__` | Una resolución al abrir; reutilizada en `execute()` internos |
| Conexión explícita ADMIN | Resolución control_plane directa |
| Background job | Resolución con tenant sintético inyectado |

**No existe resolución once-per-request HTTP global** — coherente con AS-IS sin session-per-request.

---

## 7. Vías de acceso AS-IS mapeadas

| Vía AS-IS | Resolución |
|-----------|------------|
| `execute_*` → `_get_connection_context` | tenant_data vía `get_connection_for_tenant` |
| `get_db_connection(ADMIN)` | control_plane directo |
| `get_db_connection(DEFAULT, client_id)` | tenant_data con metadata opcional |
| `get_connection_for_tenant(cliente_id)` | Orquestador tenant_data |
| `UnitOfWork` | Delega a `get_db_connection` con client_id |

**Consolidación objetivo:** `get_connection_for_tenant` permanece como **orquestador tenant_data** dentro del gateway; no se expone a L5.

---

## 8. Tablas híbridas (control vs tenant)

Algunas operaciones AS-IS enrutan distinto según mode (ej. `auth_audit_log`). Resolución canónica:

| Patrón | Regla |
|--------|-------|
| Dato clasificado CP en E3 | Siempre control_plane |
| Dato clasificado DP | Siempre tenant_data |
| Dato transversal IAM (sesión) | **Pendiente RD-11** — ruta fija una vez decidido |

**Prohibido:** lógica híbrida en L5. Si ruta depende de mode, encapsular en gateway con operation class + metadata lookup interno.

---

## 9. Validaciones pre-conexión

| Validación | Fallo |
|------------|-------|
| tenant_data sin client_id | Error configuración caller |
| client_id ≠ ContextVar sin override explícito | Warning auditoría; preferir coherencia |
| Tenant Migrando + operación ERP | Error mapeado 503/409 según contrato |
| Dedicated metadata estado Error | Error infra mapeado |
| Credenciales expiradas | Error; trigger ops alert |

---

## 10. Límites y cuotas (futuro)

| Límite | Propósito |
|--------|-----------|
| Max engines dedicated por worker | Protección memoria |
| Max concurrent resolution CP | Rate limit metadata storm |
| Timeout metadata lookup | Evitar hang request |

No diseñados en MVP; documentados para extensión.

---

## 11. Gap AS-IS

| Gap | Descripción |
|-----|-------------|
| CR-01 | `routing.py` incluye vías pyodbc sync legacy — fuera gateway async canónico |
| CR-02 | IAM services leen `database_type` para elegir ruta — violación G-05 |
| CR-03 | Engine key por tenant en shared crea engines redundantes |
| CR-04 | `request.state.cliente_id` no poblado — fallback session_scope inoperante |

---

## 12. Conclusión

Connection Resolution es el **único lugar** donde Installation Mode altera el camino hacia SQL. Produce Connection Binding consumido por Engine Management y Session Lifecycle. L5 permanece agnóstico.

Documentos relacionados: `04_ENGINE_MANAGEMENT`, `05_SESSION_LIFECYCLE`, `02_STORAGE_METADATA_RESOLUTION`.
