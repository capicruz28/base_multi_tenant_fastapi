# F17A — Reglas de bootstrap de `cfg_codigo_secuencia`

**Fase:** F17A — Bootstrap oficial
**Fecha:** 2026-07-03
**Base:** F16 `13`/`14`, F17 Ola 0 (implementación existente), `01`/`02` de esta fase

> Reglas de comportamiento para poblar `cfg_codigo_secuencia` en onboarding y en operación. **No** introduce código nuevo; describe el estándar que el seed y el motor ya deben respetar.

---

## 1. Modelo de poblado: eager + lazy (híbrido)

CAXIS usa una estrategia **híbrida** ya implementada en F17 Ola 0:

| Estrategia | Cuándo | Qué crea |
|------------|--------|----------|
| **Eager (seed onboarding)** | Al crear el tenant / primera empresa | Núcleo operativo mínimo |
| **Lazy creation** | En el primer `allocate` de un `sequence_key`+scope sin fila | Resto de secuencias, con defaults del catálogo |

**Regla BR-BOOT-01:** ninguna operación falla por ausencia de fila cfg; `AllocationCoordinator.ensure_row` la crea con los defaults del `SequenceCatalog` dentro de la misma UoW.

---

## 2. Núcleo eager (seed de onboarding) — criterio F17D

**Criterio oficial (F17D):** el onboarding siembra **todas** las secuencias de store CFG cuyo `scope_fingerprint` se resuelve por completo en onboarding — es decir, scope **TENANT** o **EMPRESA** (existe cliente + empresa sede). La selección **se deriva automáticamente** del `SequenceCatalog` en `app/core/codigo/onboarding_seed.py` (`ONBOARDING_SEQUENCE_SEEDS`): no hay lista manual de keys ni número fijo en el código.

| Grupo | scope | Filas creadas en onboarding (empresa sede) |
|-------|-------|--------------------------------------------|
| `org_empresa` | TENANT | 1 (fingerprint TENANT) |
| Resto de CFG con scope EMPRESA | EMPRESA | 56 (empresa sede, `empresa_id` no nulo) |
| `wms_*`, `pos_turno_caja` (scope ALMACEN/PUNTO_VENTA) | ALMACEN / PUNTO_VENTA | **0 en onboarding** → lazy |

**Total eager onboarding = 57 filas para una empresa** (1 TENANT + 56 EMPRESA), **derivado** del catálogo (store CFG + scope ∈ {TENANT, EMPRESA}). Coincide con `tenant_seed_profiles._row_expectations_for_profile` (`cfg_codigo_secuencia` = `len(EAGER_SEQUENCE_KEYS)`), que también se deriva del catálogo.

**Regla BR-BOOT-02 (F17D):** el núcleo eager cubre **todas** las CFG de scope resoluble. Las **4** secuencias CFG de scope **ALMACEN/PUNTO_VENTA** (`wms_zona_almacen`, `wms_ubicacion`, `wms_tarea`, `pos_turno_caja`) **no** se siembran en onboarding: su fingerprint requiere una entidad (almacén / punto de venta) inexistente en esa fase y se crean lazy vía `ensure_row` (§5).

**Regla BR-BOOT-03 (INC-01/INC-02, ya corregidas en F17):**
- `org_empresa` → scope **TENANT** (`empresa_id = NULL`).
- Las restantes EMPRESA-scoped → scope **EMPRESA** con `empresa_id` de la **empresa sede** (nunca `NULL`).
- `inv_categoria_producto` (no `inv_categoria`).

### 2.1 `org_empresa` TENANT — contador inicial post-EMP001 (BR-BOOT-04)

**Decisión normativa (greenfield):** el bootstrap de la empresa sede y el seed cfg TENANT deben dejar el contador **consistente** sin repair runtime.

| Paso onboarding | Comportamiento |
|-----------------|----------------|
| `ensure_empresa_inicial` | INSERT `org_empresa` con `codigo_empresa = EMP001` (SQL directo, sin motor) |
| `seed_cfg_tenant` | INSERT fila cfg `sequence_key=org_empresa`, scope TENANT, **`ultimo_numero = 1`** |
| Primer `allocate` runtime ORG | Emite **`EMP002`** (`max(1,0)+1`) |

**Regla BR-BOOT-04:** tras existir EMP001 en `org_empresa`, el seed cfg TENANT `org_empresa` **debe** persistir `ultimo_numero = 1`. Es la **única** excepción a INV-BOOT-04. Implementación: derivar `ultimo_numero = 1` en el seed de onboarding para `sequence_key = org_empresa` (p. ej. override en `OnboardingSequenceSeed.from_definition` o equivalente en `cfg_codigo_onboarding_seed`).

**Prohibido en despliegue greenfield:**

- Scripts ENSURE o repair post-onboarding para el contador TENANT.
- `CodigoGeneracionGateway.align_counter` en `create_empresa_servicio` u otro path ORG rutinario.
- Sembrar `org_empresa` con `ultimo_numero = 0` cuando EMP001 ya existe.

**Preferencia arquitectónica:** inicializar `ultimo_numero = 1` **directamente en el insert del seed** (no vía `align_counter`). El bootstrap es el punto autorizado de estado inicial cfg; `align_counter` queda para importación/manual alto (Gateway §5.4).

**Referencias cruzadas:** BR-M-02 (`07_BUSINESS_RULES.md`), BS-CFG-02 excepción (`01`), EX-01 (`25_EXCEPTION_ANALYSIS.md`).

---

## 3. Comportamiento Shared

| Aspecto | Regla |
|---------|-------|
| Ubicación física | `cfg_codigo_secuencia` en la BD central (control plane / `DatabaseConnection.ADMIN`) |
| Aislamiento | Todas las filas filtradas por `cliente_id`; unicidad `(cliente_id, sequence_key, scope_fingerprint)` |
| Seed onboarding | `ClienteOnboardingService._insertar_secuencias_codigo(session, cliente_id, empresa_id)` en la misma TX del onboarding |
| Lazy | El motor crea filas bajo el `cliente_id` del contexto de sesión ERP |
| Contención | Una fila por (`sequence_key`, scope) del tenant; aceptable (F16 R-01) |

**Regla BR-SHARED-01:** en Shared, dos tenants **nunca** comparten fila; el `cliente_id` es parte de la unicidad y de todo filtro.

---

## 4. Comportamiento Dedicated

| Aspecto | Regla |
|---------|-------|
| Ubicación física | `cfg_codigo_secuencia` en la **BD dedicada** del tenant (tabla requerida de runtime dedicado) |
| Seed onboarding | `dedicated_tenant_seed_adapters` paso `seed_codigo_secuencias` → mismo `_insertar_secuencias_codigo(session, cliente_id, empresa_id)` |
| Aislamiento | Físico (BD propia); las filas igualmente llevan `cliente_id` |
| Lazy | Idéntico a Shared, resuelto por el operation store del tenant (TA-06) |
| Prohibición | **No** dual-write: cfg vive solo en el store del tenant, nunca duplicado en central (F16 R-08) |

**Regla BR-DED-01:** el comportamiento funcional (prefijos, padding, lazy, high-water) es **idéntico** en Shared y Dedicated. La única diferencia es la ubicación física del store.

**Regla BR-DED-02:** el paso `seed_codigo_secuencias` exige `empresa_id` de la empresa sede ya creada (prerrequisito validado en el adaptador dedicado).

---

## 5. Lazy creation (detalle)

| Escenario | Comportamiento |
|-----------|----------------|
| Primer `allocate` de un `sequence_key`+scope sin fila | Se crea fila con defaults del catálogo (`prefijo`, `separador`, `longitud_numero`, `numero_inicial`, `ultimo_numero=0`) |
| Nueva empresa en el tenant | Las secuencias EMPRESA-scoped se crean lazy por empresa al primer uso (fingerprint distinto por `empresa_id`) |
| Nuevo almacén | Secuencias ALMACEN-scoped (`wms_*`) se crean lazy por `almacen_id` |
| Nuevo punto de venta | `pos_turno_caja` se crea lazy por `punto_venta_id` |

**Regla BR-LAZY-01:** el fingerprint (`scope_fingerprint`) garantiza una fila por combinación de scope; el lazy nunca colisiona ni duplica.

**Regla BR-LAZY-02:** el lazy usa **exactamente** los defaults del catálogo vigente. Si el catálogo cambió un default (nueva versión), las filas ya existentes **no** se alteran; solo las nuevas nacen con el nuevo default.

---

## 6. Multiempresa

| Situación | Filas cfg resultantes |
|-----------|-----------------------|
| Tenant con 1 empresa | 1 fila TENANT (`org_empresa`) + N filas EMPRESA de esa empresa |
| Tenant con M empresas | 1 fila TENANT compartida + N filas EMPRESA **por cada** empresa |
| `org_empresa` | **Una sola** secuencia TENANT para todo el tenant (numera todas las empresas) |

**Regla BR-MULTI-01:** `org_empresa` es la única secuencia TENANT; su contador es común a todas las empresas del tenant (la empresa es entidad raíz, no hija de otra empresa).

**Regla BR-MULTI-02:** cada empresa adicional obtiene su propio juego de contadores EMPRESA-scoped, independientes entre empresas (aislamiento de numeración por empresa legal).

---

## 7. Fiscal (fuera de `cfg_codigo_secuencia`)

| Aspecto | Regla |
|---------|-------|
| Store | `invbill_serie_comprobante` (`numero_actual` por `serie_id`) |
| Alta de serie | **MANUAL_ONLY** — el cliente registra series autorizadas SUNAT (`F001`, `B001`, …) |
| Seed automático | **Ninguno** — no se pre-crean series en onboarding (dependen de autorización legal del tenant) |
| Numeración | AUTO_REQUIRED en emisión: `invbill_comprobante.numero` a 8 dígitos vía `FiscalSeriesStore` |
| `log_guia_remision` | Pendiente store de serie (INC-10 / GAP-P1-01, Ola 4) |

**Regla BR-FISCAL-01:** el bootstrap de `cfg_codigo_secuencia` **no** incluye las 2 entradas F3. La configuración fiscal se realiza por el cliente al dar de alta sus series autorizadas.

---

## 8. Actualización futura del estándar

| Cambio | Efecto en tenants existentes | Efecto en tenants nuevos |
|--------|------------------------------|--------------------------|
| Nuevo `sequence_key` CFG con scope TENANT/EMPRESA | Ninguno hasta primer uso (lazy) | **Se siembra automáticamente** en onboarding (derivado del catálogo, F17D) |
| Nuevo `sequence_key` CFG con scope ALMACEN/PUNTO_VENTA | Ninguno hasta primer uso (lazy) | Lazy por entidad (no eager) |
| Cambio de default de prefijo/padding | **Ninguno** en filas existentes | Aplica a filas nuevas |
| Cambio de policy/scope/family | **Prohibido** sin enmienda F15A/F16A (gobernanza `22`) | — |

**Regla BR-UPD-01:** modificar defaults es **compatible hacia atrás** por diseño: las filas ya emitidas conservan su configuración; solo cambian las nuevas.

**Regla BR-UPD-02:** cualquier cambio de `policy`, `scope` o `family` exige versión mayor del catálogo y proceso de gobernanza (`22`), nunca un ajuste de seed.

---

## 9. Personalización por cliente

| Nivel | Alcance |
|-------|---------|
| Pre-onboarding (Dedicated) | El proyecto de implantación puede pre-cargar filas cfg con prefijos corporativos antes del go-live |
| Post-onboarding (admin, Ola 6) | Editar `prefijo`, `separador`, `longitud_numero`, `numero_inicial`, `es_activo` por fila |
| Restricción | No editar `policy`, `scope_type`, `sequence_family`, `scope_fingerprint` |

**Regla BR-CUST-01:** toda personalización valida que `numero_inicial`/`longitud_numero` no generen colisión con códigos ya emitidos (anti-colisión F16 `15` §5).

**Regla BR-CUST-02:** desactivar una secuencia (`es_activo = 0`) bloquea nuevos `allocate` (→ `ConflictError` secuencia inactiva); no elimina la fila (soft-disable, TD-M-04).

---

## 10. Invariantes de integridad del bootstrap

| ID | Invariante |
|----|-----------|
| INV-BOOT-01 | Toda fila tiene `scope_type` ∈ {TENANT, EMPRESA, ALMACEN, PUNTO_VENTA} y `scope_fingerprint` coherente |
| INV-BOOT-02 | `org_empresa` siempre TENANT (`empresa_id = NULL`) |
| INV-BOOT-03 | Entradas EMPRESA-scoped nunca con `empresa_id = NULL` |
| INV-BOOT-04 | `ultimo_numero = 0` y `numero_inicial ≥ 1` en toda fila recién sembrada **salvo** `org_empresa` TENANT con EMP001 ya persistido (`ultimo_numero = 1`; BR-BOOT-04) |
| INV-BOOT-05 | Sin filas para `sequence_key` fiscal (F3) en `cfg_codigo_secuencia` |
| INV-BOOT-06 | Unicidad `(cliente_id, sequence_key, scope_fingerprint)` siempre respetada |
| INV-BOOT-07 | Seed idempotente: re-ejecutar no duplica filas |

---

*Configuración en `01`. Prefijos en `02`. Plan de generación del seed en `04`.*
