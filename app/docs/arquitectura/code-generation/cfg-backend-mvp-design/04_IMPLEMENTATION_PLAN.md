# Plan de implementación (orden exacto)

**Paquete:** `cfg-backend-mvp-design`  
**Fecha:** 2026-07-17  
**Estado:** Blueprint listo — **ejecutar solo tras autorización explícita**

---

## 1. Orden exacto de implementación

| Paso | Entregable | Notas |
|------|------------|-------|
| **1** | Seed RBAC permisos `cfg.secuencias.consultar` + `cfg.secuencias.actualizar` | Otorgar a ADMIN_TENANT / plantilla; sin esto los endpoints no son usables en staging |
| **2** | Esqueleto `app/modules/cfg/` + `__init__` | Sin lógica |
| **3** | `presentation/schemas.py` | Read, Update, Preview, Paginated |
| **4** | `queries/cfg/codigo_secuencia_queries.py` | list, count, get, update config, set activo |
| **5** | Extender `CfgCodigoSecuenciaRepository.update_secuencia` **o** solo queries | Si queries cubren update+audit+numero_inicial, Repo extension opcional; **preferir queries canónicas** y extender Repo solo si onboarding/otros lo necesitan |
| **6** | `cfg_catalog_enricher.py` | |
| **7** | `cfg_secuencia_validator.py` | |
| **8** | `cfg_preview_context_builder.py` | |
| **9** | `codigo_secuencia_admin_servicio.py` | GET list/detail primero |
| **10** | `cfg_deps.py` + `router.py` | |
| **11** | Endpoints GET list + GET detail | Mount en `api.py` |
| **12** | Tests unitarios lectura + aislamiento | Gate parcial |
| **13** | Services + endpoints PATCH / activar / desactivar | |
| **14** | Tests mutación + org_empresa lock + colisión | |
| **15** | Service + endpoint preview | |
| **16** | Tests preview sin side-effect | |
| **17** | Regenerar / actualizar snapshot OpenAPI | Solo en este paso |
| **18** | Suite certificación (`06`) | Gate MVP Backend |

**No adelantar:** OpenAPI antes de endpoints estables; Frontend; Align.

---

## 2. Archivos que se tocarán (cuando se autorice)

| Archivo | Acción |
|---------|--------|
| `app/modules/cfg/**` | **Crear** |
| `app/infrastructure/database/queries/cfg/**` | **Crear** |
| `app/api/v1/api.py` | include_router |
| Seeds RBAC / SQL permisos (ruta canónica del repo) | Insert permisos |
| `CfgCodigoSecuenciaRepository` | Extensión menor opcional |
| `tests/unit/test_cfg_*.py` | **Crear** |
| OpenAPI snapshot | Actualizar al final |

| Archivo | **No tocar** |
|---------|--------------|
| `app/core/codigo/**` | Motor frozen |
| `app/modules/org/**`, `inv/**` | Congelados Ola 1 |
| Frontend | Fuera de alcance |

---

## 3. Riesgos técnicos

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| T-01 | Lectura admin vía Repo Path A ADMIN en Dedicated | Alta | Solo `get_connection_for_tenant` |
| T-02 | Preview consume contador por error de API | Alta | Solo `Gateway.preview`; assert en test |
| T-03 | Olvidar lock org_empresa en BE | Alta | Validator + tests |
| T-04 | PATCH acepta `ultimo_numero` | Alta | `extra='forbid'` + tests |
| T-05 | Filtro `modulo_codigo` costoso | Baja | In-memory OK volumen bajo |
| T-06 | Sesión company-required bloquea listado | Media | `require_cfg_tenant_erp_session` |
| T-07 | Permisos no sembrados | Alta | Paso 1 primero |
| T-08 | Drift doc OpenAPI vs schemas | Media | Paso 17 al final |
| T-09 | Colisión formato false positive | Baja | Criterio estricto prefijo+sep+pad |
| T-10 | Impersonación usa cliente SYSTEM | Alta | `get_cfg_session_client_id` patrón ORG |

---

## 4. Estimación de esfuerzo (orientativa)

| Bloque | Complejidad |
|--------|-------------|
| Schemas + deps + router mount | Baja |
| Queries dual-path + pagination | Media |
| Services + validator + enrich | Media |
| Preview integration | Baja–media |
| RBAC seed | Baja–media (según tooling seeds) |
| Tests certificación | Media–alta |

---

## 5. Definición de “listo para implementar”

El equipo puede empezar el Paso 1 cuando el usuario diga explícitamente autorizar implementación del MVP Backend, usando **este blueprint como única guía técnica**.
