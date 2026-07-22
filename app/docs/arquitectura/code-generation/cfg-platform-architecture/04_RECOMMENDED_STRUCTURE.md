# Estructura recomendada (post-decisión)

**Paquete:** `cfg-platform-architecture`  
**Fecha:** 2026-07-17  
**Alcance:** estructura lógica — **sin crear archivos de código en esta etapa**

---

## 1. Mapa de responsabilidades definitivo

| Capa | Path conceptual | Responsabilidad |
|------|-----------------|-----------------|
| Shared kernel | `app/core/codigo/` | Motor: allocate, preview, align, validate, Catalog |
| Persistencia | `cfg_codigo_secuencia` + ORM/Repo/Store | Datos tenant |
| **Módulo ERP admin** | `app/modules/cfg/` | HTTP + services + queries admin |
| Platform onboarding | `app/modules/tenant/.../cfg_codigo_onboarding_seed` | Seed inicial únicamente |
| Consumidores negocio | `app/modules/org`, `inv`, … | CREATE/UPDATE vía Gateway adapters |

---

## 2. Estructura de módulo ERP `cfg` (objetivo)

Alineada a ORG/INV V4 y a `codigo-generation-admin/07_MODULE_ARCHITECTURE.md`:

```text
app/modules/cfg/
├── presentation/
│   ├── router.py                 # prefix /cfg, require_erp_session
│   ├── cfg_deps.py               # get_cfg_session_client_id
│   ├── schemas.py                # Read / Update / Preview / …
│   └── endpoints_codigo_secuencia.py
├── application/
│   └── services/
│       └── codigo_secuencia_admin_servicio.py  # funciones *_servicio
└── (sin domain/ ni infrastructure/ por módulo)

app/infrastructure/database/queries/cfg/
└── codigo_secuencia_queries.py   # dual-path session, list/detail
```

**Montaje API:** `/cfg/...` en `app/api/v1/api.py` (cuando se implemente).

**Prohibido en el módulo:**

- Usar `DatabaseConnection.ADMIN` para writes operativos de secuencias
- Importar services ORG/INV para mutar cfg
- Duplicar Formatter/PolicyResolver
- Replicar patrón class-based de Platform (§21)

---

## 3. Fronteras de invocación

```text
HTTP /cfg/secuencias
  → cfg presentation (RBAC)
  → cfg *_servicio
      → queries/cfg  (lectura / update campos B)
      → CfgCodigoSecuenciaRepository (opcional, session obligatoria)
      → CodigoGeneracionGateway.preview|align|validate_manual
      → SequenceCatalog.get (enrich read-only)
```

Platform `tenant` **no** llama al módulo `cfg` en operación normal.  
El seed de onboarding puede seguir usando Repo/seed directo (como hoy), sin pasar por HTTP `/cfg`.

---

## 4. Clasificación de entidad

| Recurso | Clasificación session scope |
|---------|----------------------------|
| `cfg_codigo_secuencia` (admin) | **TENANT** — autorización por `cliente_id` |
| Filtro `empresa_id` | Query opcional; no autoriza solo |
| Scopes ALMACEN / PV | Visibles cuando existan filas; no cambian el gate TENANT |

Cross-tenant / fila de otro cliente → **404**.

---

## 5. Permisos y menú (estructura lógica)

| Permiso | Uso |
|---------|-----|
| `cfg.secuencias.consultar` | List, detail, preview |
| `cfg.secuencias.actualizar` | PATCH B, activar/desactivar |
| `cfg.secuencias.mantener` | Align (post-MVP) |
| `cfg.secuencias.diagnosticar` | Diagnóstico (post-MVP) |

Menú sugerido (FE futuro): **Configuración → Secuencias de código** (tenant shell ERP), **no** bajo consola SuperAdmin.

---

## 6. Shared vs Dedicated (estructura de acceso)

| Topología | Acceso desde módulo `cfg` |
|-----------|---------------------------|
| Shared | `get_connection_for_tenant` / DEFAULT + `client_id` según patrón vigente ORG/INV |
| Dedicated | Misma API de servicio; session de BD dedicada obligatoria en mutaciones |

Misma semántica funcional; distinto binding de conexión. **Una sola implementación** de servicios.

---

## 7. Qué permanece fuera de `cfg`

| Artefacto | Dónde queda |
|-----------|-------------|
| SequenceCatalog, Gateway, Store | `core/codigo` |
| Seed onboarding | `modules/tenant` + `core/codigo/onboarding_seed` |
| Emisión de códigos en maestros | ORG/INV adapters |
| Branding / clientes / conexiones | `modules/tenant` (Platform) |
| Series fiscales | Fuera del admin cfg v1 (store FISCAL) |

---

## 8. Relación con auditoría AS-IS

La estructura anterior **no cambia** los porcentajes de `cfg-admin-audit/`:

- Fundación ~90% reutilizable  
- Módulo `cfg` ~0% → a construir cuando se autorice MVP  

Esta decisión solo fija **dónde** se construye, no **cuándo** ni el detalle OpenAPI.
