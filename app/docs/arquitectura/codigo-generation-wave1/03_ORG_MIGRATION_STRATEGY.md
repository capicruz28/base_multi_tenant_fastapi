# Ola 1 — Estrategia de migración incremental ORG

**Estado:** Diseño — sin implementación  
**Fecha:** 2026-07-10  
**Motor:** Congelado (`app/core/codigo`)

---

## 1. Enfoque Strangler Fig

Migrar **una entidad a la vez**, manteniendo:

- Mismas rutas HTTP
- Mismo RBAC
- `AUTO_DEFAULT`: código manual sigue válido si el cliente lo envía
- Read schemas sin cambio
- Motor sin modificaciones

```
Fase 0 ── Auditoría (este documento)
Fase 1 ── Infra ORG: helper allocate + UoW company-scoped
Fase 2 ── org_cargo (piloto)
Fase 3 ── org_departamento
Fase 4 ── org_centro_costo
Fase 5 ── org_sucursal
Fase 6 ── org_empresa (+ plan EMP001)
Fase 7 ── Endurecimiento: optional-only UI, métricas, deprecación manual
```

---

## 2. Componentes a introducir (solo capa ORG)

> Diseño — no implementado en esta etapa.

### 2.1 Helper interno propuesto

Ubicación sugerida: `app/modules/org/application/services/org_codigo_service.py`

Responsabilidad única:

```text
resolve_codigo_for_create(
    sequence_key,
    *,
    session,
    client_id,
    empresa_id=None,
    manual_code=None,
) -> str
```

Implementación: delega en `CodigoGeneracionGateway.allocate()` construyendo `GenerationContext`.

**Prohibido:** llamar `AllocationCoordinator`, `seed_cfg_*`, o repos cfg directamente desde ORG.

### 2.2 UoW company-scoped

Replicar patrón de `create_empresa_servicio` (UoW-1):

- `get_connection_for_tenant(client_id, tenant_data)`
- `session.begin()`
- Dual-path en queries `create_*` + lookups pre-insert

**Entidades afectadas:** sucursal, centro_costo, departamento, cargo.

---

## 3. Plan por entidad

### 3.1 org_cargo (piloto — Fase 2)

| Aspecto | Acción |
|---------|--------|
| Gateway | `allocate("org_cargo", ...)` antes de INSERT |
| Schema | `CargoCreate.codigo` → Optional |
| Service | UoW + helper; pre-check solo si manual |
| Tests | Create sin codigo → formato CARnnn; manual → aceptado; rollback TX |
| Riesgo | **Bajo** |

### 3.2 org_departamento (Fase 3)

Igual patrón cargo. Atención FK opcionales en payload — no afectan allocate.

### 3.3 org_centro_costo (Fase 4)

| Extra | Detalle |
|-------|---------|
| Jerarquía | `ruta_jerarquica` puede derivarse del código padre — evaluar si se recalcula post-allocate |
| FK saliente | Sucursal puede referenciar CC — orden migración CC antes de sucursal ✓ |

### 3.4 org_sucursal (Fase 5)

| Extra | Detalle |
|-------|---------|
| FK entrada | `centro_costo_id` opcional — allocate independiente |
| Downstream | INV almacenes referencian sucursal — códigos motor no bloquean |

### 3.5 org_empresa (Fase 6 — última)

| Extra | Detalle |
|-------|---------|
| UoW | Ya existe |
| Bootstrap | `insertar_secuencias_codigo` permanece después de INSERT |
| Allocate | **Antes** de INSERT; ScopeType TENANT |
| EMP001 | Seed cfg `ultimo_numero=1` (BR-BOOT-04); ver §4 |
| Schema | `codigo_empresa` Optional |
| Riesgo | **Alto** |

---

## 4. Plan EMP001 / onboarding — **DECISIÓN CERRADA**

**Estado:** Normativa en Motor de Códigos (`BR-M-02`, `BR-BOOT-04`, `BS-CFG-02` excepción). **Sin ENSURE, sin repair runtime, sin guard en ORG create.**

| Decisión | Detalle |
|----------|---------|
| Bootstrap sede | `ensure_empresa_inicial` inserta `EMP001` (sin motor) — **sin cambio** |
| Seed cfg TENANT | `org_empresa` con **`ultimo_numero = 1`** al sembrar en onboarding |
| Runtime ORG | `allocate` estándar en `create_empresa_servicio`; primer auto = **`EMP002`** |
| Prohibido | `align_counter` en create, scripts ENSURE, repair post-onboarding (greenfield) |

**Implementación bootstrap:** override `ultimo_numero = 1` para `sequence_key = org_empresa` en seed onboarding (`onboarding_seed` / `cfg_codigo_onboarding_seed`). Ver `bootstrap/03_BOOTSTRAP_RULES.md` §2.1.

---

## 5. Evolución de contratos API (compatible)

### Fase transitoria (por entidad)

| Campo Create | Comportamiento |
|--------------|----------------|
| `codigo` omitido o null | AUTO_GENERATE vía gateway |
| `codigo` presente | ACCEPT_MANUAL + validación gateway + pre-check/UNIQUE |
| Response Read | Siempre incluye código final |

### OpenAPI

| Cambio | Breaking |
|--------|----------|
| Required → Optional en Create | **Sí** para validadores client estrictos |
| Nuevo query preview | No (aditivo, fase posterior) |

**Mitigación:** versionar release notes; frontend deja de enviar campo en mismo sprint.

---

## 6. Impacto frontend (documentación)

| Pantalla | Cambio |
|----------|--------|
| Alta cargo / dpto / CC / sucursal | Quitar input código; opcional badge «Se asignará automáticamente» |
| Alta empresa | Quitar `codigo_empresa`; mantener RUC |
| Edición | Mantener campo código editable (AUTO_DEFAULT) |
| Listados | Sin cambio |
| Búsqueda | Sin cambio |
| Manejo errores | Mostrar 422 `SEQUENCE_KEY_UNKNOWN`, validación formato motor |
| Preview UX | Consumir endpoint preview futuro (`CodigoGeneracionGateway.preview`) — nice-to-have |

---

## 7. Matriz de riesgos y mitigaciones

| ID | Riesgo | Fase | Mitigación |
|----|--------|------|------------|
| M-01 | allocate sin fila cfg | Todas | Verificar bootstrap; repair script tenants legacy |
| M-02 | TX parcial allocate+insert | 2–5 | UoW obligatorio |
| M-03 | Divergencia contador EMP001 | 6 | Seed cfg `ultimo_numero=1` (BR-BOOT-04) |
| M-04 | Breaking OpenAPI optional | 2+ | Release coordinado backend+frontend |
| M-05 | Códigos legacy no parseables | Transición | AUTO_DEFAULT manual path |
| M-06 | Regresión Dedicated | Todas | Gate F4-* + test allocate con tenant_data session |
| M-07 | Modificar motor por accidente | Todas | PR checklist: diff `app/core/codigo` vacío |

---

## 8. Criterios de aceptación por fase

### Gate común (cada entidad)

- [ ] CREATE sin código → gateway asigna prefijo catálogo
- [ ] CREATE con código manual válido → aceptado (AUTO_DEFAULT)
- [ ] CREATE duplicado → 409 (UNIQUE o ConflictError)
- [ ] UPDATE sin cambio de código → sin llamada allocate
- [ ] Rollback: fallo post-allocate pre-commit → sin fila persistida
- [ ] `app/core/codigo/**` sin diff
- [ ] Tests ORG existentes verdes + tests gateway entidad

### Gate org_empresa (adicional)

- [ ] allocate + INSERT + `insertar_secuencias_codigo` en un solo `begin()`
- [ ] Fallo cfg seed → rollback incluye empresa
- [ ] EMP002 auto sin colisión EMP001

---

## 9. Tests recomendados (plan — no implementados)

| ID | Test |
|----|------|
| T-ORG-CG-01 | Unit helper `resolve_codigo_for_create` mock gateway |
| T-ORG-CG-02 | Integration cargo create sin codigo → CAR001 pattern |
| T-ORG-CG-03 | Integration manual code alignment |
| T-ORG-CG-04 | Rollback allocate+insert |
| T-ORG-CG-05 | Empresa: allocate + bootstrap cfg TX |
| T-ORG-CG-06 | Regresión F17D / F4 Dedicated sin cambios motor |

---

## 10. Fuera de alcance Ola 1 ORG

| Item | Proyecto futuro |
|------|-----------------|
| `org_parametro_sistema` | N/A — fuera motor |
| Modo ENSURE / repair masivo | Solo si existieran tenants legacy (no aplica greenfield) |
| Endpoint HTTP preview global | Plataforma / shared API |
| INV movimiento AUTO_REQUIRED | Ola posterior (roadmap histórico F16) |
| Import histórico masivo | `GenerationOperation.IMPORT` |
| Cambios SequenceCatalog | Gobierno catálogo separado |
| Bootstrap sede vía motor (`allocate` EMP001) | Evolución Bootstrap V3 (opcional) |

---

## 11. Veredicto estrategia

La migración ORG es **viable sin tocar el motor** mediante:

1. Helper delgado → `CodigoGeneracionGateway`
2. UoW por entidad (empresa ya listo)
3. Strangler entidad por entidad cargo → empresa
4. AUTO_DEFAULT para convivencia manual

**Siguiente paso implementación:** Fase 1 infra ORG + Fase 2 piloto `org_cargo`.
