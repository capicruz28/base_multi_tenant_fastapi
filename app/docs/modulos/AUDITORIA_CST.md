# Auditoría — Módulo CST (Costos y Costeo)

Documento generado en **Fase 2** del prompt maestro (solo lectura y análisis).  
Prefijo de tablas: `cst_`. Rutas API bajo `{API_V1_STR}/cst` (p. ej. `/api/v1/cst`).

---

## 1. Tablas detectadas y tipo

| Tabla | Tipo |
|-------|------|
| `cst_centro_costo_tipo` | Maestro |
| `cst_producto_costo` | Registro de costeo por producto/período (no es documento con estados; **no** encaja en el patrón transaccional “borrador / aprobar / anular” del prompt maestro por ausencia de `estado` en BD) |

**Referencia BD:** `docs/bd/CST_TABLAS.sql` (y sección homóloga en `3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql`).  
**ORM:** `app/infrastructure/database/tables_erp/tables_cst.py` está alineado con esas tablas para columnas no calculadas; `costo_total` y `costo_unitario` existen como columnas calculadas persistidas en SQL Server pero **no** están definidas en `tables_cst.py` (el servicio recalcula y expone en Read).

---

## 2. Inventario de código (Fase 2.1)

No existe carpeta `repositories`: la persistencia está en `app/infrastructure/database/queries/cst/*.py` (patrón queries + `execute_query` / `execute_insert` / `execute_update`).

**Archivos del módulo CST**

| Área | Archivos |
|------|----------|
| Presentation | `endpoints.py`, `endpoints_centro_costo_tipo.py`, `endpoints_producto_costo.py`, `schemas.py` |
| Application | `application/services/centro_costo_tipo_service.py`, `producto_costo_service.py`, `__init__.py` |
| Infrastructure | `queries/cst/centro_costo_tipo_queries.py`, `producto_costo_queries.py`, `__init__.py` |
| Tablas Core | `tables_erp/tables_cst.py` |

### 2.1 Endpoints existentes

Base: `/cst` + subprefijos definidos en `app/modules/cst/presentation/endpoints.py`.

| Ruta | Método | Entidad | Tenant (`cliente_id`) | RBAC (`require_permission`) |
|------|--------|---------|-------------------------|------------------------------|
| `/cst/tipos-centro-costo` | GET | Tipo centro de costo | Sí (`current_user.cliente_id`) | Sí (`cst.centro_costo_tipo.leer`) |
| `/cst/tipos-centro-costo/{cc_tipo_id}` | GET | Tipo centro de costo | Sí | Sí (`cst.centro_costo_tipo.leer`) |
| `/cst/tipos-centro-costo` | POST | Tipo centro de costo | Sí | Sí (`cst.centro_costo_tipo.crear`) |
| `/cst/tipos-centro-costo/{cc_tipo_id}` | PUT | Tipo centro de costo | Sí | Sí (`cst.centro_costo_tipo.actualizar`) |
| `/cst/producto-costo` | GET | Producto costo | Sí | Sí (`cst.producto_costo.leer`) |
| `/cst/producto-costo/{producto_costo_id}` | GET | Producto costo | Sí | Sí (`cst.producto_costo.leer`) |
| `/cst/producto-costo` | POST | Producto costo | Sí | Sí (`cst.producto_costo.crear`) |
| `/cst/producto-costo/{producto_costo_id}` | PUT | Producto costo | Sí | Sí (`cst.producto_costo.actualizar`) |

**Tenant `empresa_id`:** Los listados aceptan `empresa_id` opcional en query; el body de creación incluye `empresa_id`. Los **GET por ID** y los **UPDATE** filtran solo por `cliente_id` + clave técnica en queries; **no** exigen ni validan `empresa_id` en la ruta ni en el cuerpo del PUT.

---

## 3. Brechas funcionales (Fase 2.2)

### `cst_centro_costo_tipo` (maestro)

| Requisito | Estado |
|-----------|--------|
| Crear | Cubierto (POST) |
| Listar | Cubierto (GET lista) |
| Detalle | Cubierto (GET por id) |
| Actualizar | Cubierto (PUT) |
| Activar / desactivar | **Parcial:** `es_activo` en `CentroCostoTipoCreate` y `CentroCostoTipoUpdate`; no hay rutas dedicadas (p. ej. `DELETE` lógico o `POST .../reactivar`) como en algunos módulos INV |

### `cst_producto_costo` (criterio transaccional del prompt maestro)

| Requisito | Estado |
|-----------|--------|
| Crear (borrador) | **N/A en BD** (no hay columna `estado`); existe **POST** de alta de registro |
| Actualizar (solo borrador) | **N/A** |
| Aprobar / procesar / anular | **N/A** por modelo de datos actual; no hay anulación lógica sin nueva columna (no proponer cambio de BD aquí) |
| Listar / detalle | Cubierto |
| Crear / actualizar genéricos | Cubierto (POST/PUT) |

**Columnas calculadas:** `costo_total` y `costo_unitario` no deben enviarse en escritura; el API actual no los incluye en Create/Update (**correcto**).

---

## 4. Campos en BD no cubiertos o divergentes en schemas (Fase 2.3)

Comparación contra **`docs/bd/CST_TABLAS.sql`** y `tables_cst.py`.

### `cst_centro_costo_tipo`

| Endpoint / schema | Observación |
|-------------------|-------------|
| `CentroCostoTipoRead` | Cobertura alineada con columnas persistidas de la tabla |
| `CentroCostoTipoUpdate` | No permite cambiar `empresa_id` (aceptable para evitar movimientos entre empresas) |

### `cst_producto_costo`

| Campo / aspecto | En schemas actuales |
|-------------------|---------------------|
| `año` (BD) vs `anio` (API) | Mapeo intencional en servicio (`_dump_to_db` / `_row_to_read`); **no** es omisión |
| `costo_total`, `costo_unitario` (calculadas en BD) | En `ProductoCostoRead` como salida; no en Create/Update (**correcto**) |
| `fecha_calculo` | En `ProductoCostoRead`; **no** está en `ProductoCostoCreate` ni `ProductoCostoUpdate`. Tras un PUT que modifica montos, la BD puede recalcular columnas persistidas, pero **no hay actualización explícita de `fecha_calculo`** desde el API (el campo existe en tabla con default en alta) |

**Create/Update vs tabla:** No faltan columnas obligatorias de negocio en Create salvo la decisión explícita de no exponer `fecha_calculo` en alta/edición.

---

## 5. Problemas de tenant y RBAC

1. **`empresa_id` en GET por ID y PUT:** `get_centro_costo_tipo_by_id` y `get_producto_costo_by_id` (y updates asociados) filtran por `cliente_id` + PK; no comprueban `empresa_id`. Un usuario con acceso multi-empresa del mismo cliente podría leer/modificar un registro de otra empresa si conociera el UUID (riesgo de contención de datos por empresa).
2. **Listados sin `empresa_id`:** devuelven filas de **todas** las empresas del cliente si el query param no se envía; puede ser intencional para back-office o exigir endurecimiento según política del producto.
3. **Seeds RBAC:** en `app/docs/database`, no se encontró un script tipo `SEED_PERMISOS_RBAC_CST.sql` con permisos `cst.centro_costo_tipo.*` ni `cst.producto_costo.*` (búsqueda por patrón de códigos). Los endpoints **sí** declaran `require_permission`; sin permisos cargados en BD, las llamadas fallarán por autorización salvo carga manual u otro script no listado.

---

## 6. Código marcado como obsoleto o incorrecto (no eliminar)

| Ubicación | Observación |
|-----------|-------------|
| `producto_costo_service.py` (`_row_to_read`) | Recalcula `costo_total` y `costo_unitario` en Python; en SQL Server las columnas pueden ser **PERSISTED**. No es incorrecto por sí, pero **duplica** la fuente de verdad respecto a la BD si el motor ya devuelve esos valores en el `SELECT`. |
| `tables_cst.py` vs `CST_TABLAS.sql` | El script documenta columnas calculadas; el modelo Core no las declara. Coherente con inserts manuales, pero conviene asumir que el **SELECT** puede traer columnas extra según driver/configuración. |

---

## 7. Endpoints faltantes (sugerencia, sin implementar aún)

Respetar prefijos actuales (`/cst/tipos-centro-costo`, `/cst/producto-costo`).

| Sugerencia | Método | Notas |
|------------|--------|--------|
| `/cst/tipos-centro-costo/{cc_tipo_id}` baja lógica | DELETE | Patrón maestro: `es_activo = 0` + permiso (p. ej. `eliminar` o reutilizar `actualizar`) si se quiere separar de PUT |
| `/cst/tipos-centro-costo/{cc_tipo_id}/reactivar` | POST | Opcional |
| Query obligatorio o validación de `empresa_id` | — | En GET por ID / PUT / DELETE si la política exige siempre contexto de empresa |
| `/cst/producto-costo/{id}/...` | — | Solo si el negocio define anulación o recalculo masivo; **requiere reglas y posiblemente BD** no previstas hoy |

---

## 8. Checklist Fase 3 (referencia)

Tras confirmación: valorar seeds RBAC para `cst.centro_costo_tipo` y `cst.producto_costo`, endurecer `empresa_id` donde aplique, rutas de baja lógica del maestro si se adoptan en el estándar del proyecto, y exposición/actualización de `fecha_calculo` en flujos de edición de costos si se desea trazabilidad de recálculo.

---

**Fin Fase 2.** Esperar confirmación antes de Fase 3 (implementación).
