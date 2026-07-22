# 04 — Bootstrap V2: Modelo de extensión

**Etapa:** Diseño TO-BE — respuestas a preguntas 12–14

---

## 1. Multi-empresa por tenant (pregunta 12)

### 1.1 Problema AS-IS

Tenant Bootstrap crea EMP001 y seed cfg EMPRESA **una vez**, acoplado al onboarding. Empresa N>1 no tiene bootstrap automático.

### 1.2 Solución V2 (sin cambiar onboarding observable)

| Escenario | Quién orquesta | Quién ejecuta |
|-----------|----------------|---------------|
| **Onboarding inicial** (EMP001) | Tenant Bootstrap | Empresa Bootstrap (modo `INITIAL`) |
| **Alta empresa adicional** (futuro ORG) | Módulo ORG (transaccional) | Empresa Bootstrap (modo `ADDITIONAL`) |
| **Reparación / idempotencia** | Script repair o retry | Empresa Bootstrap (modo `ENSURE`) |

### 1.3 Contrato oficial EmpresaBootstrapService — modos

**Servicio:** `EmpresaBootstrapService` (componente interno; no expuesto en API pública).

**Prerequisitos comunes (todos los modos):**

| Prerequisito | Obligatorio |
|--------------|-------------|
| `session` SQL activa (propagada por caller) | Sí |
| `cliente_id` válido en scope tenant | Sí |
| Roles tenant seed completos (T2) | Sí — caller garantiza |
| Motor cfg / `SequenceCatalog` disponible | Sí |

**Operaciones prohibidas (todos los modos):**

| Prohibido | Razón |
|-----------|-------|
| Crear `cliente`, roles, admin, RBAC tenant | Responsabilidad Tenant Bootstrap |
| Seed cfg TENANT (1 fila) | Responsabilidad Tenant Bootstrap |
| Abrir TX propia si caller ya tiene TX | Session-driven (P2) |
| DELETE físico | Soft delete / idempotencia |
| Exponer endpoint HTTP directo | Componente interno (DA-02) |

#### Modo `INITIAL`

| Atributo | Valor |
|----------|-------|
| **Trigger** | Tenant Bootstrap paso 3 onboarding (Shared paso 3; Dedicated S7 `seed_org_empresa`) |
| **Input** | `cliente_id`, `session`, datos empresa inicial (razón social, RUC, etc. AS-IS) |
| **Operaciones permitidas** | E-ORG: `ensure_empresa_inicial` → EMP001; E-LNK: `vincular_admin_empresa` (paso 5); E-CFG: seed 56 filas cfg EMPRESA para `empresa_id` |
| **Operaciones prohibidas** | Crear empresa N>1; seed cfg TENANT; modificar admin/roles |
| **Idempotencia** | `ensure_empresa_inicial` idempotente por `cliente_id` (retorna existente si ya hay EMP001) |
| **cfg EMPRESA** | 56 filas por `empresa_id` vía subset EMPRESA de seed codigo (delegación AS-IS Fase 1) |
| **Output** | `empresa_id` (UUID) |
| **Observable** | Idéntico AS-IS: EMP001 automática, admin vinculado, 57 cfg totales (1 TENANT + 56 EMPRESA) |
| **Orden invariante** | Debe ejecutarse **antes** de T3 admin seed (INV-01, `02` §5.1) |

#### Modo `ADDITIONAL`

| Atributo | Valor |
|----------|-------|
| **Trigger** | Módulo ORG al crear empresa N>1 (Fase 5 — futuro) |
| **Input** | `cliente_id`, `empresa_id` (nuevo), `session`, datos empresa |
| **Operaciones permitidas** | E-ORG: crear empresa adicional; E-CFG: seed 56 filas cfg EMPRESA para nuevo `empresa_id` |
| **Operaciones prohibidas** | E-LNK admin (admin ya existe); seed cfg TENANT; tocar EMP001 |
| **Idempotencia** | Por `empresa_id`: si cfg EMPRESA ya existe → skip sin duplicar |
| **cfg EMPRESA** | 56 filas nuevas; no modifica filas de otras empresas |
| **Output** | `empresa_id` confirmado |
| **Observable** | Nueva empresa operativa con cfg; onboarding inicial sin cambio |
| **Prerequisito caller** | Tenant onboarding completado; al menos EMP001 existente |

#### Modo `ENSURE`

| Atributo | Valor |
|----------|-------|
| **Trigger** | Repair scripts, redispatch saga, legacy repair (consumidores secundarios, `03` §10) |
| **Input** | `cliente_id`, `empresa_id`, `session` |
| **Operaciones permitidas** | Verificar existencia empresa; re-seed cfg EMPRESA faltante; re-vincular admin si caller lo solicita explícitamente (E-LNK opcional según script) |
| **Operaciones prohibidas** | Crear cliente; crear roles; alterar cfg TENANT; duplicar filas cfg existentes |
| **Idempotencia** | **Obligatoria:** operaciones no-op si estado ya correcto; sin UNIQUE violations |
| **cfg EMPRESA** | Insert solo filas ausentes; no UPDATE valores existentes salvo script repair explícito |
| **Output** | Reporte interno: `{ ensured: bool, cfg_rows_created: int }` |
| **Observable** | Ninguno en UX; uso operacional / soporte |

**Resumen modos (referencia rápida):**

| Modo | Trigger | Operaciones | Observable |
|------|---------|-------------|------------|
| `INITIAL` | Tenant onboarding paso 3 | E-ORG + E-LNK + E-CFG | Igual hoy |
| `ADDITIONAL` | ORG crear empresa | E-ORG + E-CFG | Nueva empresa operativa con cfg |
| `ENSURE` | Repair / redispatch | Idempotente por `empresa_id` | Sin duplicados |

### 1.4 Por qué no requiere re-modificar Tenant Bootstrap

Tenant Bootstrap **solo invoca** Empresa Bootstrap en onboarding inicial. Multi-empresa es **nueva invocación directa** ORG → Empresa Bootstrap con distinto `empresa_input`. Tenant Bootstrap permanece congelado en responsabilidades T-*.

### 1.5 cfg codigo multi-empresa

| Scope | Cuándo se crea | Owner |
|-------|----------------|-------|
| TENANT (1 fila) | Onboarding tenant | Tenant Bootstrap |
| EMPRESA (56 filas) | Por cada `empresa_id` | Empresa Bootstrap |
| ALMACEN / PUNTO_VENTA | Creación entidad | Dominio Bootstrap o Motor lazy |

---

## 2. Modelo de extensión para bootstraps de dominio (pregunta 13)

### 2.1 Jerarquía de bootstraps

```
Platform Bootstrap          (global, 1× instalación)
    │
Tenant Bootstrap            (por cliente, orquestador onboarding)
    │
Empresa Bootstrap           (por org_empresa, core ERP)
    │
Domain Bootstraps           (por entidad de dominio, plug-in)
    ├── Warehouse Bootstrap
    ├── PuntoVenta Bootstrap
    ├── CentroCostos Bootstrap
    ├── Produccion Bootstrap
    └── Contabilidad Bootstrap
```

### 2.2 Reglas de extensión

| Regla | Descripción |
|-------|-------------|
| X-01 | Dominio bootstraps **no modifican** Tenant ni Empresa core |
| X-02 | Se registran en `BootstrapExtensionRegistry` (conceptual) |
| X-03 | Invocados por **módulo ERP owner** al crear entidad (ej. ORG crea almacén → Warehouse Bootstrap) |
| X-04 | Reciben `(session, cliente_id, empresa_id?, entity_id, context)` |
| X-05 | Idempotentes por entidad (`ensure_*` pattern) |
| X-06 | Lazy cfg ALMACEN/PV puede delegar en Motor `ensure_row` sin bootstrap dedicado |
| X-07 | No abren conexión propia — session del UoW del servicio ERP |

### 2.3 Bootstraps futuros — responsabilidades conceptuales

| Bootstrap | Trigger natural | Artefactos típicos | Depende de |
|-----------|-----------------|-------------------|------------|
| **Warehouse** | Alta `org_almacen` | cfg ALMACEN lazy, defaults stock | `empresa_id`, `almacen_id` |
| **PuntoVenta** | Alta punto venta | cfg PV lazy, caja defaults | `empresa_id`, `pv_id` |
| **CentroCostos** | Alta centro costo | plan contable links, cfg | `empresa_id` |
| **Produccion** | Activación módulo + BOM inicial | cfg producción, rutas | `empresa_id` |
| **Contabilidad** | Activación módulo contable | plan cuentas seed, periodos | `empresa_id` |

### 2.4 Integración sin romper arquitectura

```
ORG Service.crear_almacen(...)
    │
    ├── UoW ERP (session tenant DB)
    ├── INSERT org_almacen
    └── BootstrapExtensionRegistry.invoke("warehouse", ctx)
            └── WarehouseBootstrap.ensure(ctx)
                    └── AllocationCoordinator.ensure_row (ALMACEN scope)
```

**Tenant Bootstrap y Empresa Bootstrap no conocen** Warehouse Bootstrap. Solo el registry y el módulo ORG/INV.

### 2.5 cfg_codigo_secuencia y dominio

| Scope | Mecanismo V2 |
|-------|--------------|
| TENANT / EMPRESA | Bootstrap core (Tenant / Empresa) |
| ALMACEN / PUNTO_VENTA | Dominio bootstrap **o** Motor lazy (AS-IS) |
| SERIE_FISCAL | Fuera cfg — store FISCAL (sin cambio) |

---

## 3. Principios arquitectónicos oficiales (pregunta 14)

Todos los bootstraps presentes y futuros **deben** cumplir:

### P1 — Orquestación vs ejecución
> El orquestador coordina; el especialista ejecuta. Tenant Bootstrap orquesta; Empresa Bootstrap ejecuta empresa; dominio ejecuta entidad.

### P2 — Session-driven
> Toda escritura bootstrap usa la `AsyncSession` del UoW caller. Prohibido abrir conexión paralela en la misma operación (lección F19 auth config).

### P3 — Idempotencia
> Toda operación bootstrap debe ser re-ejecutable sin duplicar filas (`ensure_*`, markers Dedicated, UNIQUE guards).

### P4 — Atomicidad preservada
> Onboarding inicial Shared permanece en **una TX**. Dedicated S7 preserva markers por sub-paso. No fragmentar commits visibles al usuario.

### P5 — Cero duplicación de metadatos
> Prefijos, padding, scope, sequence_key provienen de `SequenceCatalog`. Bootstraps no hardcodean metadatos funcionales.

### P6 — Scope explícito
> Cada bootstrap declara si opera en scope TENANT, EMPRESA o ENTIDAD. Filtra `cliente_id` siempre; `empresa_id` cuando aplique.

### P7 — No observable change
> Refactors internos no alteran contratos API, orden de artefactos resultantes, ni UX onboarding.

### P8 — Paridad Shared/Dedicated (semántica seed ERP)

> Misma **semántica de seed ERP** (roles, EMP001, admin, RBAC, cfg×57 en BD operativa); distinta **sesión física** (ADMIN vs dedicated DB). Facades V2 abstraen el transporte, no la lógica.

> **No confundir con paridad CP:** `cliente_auth_config` en Dedicated es deuda AS-IS (ADJ-07), fuera del alcance P8. Ver `06` §4.2.

### P9 — Extensión plug-in
> Nuevos bootstraps se **añaden** vía registry; no se editan Tenant/Empresa core salvo registro.

### P10 — Separación CP / DP

> Auth config y provisioning metadata viven en CP. Datos ERP operativos viven en tenant store (Shared=ADMIN único, Dedicated=BD tenant).

> **Excepción ADJ-07:** Dedicated no ejecuta T6 (`cliente_auth_config`) en S7 AS-IS. Es deuda técnica preexistente, no requisito Bootstrap V2 Fases 1–4. Cierre opcional en Fase 3 como fix de paridad CP independiente.

### P11 — Fail-closed
> Bootstrap incompleto → rollback TX o FAILED saga; no estados terminales parciales silenciosos.

### P12 — Verificabilidad
> Row expectations / audit snapshots verifican conteos mínimos post-bootstrap (preservar `tenant_seed_profiles` pattern).

---

## 4. BootstrapExtensionRegistry — diseño conceptual

| Campo | Descripción |
|-------|-------------|
| `extension_key` | `"warehouse"`, `"punto_venta"`, etc. |
| `scope` | `ENTITY` |
| `trigger_entity` | Tabla origen (`org_almacen`, …) |
| `handler` | Callable async `(session, BootstrapContext) → BootstrapResult` |
| `depends_on` | Prerequisitos (`empresa_bootstrap_complete`, módulo activo) |

**Registro:** en startup del módulo ERP o manifest estático versionado — decisión de implementación futura, no bloqueante para V2 core.

---

*Estrategia de implementación incremental: `05`.*
