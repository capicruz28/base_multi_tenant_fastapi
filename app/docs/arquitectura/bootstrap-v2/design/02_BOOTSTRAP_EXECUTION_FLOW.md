# 02 — Bootstrap V2: Flujo oficial de ejecución

**Etapa:** Diseño TO-BE  
**Garantía:** orden y resultado **idénticos** al AS-IS observable.

---

## 1. Flujo Platform (sin cambio observable)

```
Instalación (manual, 1×)
│
├── Fase SQL: bootstrap_v2 V010→V030, S010→S020
│
├── Fase Startup: permission_sync (cada arranque app)
│
└── Fase CLI: bootstrap_platform.py --apply
         │
         ▼
    PlatformBootstrapService.bootstrap
         ├── PlatformIdentityBootstrapService (cliente/rol/usuario/auth platform)
         └── PlatformRbacBootstrapService (SYS_ADMIN, grants CP)
```

**Frecuencia:** Platform una vez; startup cada arranque. **No interviene** en `POST /clientes`.

---

## 2. Flujo Tenant Shared — orden oficial V2

**Entry:** `POST /clientes/` → `ClienteService.crear_cliente` → **Tenant Bootstrap Orchestrator**  
**TX:** una sola transacción ADMIN (preservada)

```
Tenant Bootstrap Orchestrator
│
├── [T1]  Crear cliente                    ← Tenant scope
├── [T2]  Crear roles base                 ← Tenant scope
│
├── [E-PHASE] ──► Empresa Bootstrap (interno, automático)
│       ├── [E1] Crear org_empresa EMP001
│       ├── [E2] (reservado) artefactos empresa futuros
│       └── retorna empresa_id
│
├── [T3]  Crear usuario admin              ← Tenant scope (usa empresa_id de E1)
├── [T4]  Vincular admin ↔ empresa         ← invoca Empresa Bootstrap (preferencia)
├── [T5]  RBAC tenant (plan + bundles)     ← Tenant scope
├── [T6]  Auth config                      ← Tenant scope
├── [T7]  Secuencias CFG TENANT (1 fila)   ← Tenant scope
│
└── [E-PHASE-2] ──► Empresa Bootstrap (cfg EMPRESA)
        └── [E3] Secuencias CFG EMPRESA (56 filas)
```

**Nota de diseño:** en implementación, E1/E3/E4 (vínculo) pueden agruparse en una o dos invocaciones internas a `EmpresaBootstrapService`; el **orden observable** y las **tablas resultantes** deben coincedir con AS-IS.

### Equivalencia AS-IS → V2 (Shared)

| Paso observable AS-IS | Capa V2 | Código AS-IS (referencia) |
|----------------------|---------|---------------------------|
| 1. Cliente | Tenant T1 | `_insertar_cliente` |
| 2. Roles | Tenant T2 | `_insertar_roles_base` |
| 3. Empresa EMP001 | Empresa E1 | `ensure_empresa_inicial` |
| 4. Admin | Tenant T3 | `_insertar_usuario_admin` |
| 5. Vínculo admin | Empresa (preferencia) | `vincular_admin_empresa` |
| 6. RBAC | Tenant T5 | `bootstrap_cliente_rbac` |
| 7. Auth config | Tenant T6 | `_insertar_auth_config_si_no_existe` |
| 8. cfg ×57 | Tenant T7 + Empresa E3 | `_insertar_secuencias_codigo` |

**El paso 8 AS-IS se divide internamente** en T7 (1 TENANT) + E3 (56 EMPRESA) sin cambiar filas totales ni orden de commits.

---

## 3. Flujo Tenant Dedicated — orden oficial V2

**Entry:** `POST /clientes/` (dedicated) → CP `cliente` + saga S1–S10  
**Tenant Bootstrap efectivo:** S7 `DedicatedTenantSeedService`

```
Saga Dedicated (sin cambio de steps públicos S1–S10)
│
├── S1–S3: registry, allocation, create_database
├── S4/S5: schema DDL (tablas vacías)
├── S6: catálogos SQL (permiso, modulo_menu)
│
├── S7: Tenant Bootstrap Orchestrator (Dedicated)
│       │
│       ├── sub-paso 1: roles base              [T2]
│       ├── sub-paso 2: ──► Empresa Bootstrap   [E1]
│       ├── sub-paso 3: admin user              [T3]
│       ├── sub-paso 4: ──► Empresa Bootstrap   [vínculo]
│       ├── sub-paso 5: RBAC                    [T5]
│       └── sub-paso 6: cfg (T7 + E3)           [T7 + E3]
│       │
│       └── (deuda AS-IS, fuera V2 core) auth config CP  [T6] — ADJ-07; ver `06` §4.2
│
├── S8–S10: metadata, routing, mark_ready
```

**Markers S7:** los `step_code` AS-IS (`seed_org_empresa`, etc.) pueden **mapear internamente** a invocaciones Empresa Bootstrap sin cambiar nombres de marker en fase incremental (ver `05`).

---

## 4. Comunicación Tenant ↔ Empresa Bootstrap

### 4.1 Contrato conceptual (interno)

```
EmpresaBootstrapService.bootstrap_empresa(
    session,                    # misma sesión que Tenant (TX compartida)
    cliente_id,
    empresa_input,              # datos para crear org_empresa (ClienteCreate en 1ª)
    options: EmpresaBootstrapOptions
) → EmpresaBootstrapResult {
    empresa_id,
    codigo_empresa,
    created: bool,
    cfg_seeded: bool,
    admin_linked: bool,
}
```

### 4.2 Reglas de comunicación

| Regla | Descripción |
|-------|-------------|
| C-01 | Tenant Bootstrap **siempre** posee la sesión/transacción |
| C-02 | Empresa Bootstrap **nunca** abre conexión propia |
| C-03 | Empresa Bootstrap **nunca** es invocado desde API pública directamente en onboarding |
| C-04 | Retorno mínimo: `empresa_id` para pasos tenant subsiguientes |
| C-05 | Idempotencia: misma semántica AS-IS (`_get_primera_empresa_activa` en re-ejecución) |
| C-06 | Dedicated: mismas reglas sobre `provisioning_dedicated_session` |

### 4.3 Invocaciones en onboarding inicial

| Momento | Invocación Empresa Bootstrap | Operación |
|---------|------------------------------|-----------|
| Tras roles base | `bootstrap_empresa_create` | E1: org_empresa |
| Tras admin creado | `bootstrap_empresa_link_admin` | preferencia default |
| Tras auth config (Shared) / antes de commit | `bootstrap_empresa_cfg_sequences` | E3: 56 filas |

En implementación incremental, estas tres operaciones pueden ser **un solo método** con fases internas; el diseño las separa para claridad y multi-empresa futura.

---

## 5. Orden oficial consolidado (respuesta pregunta 8)

**Secuencia normativa V2 (observable = AS-IS):**

1. Cliente  
2. Roles  
3. **Empresa (EMP001)** — Empresa Bootstrap, invocado por Tenant  
4. Usuario admin  
5. Vínculo admin ↔ empresa — Empresa Bootstrap  
6. RBAC  
7. Auth config (Shared)  
8. Configuraciones iniciales (1 cfg TENANT + 56 cfg EMPRESA)  

**Prohibido en diseño:** invertir 3 y 4; omitir 3; exponer 3 como paso manual usuario.

### 5.1 Invariante INV-01 — orden E1 antes T3 (obligatorio)

```
EmpresaBootstrap(E1)   ← org_empresa EMP001
        ↓
Usuario Admin (T3)     ← requiere empresa_id de E1
```

| Regla | Descripción |
|-------|-------------|
| INV-01 | **E1 siempre precede T3.** El admin se crea con contexto de empresa existente. |
| INV-01-P | **Prohibido** invertir E1 y T3 en Shared, Dedicated S7, o cualquier refactor V2. |
| INV-01-R | Violación → FK/scope inválido, admin sin `empresa_default_id`, regresión R-T5. |
| INV-01-V | Verificable: paso 3 AS-IS (`ensure_empresa_inicial`) antes paso 4 (`_insertar_usuario_admin`). |

Este invariante es **normativo** y no admite excepción en Bootstrap V2.

---

## 6. Multi-empresa futura (flujo adicional, fuera onboarding inicial)

```
POST /org/empresas/  (futuro — módulo ORG, fuera alcance implementación)
    │
    └── ORG Service
            └── Empresa Bootstrap.bootstrap_empresa(...)   # empresa N>1
                    ├── org_empresa
                    └── cfg EMPRESA ×56
```

**Tenant Bootstrap no se re-ejecuta.** Solo Empresa Bootstrap para la nueva `empresa_id`.

---

*Responsabilidades detalladas: `03`. Extensiones: `04`.*
