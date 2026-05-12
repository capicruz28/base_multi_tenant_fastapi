# Auditoría — Módulo TAX (Gestión Tributaria)

**Código:** TAX  
**Fuente de modelo de datos:** `docs/bd/TAX_TABLAS.sql` (tablas `tax_*`).  
**Metodología:** `docs/prompts/PROMPT_MODULO_MAESTRO.md` — Fase 2.

**Inventario de código TAX**

| Capa | Ubicación |
|------|-----------|
| Routers (presentation) | `app/modules/tax/presentation/endpoints.py` (agregador), `endpoints_libro_electronico.py` |
| Schemas | `app/modules/tax/presentation/schemas.py` |
| Servicios (application) | `app/modules/tax/application/services/libro_electronico_service.py`, `__init__.py` |
| Consultas SQL / Core (infraestructura) | `app/infrastructure/database/queries/tax/libro_electronico_queries.py`, `queries/tax/__init__.py` |
| Tablas Core (SQLAlchemy metadata) | `app/infrastructure/database/tables_erp/tables_tax.py` |
| Repositories dedicados en `app/modules/tax/` | No hay carpeta `repositories`; persistencia vía queries + `Table` Core |

Prefijo API registrado: **`/tax`** (`app/api/v1/api.py`). Subrecurso: **`/tax/libros-electronicos`**.

---

## 1. Tablas detectadas y su tipo

| Tabla | Tipo (prompt) |
|-------|----------------|
| `tax_libro_electronico` | **Transaccional / operativo** (ciclo de generación y estado del libro PLE; no es maestro de catálogo; no es tabla derivada de solo lectura). |

La tabla **no** define `es_activo`; la baja lógica estilo ORG no aplica tal cual sobre este modelo.

---

## 2. Endpoints existentes

Criterios: **tenant** = propagación de `cliente_id` del usuario autenticado hasta queries (`client_id` / `cliente_id` en filtros e inserción). **RBAC** = `Depends(require_permission(...))` en la ruta.

Rutas relativas a **`/tax/libros-electronicos`**.

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | RBAC |
|------|--------|-----------------|------------------------|------|
| `/tax/libros-electronicos` | GET | `tax_libro_electronico` | Sí (list + filtros opcionales) | `tax.libro.leer` |
| `/tax/libros-electronicos/{libro_id}` | GET | `tax_libro_electronico` | Sí (`get` por id + `cliente_id`) | `tax.libro.leer` |
| `/tax/libros-electronicos` | POST | `tax_libro_electronico` | Sí (`create` inyecta `cliente_id`) | `tax.libro.crear` |
| `/tax/libros-electronicos/{libro_id}` | PUT | `tax_libro_electronico` | Sí (`update` condiciona por `cliente_id`) | `tax.libro.actualizar` |

**Notas técnicas**

- En listado, `empresa_id` es **opcional** en query; si se omite, se listan filas de todas las empresas del tenant (mismo criterio que varios listados ORG con `empresa_id` opcional).
- En **detalle por id** no hay query `empresa_id` opcional para reforzar alcance; la fila sigue acotada por `cliente_id` + `libro_id`.

---

## 3. Brechas frente al estándar del prompt

### 3.1 Estándar **MAESTRO** (crear, listar, detalle, actualizar, activar/desactivar)

**No aplica** como estándar principal: la entidad es transaccional/operativa, no catálogo maestro. No hay `es_activo` en BD.

### 3.2 Estándar **TRANSACCIONAL** del prompt

Referencia del prompt: crear (**borrador**), actualizar (**solo en borrador**), **aprobar**, **procesar**, **anular**, listar, detalle.

| Capacidad | Estado actual |
|-----------|----------------|
| Listar | Cubierto (`GET ""`) |
| Detalle | Cubierto (`GET /{libro_id}`) |
| Crear | Cubierto (`POST ""`); no hay distinción explícita de estado **borrador** vs definitivo (el cliente puede enviar `estado` en body; por defecto en schema `generado`) |
| Actualizar solo en borrador | **No** implementado: `PUT` no valida estado previo |
| Aprobar / procesar / anular como rutas o reglas de negocio | **No** hay endpoints dedicados; parte del ciclo podría modelarse vía `estado` en `PUT` sin reglas centralizadas |
| Transacciones cabecera + detalle | **N/A** en `TAX_TABLAS.sql` (sin tabla detalle en alcance) |

---

## 4. Endpoints faltantes o sugeridos (Fase 3)

| Ruta sugerida (bajo `/tax`) | Método | Motivo |
|-----------------------------|--------|--------|
| `/libros-electronicos/{libro_id}?empresa_id=` (refuerzo) | GET | Paridad con patrones ORG: validar que la fila pertenezca a la empresa indicada cuando el cliente envía `empresa_id` |
| Acciones de ciclo de vida (si negocio lo exige) | POST o PATCH | Por ejemplo **registrar envío** / **anular** con transiciones válidas de `estado`, en lugar de exponer cambios libres de estado solo por `PUT` |
| Validación de pertenencia `empresa_id` ↔ `cliente_id` en **POST** | — | Evitar insertar libros para una empresa de otro tenant si el UUID de empresa no pertenece al cliente (hoy las queries confían en FK de BD y en datos coherentes) |

No se sugiere `DELETE` físico (reglas del proyecto: no borrado físico; aquí no hay baja lógica `es_activo` en el script de referencia).

---

## 5. Campos en BD (`TAX_TABLAS.sql`) no reflejados o divergentes en schemas

Comparación por endpoint / schema. La columna BD `año` se expone en API como **`anio`** (mapeo en servicio y queries); eso es **convención intencional**, no brecha.

### 5.1 `LibroElectronicoRead` ↔ columnas BD

| Columna BD | Observación |
|--------------|-------------|
| Todas las columnas de la tabla | Cubiertas en lectura (`año` → `anio`). |

### 5.2 `LibroElectronicoCreate` ↔ columnas BD

| Columna BD | Observación |
|--------------|-------------|
| `libro_id` | Generado en capa de aplicación al insertar (coherente). |
| `cliente_id` | No va en body; lo inyecta la capa de datos (coherente). |
| `fecha_generacion`, `fecha_creacion` | Valores por defecto en BD / servidor; no están en el schema de creación (aceptable). |

### 5.3 `LibroElectronicoUpdate` ↔ columnas BD

Columnas que **existen en BD** y **no** están en `LibroElectronicoUpdate` (actualización parcial intencional o brecha según reglas de negocio):

| Columna BD | Observación |
|--------------|-------------|
| `empresa_id` | No actualizable por API actual. |
| `tipo_libro` | No actualizable por API actual. |
| `periodo_id` | No actualizable por API actual. |
| `año` / `mes` | No actualizables por API actual (solo en creación como `anio`/`mes`). |
| `fecha_generacion` | No actualizable por API actual. |
| `generado_por_usuario_id` | Creable en `POST`; **no** en `PUT`. Si negocio requiere corregir usuario generador tras creación, falta en `Update`. |

---

## 6. Problemas de tenant o RBAC (resumen)

| Problema | Severidad | Ubicación / notas |
|----------|-----------|-------------------|
| Permisos `tax.libro.*` no encontrados en seeds SQL del repo (búsqueda en `app/docs/database` y patrones `tax.`) | **Media / alta** en despliegue nuevo | Sin filas en `permiso` (o equivalente) alineadas a `tax.libro.leer`, `tax.libro.crear`, `tax.libro.actualizar`, los usuarios no tenant-admin podrían recibir **403** salvo carga manual en BD. |
| Código de recurso RBAC es `libro` (abreviado), no `libro_electronico` | Baja | `endpoints_libro_electronico.py` — coherente con `modulo.recurso.accion` pero distinto al nombre de tabla; documentar en seeds/menu si se desea alinear nomenclatura. |
| `GET /{libro_id}` sin validación explícita opcional `empresa_id` | Baja | Aislamiento por tenant vía `cliente_id` correcto; refuerzo multi-empresa opcional. |
| Reglas de estado en `PUT` | Media | Sin máquina de estados: el cliente puede enviar `estado` arbitrario en creación/actualización dentro de límites de longitud. |

---

## 7. Código marcado como revisión (no eliminar en esta fase)

- La implementación actual de TAX se **mantiene**; la Fase 3 debe **completar** solo lo acordado en el reporte (RBAC seeds, refuerzos tenant, reglas transaccionales o campos en schemas, según decisión de producto).
- No marcar como obsoleto el uso de `anio` en API frente a `año` en BD: es un mapeo estable y documentado en comentarios de `schemas.py` y servicio.

---

## 8. Checkpoint Fase 2 (respuestas cortas)

1. **Routers / services / queries:** Cubiertos para `tax_libro_electronico`; no hay más tablas `tax_*` en el SQL de referencia del módulo.  
2. **Endpoints:** 4 rutas bajo `/tax/libros-electronicos` (GET lista, GET detalle, POST, PUT).  
3. **Brechas transaccionales:** Sin modelo borrador ni endpoints aprobar/procesar/anular; actualización sin restricción por estado.  
4. **Schemas vs BD:** `Read` y `Create` alineados con alcance habitual; `Update` omite varias columnas de BD (ver §5.3).  
5. **Permisos en seeds:** No detectados en el repositorio; verificar o añadir en Fase 3.

⛔ **Fin Fase 2.** Continuar con Fase 3 solo tras confirmación explícita.
