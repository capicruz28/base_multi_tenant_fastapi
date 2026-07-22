# Motor de Códigos — Impacto Bootstrap (generation_policy)

**Estado:** Diseño — sin implementación  
**Fecha:** 2026-07-11

---

## 1. Estado AS-IS del bootstrap cfg

### 1.1 Flujo actual

```
SequenceCatalog (incluye policy en defn — no persistida)
  → onboarding_seed.ONBOARDING_SEQUENCE_SEEDS
      (sequence_key, scope, prefijo, longitud, separador, contadores)
  → cfg_codigo_onboarding_seed._seed_cfg_rows
  → CfgCodigoSecuenciaRepository.insert_secuencia
  → cfg_codigo_secuencia (sin generation_policy)
```

### 1.2 Invocadores

| Flujo | Función | Filas aprox |
|-------|---------|-------------|
| **Bootstrap Tenant (Shared onboarding)** | `seed_cfg_tenant` + `seed_cfg_empresa` | 1 TENANT + 56 EMPRESA |
| **Empresa Bootstrap V1** | `seed_cfg_empresa` solamente | 56 EMPRESA por empresa nueva |
| **Dedicated S7** | `TenantBootstrapOrchestrator.run_seed_codigo_secuencias` | idem Shared |
| **Lazy runtime** | `CfgSequenceStore.ensure_row` | ALMACEN/PV bajo demanda |

### 1.3 DDL AS-IS (`V010`)

Columnas cfg relevantes: prefijo, separador, longitud_numero, ultimo_numero, numero_inicial, es_activo.  
**Sin** columna de política. **Sin** DEFAULT SQL para policy.

---

## 2. ¿Sembrar explícitamente vs DEFAULT SQL?

### 2.1 Veredicto: **sembrar explícitamente**

| Enfoque | Veredicto |
|---------|-----------|
| `DEFAULT 'AUTO_DEFAULT'` en DDL | **Rechazado como fuente de negocio** — oculta origen; F2 quedaría mal sembrado |
| NULL + fallback runtime catálogo | **Solo ventana migración** |
| **INSERT explícito en seed** desde catálogo | **Recomendado** |

### 2.2 Regla de semilla

```python
generation_policy = defn.default_generation_policy  # ex policy
```

Por fila:

| Familia catálogo | Valor sembrado |
|------------------|----------------|
| F1 maestros (ORG, INV cat, …) | `AUTO_DEFAULT` |
| F2 documentos (MOV, OC, …) | `AUTO_REQUIRED` |
| F4 WMS ALMACEN | `AUTO_DEFAULT` |

**Ejemplo explícito:** fila `inv_movimiento` → `generation_policy = 'AUTO_REQUIRED'`, **no** inferido por DEFAULT SQL genérico.

---

## 3. Cambios por capa bootstrap

### 3.1 DDL (futuro script — no implementar en esta tarea)

```sql
ALTER TABLE cfg_codigo_secuencia
  ADD generation_policy NVARCHAR(20) NOT NULL
  CONSTRAINT DF_cfg_generation_policy DEFAULT 'AUTO_DEFAULT'  -- solo migración
  CONSTRAINT CK_cfg_generation_policy CHECK (
    generation_policy IN ('AUTO_REQUIRED', 'AUTO_DEFAULT', 'MANUAL_ONLY')
  );
-- Post-backfill: opcional DROP DEFAULT
```

**Nota diseño:** DEFAULT temporal acelera ADD COLUMN en BD grandes; **seed siempre envía valor explícito** en código nuevo.

### 3.2 `OnboardingSequenceSeed`

| Campo nuevo | Fuente |
|-------------|--------|
| `generation_policy: CodePolicy` | `defn.default_generation_policy` |

### 3.3 `cfg_codigo_onboarding_seed`

Sin cambio estructural — propaga seed al repo.

### 3.4 `CfgCodigoSecuenciaRepository.insert_secuencia`

| Cambio | Detalle |
|--------|---------|
| Nuevo param | `generation_policy: CodePolicy` |
| VALUES dict | Incluir columna |

### 3.5 `CfgSequenceStore.ensure_row` (lazy)

Copiar `generation_policy=defn.default_generation_policy` en INSERT lazy.

---

## 4. Impacto por flujo bootstrap

### 4.1 Bootstrap Tenant (onboarding inicial)

| Aspecto | Impacto |
|---------|---------|
| `TenantBootstrapOrchestrator.run_seed_codigo_secuencias` | Sin cambio firma |
| Conteo filas | Sin cambio (57 resoluble eager) |
| Contenido filas | +1 columna policy por fila |
| Tests F17D | Assert policy en inserts mock |

### 4.2 Bootstrap Empresa (Empresa Bootstrap V1)

| Aspecto | Impacto |
|---------|---------|
| `EmpresaBootstrapService.insertar_secuencias_codigo` | Sin cambio firma |
| 56 filas EMPRESA | Cada una con policy desde catálogo |
| UoW ORG create empresa | Sin cambio flujo |

### 4.3 Dedicated provisioning

| Aspecto | Impacto |
|---------|---------|
| Adapters S7 | Sin cambio — delegan TBO |
| Row expectations | Sin cambio conteo |
| Policy en BD dedicada | Mismo seed path |

### 4.4 Bootstrap V2 scripts SQL

| Artefacto | Impacto |
|-----------|---------|
| `V010__tablas_bd_erp_completo.sql` | **Futuro** V0xx ALTER — no editar V010 retroactivamente en impl |
| Seeds SQL estáticos | **No existen** para cfg — todo Python |

---

## 5. Backfill tenants existentes

### 5.1 Script repair propuesto (diseño)

```
repair_cfg_generation_policy:
  FOR each row cfg WHERE generation_policy IS NULL (migración)
    SET generation_policy = SequenceCatalog.get(row.sequence_key).default_generation_policy
```

### 5.2 Validación post-backfill

| Check | Expectativa |
|-------|-------------|
| NULL policy | 0 filas |
| F2 keys | 100% AUTO_REQUIRED |
| F1 ORG keys | 100% AUTO_DEFAULT |
| Conteo total cfg | Sin cambio |

---

## 6. Riesgos bootstrap

| ID | Riesgo | Mitigación |
|----|--------|------------|
| B-01 | Seed omit policy en una fila | Test F17D + contract seed |
| B-02 | EMP002 sin policy (EBS V1) | Actualizar repo insert |
| B-03 | Lazy row sin policy | ensure_row obligatorio |
| B-04 | Dedicated tenant sin backfill | Repair en activación |
| B-05 | Divergencia F2 sembrado AUTO_DEFAULT por bug | Assert por familia en test |

---

## 7. Qué NO cambia en bootstrap

| Componente | Estado |
|------------|--------|
| `TenantBootstrapOrchestrator` secuencia | Sin cambio |
| `ClienteOnboardingService` | Sin cambio |
| `EmpresaBootstrapService` API | Sin cambio |
| Conteo 57 / 56 filas | Sin cambio |
| `ONBOARDING_RESOLVABLE_SCOPES` | Sin cambio |
| SequenceCatalog keys | Sin cambio |

---

## 8. Veredicto bootstrap

**Sembrar `generation_policy` explícitamente** en Python seed desde `default_generation_policy` del catálogo.  
**No depender** de DEFAULT SQL para distinguir F1 vs F2.  
Backfill obligatorio para tenants existentes antes de Ola 1 ORG runtime.
