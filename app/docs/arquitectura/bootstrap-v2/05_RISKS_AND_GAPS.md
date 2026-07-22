# 05 — Riesgos, gaps y dependencias de separación

**Etapa:** Auditoría bootstrap-v2 — pregunta 12  
**Nota:** Inventario de riesgos **si** se separa Tenant Bootstrap vs Empresa Bootstrap. No propone solución.

---

## 1. Gaps actuales (pre-separación)

| ID | Gap | Evidencia | Severidad |
|----|-----|-----------|-----------|
| G1 | Dedicated sin `cliente_auth_config` en S7 | ADJ-07; ausente en `dedicated_tenant_seed_adapters.py` | Media |
| G2 | Sin bootstrap para empresa adicional (N>1) | Solo `ensure_empresa_inicial` + EMP001 | Alta (multi-empresa) |
| G3 | 56 secuencias EMPRESA solo en onboarding | `_insertar_secuencias_codigo` una vez por tenant | Alta |
| G4 | `_get_primera_empresa_activa` ambiguo | `TOP 1 ORDER BY fecha_creacion` | Media |
| G5 | `CfgCodigoSecuenciaRepository` sin session → ADMIN | AI-X1 `28_BOOTSTRAP_INTEGRATION_AUDIT.md` | Media (Dedicated) |
| G6 | Nombre `MinimalErpTenantBootstrapService` | Servicio es empresa-centric | Baja (claridad) |

---

## 2. Riesgos al separar Tenant vs Empresa Bootstrap

### R-T1 — Orden de ejecución y FK

**Riesgo:** `cfg_codigo_secuencia` EMPRESA requiere FK lógica a `org_empresa` existente.  
**Evidencia:** `_insertar_secuencias_codigo:409-410` usa `empresa_id`; `insert_secuencia` scope EMPRESA (`cfg_codigo_secuencia_repository.py:199-205`).  
**Si se separa mal:** seed cfg antes de `org_empresa` → fallo o filas huérfanas.

### R-T2 — Transaccionalidad Shared

**Riesgo:** Hoy Shared es **una TX atómica** (`session.begin()` `:100`). Separar en dos fases expone estados intermedios (tenant sin empresa, tenant sin cfg).  
**Evidencia:** docstring `cliente_onboarding_service.py:4-5` promete rollback completo.  
**Impacto:** API `POST /clientes/` podría dejar tenant parcial si empresa bootstrap falla en fase 2.

### R-T3 — Paridad Dedicated S7

**Riesgo:** `tenant_seed_profiles` y markers asumen 6 pasos monolíticos; reordenar o split requiere nuevos `step_code` o sub-perfil.  
**Evidencia:** `_TENANT_SEED_STEPS` (`tenant_seed_profiles.py:38-45`); idempotencia `bootstrap_applied` por paso.  
**Impacto:** Runs Dedicated en PROVISIONING mid-saga necesitan migración de markers.

### R-T4 — Row expectations Dedicated

**Riesgo:** `_verify_row_expectations` espera `org_empresa≥1` y `cfg_codigo_secuencia≥57` en mismo S7.  
**Evidencia:** `tenant_seed_profiles.py:79-85`; `dedicated_tenant_seed_service.py:133-136`.  
**Impacto:** Split exige recalcular expectativas por fase o mover verificación empresa.

### R-T5 — Admin sin empresa default

**Riesgo:** `_insertar_usuario_admin` recibe `empresa_id` (`cliente_onboarding_service.py:118-124`). Si tenant bootstrap corre antes de empresa bootstrap, admin podría crearse sin default válido.  
**Evidencia:** INSERT usa `:empresa_default_id` (`:326`); validación FK en except (`:332-335`).

### R-T6 — RBAC bundles vs empresa

**Riesgo:** Bajo — RBAC onboarding es tenant-wide (`empresa_id=NULL` en grants).  
**Evidencia:** `vincular_admin_empresa:127-130` explícito M4 tenant-wide.  
**Separación RBAC:** probablemente permanece en Tenant Bootstrap.

### R-T7 — Reutilización adapters

**Riesgo:** `dedicated_tenant_seed_adapters.py` importa métodos estáticos mezclados; refactor de firmas rompe Shared y Dedicated simultáneamente.  
**Evidencia:** 6 call sites `:123-199`.  
**Mitigación futura:** requiere contrato estable inter-capas (fuera de alcance).

### R-T8 — Motor de códigos — split TENANT/EMPRESA seed

**Riesgo:** `ONBOARDING_SEQUENCE_SEEDS` mezcla scopes (`onboarding_seed.py:77-83`); separar exige dos entry points o filtro por scope en caller.  
**Evidencia:** `EAGER_SEQUENCE_KEYS` usado en `row_expectations` como conteo único 57.  
**Impacto:** Conteos Dedicated deben partir (1 tenant + 56×N empresas).

### R-T9 — Platform bootstrap confusión

**Riesgo:** Bajo si se mantiene frontera — Platform ya separado (`PlatformBootstrapService`).  
**Evidencia:** No comparte orquestador con `ClienteOnboardingService`.  
**Cuidado:** no mover auth config platform a tenant bootstrap.

### R-T10 — API / contratos públicos

**Riesgo:** `POST /clientes/` retorna `ClienteOnboardingResult` con credenciales tras TX completa.  
**Evidencia:** `cliente_onboarding_service.py:147-165`.  
**Separación visible:** cambiaría semántica si tenant y empresa son operaciones distintas API.

### R-T11 — Multi-empresa runtime vs bootstrap

**Riesgo:** Módulo ORG puede crear empresas post-onboarding sin invocar seed cfg.  
**Evidencia:** No hay hook documentado org→cfg seed en bootstrap actual.  
**Gap amplificado:** separar Empresa Bootstrap sin integrar ORG deja empresas sin secuencias.

### R-T12 — Tests y harness

**Riesgo:** Tests F4-07, F17D, onboarding RBAC asumen flujo monolítico 8 pasos / 6 pasos S7.  
**Evidencia:** `test_f4_07_dedicated_tenant_seed_service.py`; `test_codigo_engine_f17d_full_cfg_seed.py`.  
**Impacto:** Suite de provisioning requiere actualización en etapa implementación.

---

## 3. Matriz riesgo × componente

| Componente | R-T1 | R-T2 | R-T3 | R-T4 | R-T5 | R-T8 |
|------------|------|------|------|------|------|------|
| `cliente_onboarding_service` | ● | ● | ○ | ○ | ● | ● |
| `minimal_erp_tenant_bootstrap_service` | ● | ● | ● | ● | ● | ○ |
| `dedicated_tenant_seed_*` | ● | ○ | ● | ● | ● | ● |
| `onboarding_seed.py` | ● | ○ | ○ | ● | ○ | ● |
| `onboarding_rbac_service` | ○ | ○ | ○ | ○ | ○ | ○ |

● = impacto directo · ○ = impacto bajo o indirecto

---

## 4. Dependencias externas al bootstrap (no modificar en esta etapa)

| Sistema | Relación |
|---------|----------|
| `DedicatedProvisioningOrchestrator` | Orquesta S7; no es bootstrap tenant puro |
| `permission_sync` startup | Catálogo global; prerequisito platform y S6 |
| `CodigoGeneracionGateway` / lazy | Runtime; fuera seed onboarding |
| Módulo ORG (crear empresa) | Consumidor futuro de Empresa Bootstrap |

---

## 5. Invariantes a preservar (cualquier separación futura)

1. **Session-driven writes** — seed cfg siempre con `session=` explícita (`cfg_codigo_secuencia_repository._assert_write_session`).
2. **SequenceCatalog SSOT** — metadatos no duplicados en bootstrap (`onboarding_seed.py:1-11`).
3. **Paridad Shared/Dedicated** — mismos métodos o contratos equivalentes (`28` AI-D1).
4. **RBAC tenant-wide** — admin grants con `empresa_id=NULL` (`vincular_admin_empresa:127-130`).
5. **Dedicated DDL antes de S7** — catálogos S6 antes de RBAC (`verify_tenant_seed_prerequisites`).

---

*Resumen ejecutivo con respuestas 1–12: `06`.*
