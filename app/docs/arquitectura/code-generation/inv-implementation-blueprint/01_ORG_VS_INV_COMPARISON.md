# Comparación ORG vs INV — Golden Reference → Categoría piloto

**ORG de referencia (patrón EMPRESA):** `org_cargo` / `cargo_service.py`  
**INV piloto:** `inv_categoria_producto` / `categoria_service.py`  
**Nota:** `org_empresa` es TENANT — **no** usar como plantilla de maestros INV.

---

## 1. Comparación ORG vs INV (Categoría)

| Dimensión | ORG Cargo (AS-IS certificado) | INV Categoría (AS-IS) | Acción Blueprint |
|-----------|-------------------------------|------------------------|------------------|
| Scope | EMPRESA | EMPRESA | Reutilizar |
| `sequence_key` | `org_cargo` | `inv_categoria_producto` | Usar catálogo |
| Campo código | `codigo` | `codigo` | Igual nombre |
| Policy | AUTO_DEFAULT | AUTO_DEFAULT | Igual |
| Prefijo / pad | CAR / 3 | CAT / 3 | Via cfg/catálogo |
| Create: código | Optional | **Required** | → Optional |
| Update: código | **Ausente** (BR-IMM) | Presente Optional | → Quitar |
| Adapter | `OrgCodigoGenerationService` | **No existe** | Crear `InvCodigoGenerationService` |
| CREATE UoW | `get_connection_for_tenant` + `session.begin` | Insert directo sin session | Adoptar UoW ORG |
| Gateway.allocate | Sí | No | Añadir |
| Pre-check UNIQUE manual | `get_cargo_by_codigo` + 409 | **No hay** `get_categoria_by_codigo` | Añadir query + ConflictError |
| Queries dual-path | `session=` opcional | Solo `execute_*` | Extender create/get_by_codigo |
| Audit | Logs ORG session | `apply_create_audit` | Conservar audit INV |
| Soft-delete | Sí | Update `es_activo` vía payload | Sin cambio Motor |

### Qué se reutiliza (sin copiar archivos)

| Componente | Reutilización |
|------------|---------------|
| `CodigoGeneracionGateway` | Import directo desde core |
| `GenerationContext`, enums | Import directo |
| `get_connection_for_tenant` / `OPERATION_CLASS_TENANT_DATA` | Mismo routing |
| `enforce_body_empresa_matches_session` / `ensure_empresa_in_tenant` | Mismo company_scope |
| `ConflictError` / `NotFoundError` | Mismos exceptions |
| Patrón de tests unitarios (mocks) | Replicar estructura ORG |

### Qué se copia / adapta (nuevo en INV)

| Artefacto | Origen ORG | Destino INV |
|-----------|------------|-------------|
| Adapter | `org_codigo_generation_service.py` | `inv_codigo_generation_service.py` |
| `_SEQUENCE_KEY` + create UoW | `cargo_service.py` | `categoria_service.py` |
| Schema Create/Update | `CargoCreate` / `CargoUpdate` | `CategoriaCreate` / `CategoriaUpdate` |
| Tests motor + IMM | `test_org_cargo_*` / `test_org_br_imm_*` | `test_inv_categoria_*` |

### Qué cambia (solo contexto INV)

| Cambio | Detalle |
|--------|---------|
| Prefijo módulo | `inv` vs `org` |
| Table / PK | `categoria_id` vs `cargo_id` |
| Audit | `inv_audit_context.apply_create_audit` (ORG no usa el mismo helper) |
| Paginación | Categoría ya tiene paginación ERP — **conservar** |
| Query gap | INV debe ganar dual-path + `get_*_by_codigo` (ORG ya lo tiene) |

### Qué NO se toca

Motor, Gateway, SequenceCatalog, Baseline V1, BR-IMM docs, código ORG certificado.

---

## 2. Archivos equivalentes ORG ↔ INV

### 2.1 Capas producto

| Rol | ORG (referencia) | INV (objetivo) |
|-----|------------------|----------------|
| Adapter código | `app/modules/org/application/services/org_codigo_generation_service.py` | `app/modules/inv/application/services/inv_codigo_generation_service.py` **(nuevo)** |
| Service piloto | `.../cargo_service.py` | `.../categoria_service.py` |
| Schemas | `app/modules/org/presentation/schemas.py` (`Cargo*`) | `app/modules/inv/presentation/schemas.py` (`Categoria*`) |
| Queries | `app/infrastructure/database/queries/org/cargo_queries.py` | `.../inv/categoria_queries.py` |
| Endpoints | `endpoints_cargos.py` | `endpoints_categorias.py` (sin cambio de rutas) |
| Router | `org/presentation/endpoints.py` | `inv/presentation/endpoints.py` |

### 2.2 Matriz 7 entidades INV ↔ plantilla ORG

| # | INV entidad | sequence_key | Campo | Service INV | Query INV | Plantilla ORG más cercana |
|---|-------------|--------------|-------|-------------|-----------|---------------------------|
| 1 | Categoría | `inv_categoria_producto` | `codigo` | `categoria_service` | `categoria_queries` | **cargo** |
| 2 | Unidad medida | `inv_unidad_medida` | `codigo` | `unidad_medida_service` | `unidad_medida_queries` | cargo |
| 3 | Tipo movimiento | `inv_tipo_movimiento` | `codigo` | `tipo_movimiento_service` | `tipo_movimiento_queries` | cargo |
| 4 | Almacén | `inv_almacen` | `codigo` | `almacen_service` | `almacen_queries` | cargo / sucursal |
| 5 | Producto | `inv_producto` | `codigo_sku` | `producto_service` | `producto_queries` | cargo (campo ≠ `codigo`) |
| 6 | Movimiento | `inv_movimiento` | `numero_movimiento` | `movimiento_service` (+ proceso) | `movimiento_queries` | cargo + política AUTO_REQUIRED |
| 7 | Inv. físico | `inv_inventario_fisico` | `numero_inventario` | `inventario_fisico_service` | `inventario_fisico_queries` | movimiento (F2) |

---

## 3. Servicios: reutilizar vs implementar

| Servicio / componente | ¿Reutilizar tal cual? | Notas |
|-----------------------|----------------------|-------|
| `CodigoGeneracionGateway` | **Sí** | No modificar |
| `OrgCodigoGenerationService` | **No** (no cross-import módulo) | Clonar patrón → `InvCodigoGenerationService` |
| `cargo_service` create/update | **Como plantilla** | No llamar desde INV |
| `categoria_service` list/get/delete | **Conservar** | Solo mutar create + update BR-IMM |
| `inv_stock_write_policy` / workflow | **No tocar** en fase maestros | Fuera piloto categoría |
| `inv_estorno_proceso` / aprobación IF | **Fase documentos** | Sustituir gens timestamp |

---

## 4. Schemas — mismo patrón ORG

### 4.1 Regla transversal (todas las entidades Motor)

| Schema | Campo Motor | Regla |
|--------|-------------|-------|
| `*Create` | Presente | AUTO_DEFAULT → `Optional`; AUTO_REQUIRED → omitir o no required |
| `*Update` | **Ausente** | BR-IMM-01…03 |
| `*Read` | Presente `str` required | Sin cambio |

### 4.2 Categoría (piloto) — transformación exacta

| Schema | AS-IS | TO-BE |
|--------|-------|-------|
| `CategoriaCreate.codigo` | `str = Field(...)` | `Optional[str] = Field(None, max_length=20)` |
| `CategoriaUpdate.codigo` | `Optional[str]` | **Eliminar campo** |
| Mixin validator `codigo` | En Create/Update | `check_fields=False` en Update (patrón ORG schemas) |
| `CategoriaRead.codigo` | `str` | Sin cambio |

### 4.3 Resto (misma transformación)

| Create AS-IS required | Update AS-IS tiene código | TO-BE |
|----------------------|---------------------------|-------|
| UM, TM, Almacén `codigo` | Sí | Optional Create; quitar Update |
| Producto `codigo_sku` | Sí en Update | Optional Create; quitar de Update; **no** tocar barra/interno/fabricante |
| Movimiento `numero_movimiento` | Sí | Create: no required / omitir; Update: quitar |
| IF `numero_inventario` | Sí | Idem AUTO_REQUIRED |

---

*Adapter y flujos: [`02_ADAPTER_AND_FLOWS.md`](02_ADAPTER_AND_FLOWS.md)*
