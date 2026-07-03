# F16 — Modelo de secuencia (`cfg_codigo_secuencia`)

**Fase:** F16 — Diseño técnico  
**Fecha:** 2026-07-03  
**Importante:** Documenta el diseño definitivo. **No modifica V010 ni ORM en esta fase.**

---

## 1. Veredicto sobre estructura actual

### 1.1 Columnas actuales (V010)

| Columna | Tipo actual | ¿Suficiente? |
|---------|-------------|--------------|
| `secuencia_id` | UNIQUEIDENTIFIER PK | ✅ Mantener |
| `cliente_id` | UNIQUEIDENTIFIER NOT NULL | ✅ Mantener |
| `empresa_id` | UNIQUEIDENTIFIER NULL | ⚠️ Insuficiente solo |
| `entidad` | NVARCHAR(50) | ⚠️ Renombrar a `sequence_key` |
| `prefijo` | NVARCHAR(5) | ❌ Longitud insuficiente |
| `longitud_numero` | INT DEFAULT 3 | ✅ Mantener |
| `ultimo_numero` | INT DEFAULT 0 | ✅ Mantener |
| `separador` | NVARCHAR(2) | ✅ Mantener |
| `es_activo` | BIT DEFAULT 1 | ✅ Mantener |

### 1.2 UNIQUE actual

```
UNIQUE (cliente_id, empresa_id, entidad)
```

**Insuficiente** para T3 (almacén), T4 (punto venta) y para distinguir múltiples secuencias empresa-scoped con misma tabla en escenarios futuros.

### 1.3 Conclusión

La tabla actual es **base válida** para prototipo onboarding pero **requiere evolución** antes de producción multi-scope. La familia **F3 fiscal** no debe sobrecargar esta tabla; usa `invbill_serie_comprobante`.

---

## 2. Diseño definitivo propuesto

### 2.1 Columnas

| Columna | Tipo propuesto | Nullable | Descripción |
|---------|----------------|----------|-------------|
| `secuencia_id` | UNIQUEIDENTIFIER | NOT NULL PK | Identificador fila |
| `cliente_id` | UNIQUEIDENTIFIER | NOT NULL | Tenant |
| `sequence_key` | NVARCHAR(64) | NOT NULL | Catálogo oficial (ex `entidad`) |
| `scope_type` | NVARCHAR(20) | NOT NULL | `TENANT`, `EMPRESA`, `ALMACEN`, `PUNTO_VENTA` |
| `empresa_id` | UNIQUEIDENTIFIER | NULL | Obligatorio lógico si scope requiere |
| `almacen_id` | UNIQUEIDENTIFIER | NULL | Obligatorio lógico si ALMACEN |
| `punto_venta_id` | UNIQUEIDENTIFIER | NULL | Obligatorio lógico si PUNTO_VENTA |
| `prefijo` | NVARCHAR(10) | NOT NULL | Ampliado desde 5 (ej. `INV-AJUS` prohibido en estándar pero margen) |
| `separador` | NVARCHAR(2) | NULL | `''` o `-` |
| `longitud_numero` | INT | NOT NULL DEFAULT 3 | Padding numérico |
| `ultimo_numero` | INT | NOT NULL DEFAULT 0 | High-water consumido |
| `numero_inicial` | INT | NOT NULL DEFAULT 1 | Primer número a asignar (admin) |
| `es_activo` | BIT | NOT NULL DEFAULT 1 | |
| `fecha_creacion` | DATETIME | NOT NULL | Auditoría |
| `fecha_actualizacion` | DATETIME | NULL | Auditoría |
| `usuario_actualizacion_id` | UNIQUEIDENTIFIER | NULL | Auditoría admin |

### 2.2 Columnas explícitamente excluidas

| Columna candidata | Por qué no |
|-------------------|------------|
| `politica` | Vive en SequenceCatalog (inmutable por tenant) |
| `modulo_codigo` | Redundante con `sequence_key` |
| `tabla_origen` | Redundante con `sequence_key` |
| `codigo_column` | Vive en catálogo |
| `serie_id` | Solo en store fiscal |
| `año_fiscal` | Reinicio anual no es estándar F15A |

### 2.3 Restricciones

| Constraint | Definición |
|------------|------------|
| **PK** | `secuencia_id` |
| **UQ cfg scope** | `UNIQUE (cliente_id, sequence_key, scope_type, empresa_id, almacen_id, punto_venta_id)` con semántica NULL: en SQL Server usar **filtered unique indexes** o **scope_fingerprint** (ver §2.4) |
| **CK scope** | Check: dimensiones coherentes con `scope_type` |
| **CK prefijo** | `LEN(prefijo) >= 1` |
| **CK numeros** | `ultimo_numero >= 0`, `numero_inicial >= 1`, `longitud_numero BETWEEN 1 AND 12` |
| **FK cliente_id** | → `cliente` (si cfg en central) o validación app (dedicated) |
| **FK empresa_id** | → `org_empresa` cuando NOT NULL |
| **FK almacen_id** | → `inv_almacen` cuando NOT NULL |
| **FK punto_venta_id** | → `pos_punto_venta` cuando NOT NULL |

### 2.4 Problema UNIQUE con NULL y solución recomendada

SQL Server: múltiples NULL en UNIQUE tradicional no garantizan unicidad deseada.

**Decisión TD-M-01:** añadir columna **`scope_fingerprint`** CHAR(64) NOT NULL:

- Hash determinista de `(scope_type, empresa_id, almacen_id, punto_venta_id)` con sentinels para nulls.
- **UNIQUE (cliente_id, sequence_key, scope_fingerprint)**.

Alternativa equivalente: índices únicos filtrados por combinación de scope_type (más verboso).

### 2.5 Índices

| Índice | Columnas | Propósito |
|--------|----------|-----------|
| `PK_cfg_codigo_secuencia` | `secuencia_id` | PK |
| `UQ_cfg_scope` | `cliente_id`, `sequence_key`, `scope_fingerprint` | Unicidad |
| `IDX_cfg_cliente_activo` | `cliente_id`, `es_activo` | Listado admin |
| `IDX_cfg_empresa` | `cliente_id`, `empresa_id`, `sequence_key` | Resolución empresa |
| `IDX_cfg_almacen` | `cliente_id`, `almacen_id`, `sequence_key` | WMS |

---

## 3. Mapeo scope → columnas pobladas

| scope_type | empresa_id | almacen_id | punto_venta_id |
|------------|------------|------------|----------------|
| TENANT | NULL | NULL | NULL |
| EMPRESA | NOT NULL | NULL | NULL |
| ALMACEN | NULL* | NOT NULL | NULL |
| PUNTO_VENTA | NOT NULL | NULL | NOT NULL |

\* `empresa_id` opcional denormalizado en ALMACEN para consultas; no participa en fingerprint si no está en ScopeKey F16.

---

## 4. Defaults por sequence_key (catálogo seed)

Reemplaza `SECUENCIAS_CODIGO` onboarding. Valores iniciales **documentados** (no código):

| sequence_key | scope_type | prefijo | longitud | separador | ultimo_inicial |
|--------------|------------|---------|----------|-----------|----------------|
| `org_empresa` | TENANT | EMP | 3 | — | 0 |
| `org_sucursal` | EMPRESA | SUC | 3 | — | 0 |
| `org_departamento` | EMPRESA | DEP | 3 | — | 0 |
| `org_cargo` | EMPRESA | CAR | 3 | — | 0 |
| `org_centro_costo` | EMPRESA | CC | 3 | — | 0 |
| `inv_almacen` | EMPRESA | ALM | 3 | — | 0 |
| `inv_producto` | EMPRESA | P | 5 | — | 0 |
| `inv_categoria_producto` | EMPRESA | CAT | 3 | — | 0 |
| `inv_movimiento` | EMPRESA | MOV | 6 | — | 0 |

**Corrección obligatoria:** `inv_categoria` → `inv_categoria_producto`; seeds empresa-scoped con `empresa_id` de empresa sede, no NULL (excepto `org_empresa` TENANT).

---

## 5. Store fiscal (fuera de cfg)

`invbill_serie_comprobante` permanece como contador F3:

| Campo fiscal | Rol |
|--------------|-----|
| `serie_id` | PK lógico ScopeKey SERIE_FISCAL |
| `numero_actual` | Equivalente `ultimo_numero` |
| `numero_inicial`, `numero_final` | Límites legales |
| `tipo_comprobante`, `serie` | Identificación humana |

No duplicar en cfg. FiscalSeriesStore abstrae esta tabla.

---

## 6. Naming oficial

| Concepto | Nombre BD | Nombre código |
|----------|-----------|---------------|
| Tabla | `cfg_codigo_secuencia` | — |
| Clave catálogo | `sequence_key` | `sequence_key` |
| Columna legacy | `entidad` | Deprecada → alias temporal |

---

## 7. Nullable y integridad

| Regla | Descripción |
|-------|-------------|
| TD-M-02 | `scope_type` nunca NULL |
| TD-M-03 | Si `scope_type=EMPRESA`, fingerprint debe incluir `empresa_id` real |
| TD-M-04 | Soft-disable vía `es_activo=0`; fila histórica se conserva |
| TD-M-05 | DELETE físico prohibido (estándar ERP) |

---

## 8. Extensiones futuras sin rediseño

| Necesidad | Extensión |
|-----------|-----------|
| Nuevo módulo ERP | Nueva `sequence_key` + filas cfg |
| Nuevo scope_type | Columna dimensión + fingerprint |
| Padding variable por longitud columna destino | Campo catálogo `max_output_length` |
| Secuencia por periodo | Tabla hija `cfg_codigo_secuencia_periodo` (fuera V1) |

---

## 9. Comparativa AS-IS → TO-BE

| Aspecto | V010 actual | Diseño F16 |
|---------|-------------|------------|
| Scope almacén | No soportado | `almacen_id` + scope_type |
| Scope PV | No soportado | `punto_venta_id` |
| UNIQUE | 3 columnas | fingerprint 3D |
| Prefijo max | 5 | 10 |
| Naming | `entidad` | `sequence_key` |
| numero_inicial | Implícito 1 | Explícito |
| Auditoría | No | Sí |
| Fiscal | Mezclado conceptualmente | Store separado |

---

## 10. Migración de datos (plan conceptual, no ejecutar)

| Paso | Acción |
|------|--------|
| 1 | DDL nueva versión bootstrap (V0xx, fuera de esta fase) |
| 2 | Renombrar `entidad` → `sequence_key` |
| 3 | Poblar `scope_type`, `scope_fingerprint` desde reglas F16 |
| 4 | Dividir filas seed incorrectas (NULL empresa) en filas por empresa sede |
| 5 | Renombrar `inv_categoria` → `inv_categoria_producto` |
| 6 | Alinear `ultimo_numero` con MAX existente por scope |

---

*Transacciones y manual en `15_TRANSACTION_AND_CONCURRENCY.md`.*
