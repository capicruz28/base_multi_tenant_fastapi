# CFG Admin — Auditoría arquitectónica (estado actual)

**Etapa:** Auditoría de solo lectura — **sin implementación**  
**Fecha:** 2026-07-17  
**Contexto:** Ola 1 Motor (ORG + INV Backend/Frontend) **cerrada**  
**Objetivo:** determinar qué existe, qué se reutiliza y qué falta para el Administrador del Motor  
**Alcance de datos:** `cfg_codigo_secuencia` (store CFG). Excluye series fiscales.

---

## 1. Dictamen ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Existe un módulo ERP `cfg` implementado? | **No** — no hay `app/modules/cfg/`, ni routers, ni schemas, ni OpenAPI `/cfg/*` |
| ¿Existe la tabla y el ORM? | **Sí** — DDL V010 + `CfgCodigoSecuenciaTable` |
| ¿El Motor ya lee/escribe cfg? | **Sí** — `CfgSequenceStore` + `CodigoGeneracionGateway` |
| ¿Existe persistencia de bootstrap? | **Sí** — `CfgCodigoSecuenciaRepository` + seed onboarding |
| ¿Existe diseño previo del admin? | **Sí** — paquete `codigo-generation-admin/` (2026-07-12), sin código |
| ¿Puede un Tenant Admin configurar el Motor hoy vía API? | **No** |

### Porcentajes (alcance “Administrador del Motor” completo)

| Dimensión | Existe | Por implementar |
|-----------|--------|-----------------|
| **Fundación reutilizable** (DDL, ORM, Store, Repo, Catalog, Gateway preview/align) | **~90%** | ~10% (extensiones menores: p. ej. `numero_inicial` en update, queries list paginado) |
| **Módulo ERP admin** (presentation + services + RBAC + tests + OpenAPI) | **~0%** código / **100%** diseño documental | **~100%** del producto admin |
| **Producto CFG Admin (ponderado)** | **~30%** | **~70%** |

**Lectura:** la infraestructura de datos y runtime está madura y congelada. Falta casi todo el módulo ERP de administración que la expone de forma segura al Tenant Administrator.

---

## 2. Qué se reutiliza sin modificar Motor/Gateway/Catalog

| Componente | Uso en admin futuro |
|------------|---------------------|
| `CfgCodigoSecuenciaTable` | Fuente de verdad persistente |
| `CfgSequenceStore` | Solo vía Gateway en runtime; admin **no** debe escribir contador directo |
| `CfgCodigoSecuenciaRepository` | List/get/update config (extendible); escrituras con `session` obligatoria (ADJ-03) |
| `SequenceCatalog` | Metadatos read-only (policy nominal, defaults, módulo) |
| `CodigoGeneracionGateway.preview` | Preview sin consumo |
| `CodigoGeneracionGateway.align_counter` | Mantenimiento controlado |
| `CodigoGeneracionGateway.validate_manual` | Validación operativa |
| `CodeFormatter` / Parser / Validator | Indirectos vía Gateway; no reimplementar |
| `get_connection_for_tenant` | UoW Dedicated/Shared |
| Diseño `codigo-generation-admin/` | Contrato funcional y taxonomía ya definidos |

---

## 3. Qué requiere desarrollo nuevo

| Capacidad | Estado |
|-----------|--------|
| Módulo `app/modules/cfg/` (V4) | Inexistente |
| `queries/cfg/` dual-path + paginación | Inexistente |
| Schemas Read/Update/Preview/Align/Diagnóstico | Inexistentes |
| Servicios admin + validadores BR-CUST | Inexistentes |
| Endpoints `/cfg/secuencias` | Inexistentes |
| Permisos RBAC `cfg.secuencias.*` | Inexistentes (sin seed SQL) |
| OpenAPI snapshot del recurso | Inexistente |
| Tests unitarios/integración admin | Inexistentes |
| Menú/Frontend admin secuencias | Fuera de esta auditoría de código; no hay contrato FE CFG implementado en Backend |

---

## 4. MVP recomendado (primera versión)

**MVP = Fase A + Fase B del diseño `codigo-generation-admin`**, acotado:

1. **Solo lectura:** listado + detalle enriquecido con catálogo (`cfg.secuencias.consultar`).
2. **Configuración segura:** PATCH de campos B (`prefijo`, `separador`, `longitud_numero`, `numero_inicial`, `es_activo`) con validaciones anti-colisión y bloqueo `org_empresa` donde aplique (`cfg.secuencias.actualizar`).
3. **Preview:** POST delegado a Gateway (`consultar`).
4. **Fuera de MVP:** align, diagnóstico avanzado, historial de auditoría dedicado, admin fiscal, cambio de `generation_policy`.

Gate MVP: Tenant Admin puede **ver** y **ajustar formato/activo** de secuencias de su tenant sin tocar Motor/Gateway/Catalog y sin poder mutar `ultimo_numero` directamente.

---

## 5. Índice del paquete

| Doc | Contenido |
|------|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este documento |
| `01_CURRENT_ARCHITECTURE.md` | Arquitectura AS-IS y límites |
| `02_EXISTING_INFRASTRUCTURE.md` | Inventario de código existente |
| `03_SEQUENCE_CONFIGURATION_ANALYSIS.md` | Políticas, perfiles, strategies, scope |
| `04_SECURITY_AND_GOVERNANCE.md` | RBAC, tenant/empresa, Dedicated/Shared |
| `05_GAP_ANALYSIS.md` | Gaps, riesgos, deuda, simplificación |
| `06_RECOMMENDED_IMPLEMENTATION_SCOPE.md` | Alcance MVP y fases posteriores |

---

*No se modificó código. Siguiente paso: aprobación del alcance MVP antes de cualquier implementación.*
