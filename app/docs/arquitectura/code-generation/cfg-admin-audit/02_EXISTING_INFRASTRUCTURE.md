# Infraestructura existente (inventario AS-IS)

**Paquete:** `cfg-admin-audit`  
**Fecha:** 2026-07-17

---

## 1. Resumen del inventario

| Área | Existe | Evidencia |
|------|--------|-----------|
| Módulo ERP `cfg` | ❌ | Sin `app/modules/cfg/` |
| DDL `cfg_codigo_secuencia` | ✅ | `V010__tablas_bd_erp_completo.sql` |
| Modelo SQLAlchemy | ✅ | `CfgCodigoSecuenciaTable` en `tables.py` |
| Queries ERP `queries/cfg/` | ❌ | Sin carpeta |
| Repositorio bootstrap | ✅ | `CfgCodigoSecuenciaRepository` |
| Store Motor | ✅ | `CfgSequenceStore` |
| Servicios admin | ❌ | No hay `*_servicio` CFG |
| Endpoints / OpenAPI CFG | ❌ | Sin rutas `/cfg`; sin permisos seed |
| Seed onboarding | ✅ | `onboarding_seed.py` + `cfg_codigo_onboarding_seed.py` |
| Diseño admin documental | ✅ | `codigo-generation-admin/` |

---

## 2. Entidad `cfg_codigo_secuencia`

### 2.1 Columnas (ORM)

| Columna | Tipo | Notas |
|---------|------|-------|
| `secuencia_id` | UNIQUEIDENTIFIER PK | |
| `cliente_id` | FK `cliente` CASCADE | Aislamiento tenant |
| `sequence_key` | String(64) | Clave catálogo |
| `scope_type` | String(20) | TENANT / EMPRESA / ALMACEN / PUNTO_VENTA |
| `scope_fingerprint` | String(64) | Parte de UQ |
| `empresa_id` | FK `org_empresa` nullable | Scope EMPRESA+ |
| `almacen_id` | FK `inv_almacen` nullable | Scope ALMACEN |
| `punto_venta_id` | FK `pos_punto_venta` nullable | Scope PUNTO_VENTA |
| `prefijo` | String(10) | Override formato |
| `separador` | String(2) nullable | |
| `longitud_numero` | Integer | Padding |
| `ultimo_numero` | Integer | Contador operativo |
| `numero_inicial` | Integer | Piso |
| `es_activo` | Boolean | Soft-enable |
| `generation_policy` | String(20) | CK: AUTO_REQUIRED / AUTO_DEFAULT / MANUAL_ONLY |
| `fecha_creacion` | DateTime | |
| `fecha_actualizacion` | DateTime nullable | |
| `usuario_actualizacion_id` | UNIQUEIDENTIFIER nullable | Sin FK explícita en ORM |

**Unique:** `(cliente_id, sequence_key, scope_fingerprint)` = `UQ_cfg_scope`.

### 2.2 Clasificación operativa (diseño admin, confirmada por código)

| Clase | Campos | Editable por admin futuro |
|-------|--------|---------------------------|
| **A** Inmutable | ids, key, scope, fingerprint | No |
| **B** Configurable | prefijo, separador, longitud_numero, numero_inicial, es_activo | Sí |
| **C** Solo lectura | generation_policy, timestamps | No (policy = catálogo) |
| **D** Operativo | ultimo_numero | Solo Motor / Gateway.align |

---

## 3. Modelos SQLAlchemy

- **Tabla Core:** `CfgCodigoSecuenciaTable` (`app/infrastructure/database/tables.py`).
- **No hay** modelo ORM clase-mapped separado ni schemas Pydantic de presentación CFG.
- **DTO Motor:** `CfgSequenceRow` (dataclass en `cfg_sequence_store.py`).

---

## 4. Queries

| Artefacto | Estado |
|-----------|--------|
| `app/infrastructure/database/queries/cfg/` | **Ausente** |
| Patrón dual-path session (como ORG/INV) | **Ausente** para admin |
| Paginación ERP (`apply_erp_pagination`) sobre cfg | **Ausente** |

La lectura admin hoy solo es posible vía:

- `CfgCodigoSecuenciaRepository.get_by_cliente` / `get_by_sequence_key` / `get_by_entidad`
- `CfgSequenceStore.get_by_scope` / `read_for_preview` (runtime Motor)

Ninguno expone contrato HTTP.

---

## 5. Repositorio bootstrap (`CfgCodigoSecuenciaRepository`)

| Método | Capacidad | Relevancia admin |
|--------|-----------|------------------|
| `get_by_cliente` | Lista por tenant | Base listado |
| `get_by_sequence_key` | Filtro key + scope dims | Detalle / filtro |
| `get_by_entidad` | Por empresa/almacén/PV | Filtros scope |
| `insert_secuencia` | Alta fila | Solo bootstrap/lazy — **no** CRUD admin libre |
| `update_secuencia` | Actualiza prefijo, separador, longitud, es_activo, usuario, fecha | Base PATCH B (parcial) |
| `update_ultimo_numero` | Contador | **Prohibido** en API admin genérica; solo vía align Motor |

**Gap repo detectado:** `update_secuencia` **no** actualiza `numero_inicial` (columna B documentada como configurable). Extensión menor futura si MVP incluye ese campo.

**ADJ-03:** escrituras del repo requieren `session` explícita (Dedicated-safe).

---

## 6. Store Motor (`CfgSequenceStore`)

| Método | Uso |
|--------|-----|
| `get_by_scope` | Lookup por ScopeKey |
| `ensure_row` | Lazy creation ALMACEN/PV |
| `increment_and_get` | allocate |
| `align_counter` | mantenimiento |
| `read_for_preview` | preview sin consumo |

**Regla de reuso:** el módulo admin **no** debe llamar `increment_and_get` ni mutar contador fuera del Gateway.

---

## 7. Servicios

| Tipo | Estado |
|------|--------|
| Servicios ERP admin CFG | ❌ |
| Seed onboarding tenant | ✅ `cfg_codigo_onboarding_seed.py` |
| Motor coordinators/services | ✅ (preview_reader, counter_alignment, allocation) — uso interno Gateway |

---

## 8. Endpoints y OpenAPI

| Ítem | Estado |
|------|--------|
| Rutas `/cfg/secuencias` | ❌ No hay matches en código |
| Permisos `cfg.secuencias.*` en seeds/SQL | ❌ No encontrados |
| Snapshot OpenAPI CFG | ❌ No aplica (recurso inexistente) |
| Endpoints ORG/INV códigos | ✅ Emiten códigos; **no** administran cfg |

---

## 9. Seed y catálogo

| Ítem | Estado |
|------|--------|
| `SequenceCatalog` | ✅ ~63 entradas; fuente normativa |
| Eager onboarding (TENANT/EMPRESA CFG) | ✅ Derivado del catálogo (`EAGER_SEQUENCE_KEYS`) |
| Lazy ALMACEN / PUNTO_VENTA | ✅ `ensure_row` en primer uso |
| Store FISCAL | ✅ Fuera de `cfg_codigo_secuencia` |

---

## 10. Componentes reutilizables vs faltantes

### Reutilizables sin modificar Motor

- DDL + ORM
- `CfgCodigoSecuenciaRepository` (lectura + update config)
- `CodigoGeneracionGateway` (preview, align, validate_manual)
- `SequenceCatalog` (enrich read-only)
- `get_connection_for_tenant` + sesión UoW
- Documentación `codigo-generation-admin/` (contrato funcional)

### Faltantes (desarrollo nuevo del módulo)

- Árbol `app/modules/cfg/` completo (V4)
- `queries/cfg/` + paginación/sort
- Schemas presentation
- Servicios + validators BR-CUST / org_empresa lock
- Routers + `cfg_deps`
- Seed RBAC permisos/menú
- Tests y OpenAPI del recurso
- (Opcional post-MVP) diagnóstico, historial audit dedicado

---

## 11. Dependencias con ORG / INV / futuros ERP

| Módulo | Relación AS-IS |
|--------|----------------|
| ORG | Consumidor Gateway; FK `empresa_id` en filas EMPRESA; BR-BOOT-04 `org_empresa` |
| INV | Consumidor Gateway; FK `almacen_id` para scopes ALMACEN |
| POS (futuro) | FK `punto_venta_id`; lazy rows |
| Otros ERP | Nuevas `sequence_key` en Catalog → filas cfg seed/lazy; admin las lista sin conocer ORG/INV |

El admin CFG es **transversal**: no debe importar services ORG/INV para mutar secuencias; solo puede enriquecer display con metadatos de catálogo (`modulo_codigo`).
