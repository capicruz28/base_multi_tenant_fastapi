# Auditoría — Módulo PRC (Gestión de Precios)

**Código:** PRC  
**Fuente de modelo de datos:** `docs/bd/PRC_TABLAS.sql` (tablas `prc_*`).  
**Metodología:** `docs/prompts/PROMPT_MODULO_MAESTRO.md` — Fase 2.

**Inventario de código PRC**

| Capa | Ubicación |
|------|-----------|
| Routers (presentation) | `app/modules/prc/presentation/endpoints.py` (agregador), `endpoints_listas_precio.py`, `endpoints_promociones.py` |
| Schemas | `app/modules/prc/presentation/schemas.py` |
| Servicios (application) | `app/modules/prc/application/services/lista_precio_service.py`, `promocion_service.py`, `__init__.py` |
| Consultas SQL (infraestructura) | `app/infrastructure/database/queries/prc/lista_precio_queries.py`, `promocion_queries.py` |
| Tablas Core (ORM metadata) | `app/infrastructure/database/tables_erp/tables_prc.py` |
| Repositories dedicados en `app/modules/prc/` | No hay carpeta `repositories`; persistencia vía queries en infraestructura |

Prefijo API registrado: **`/prc`** (`app/api/v1/api.py`).

---

## 1. Tablas detectadas y su tipo

| Tabla | Tipo (prompt) |
|-------|----------------|
| `prc_lista_precio` | Maestro |
| `prc_lista_precio_detalle` | Detalle de maestro (líneas de lista; no es derivada analítica) |
| `prc_promocion` | Maestro |

No hay tablas derivadas de solo lectura en el alcance de `PRC_TABLAS.sql`.

**Nota de consistencia modelo código vs SQL de referencia:** En `docs/bd/PRC_TABLAS.sql` la cabecera de lista define **`moneda_id`** (FK a `cat_moneda`). En `app/infrastructure/database/tables_erp/tables_prc.py` la columna mapeada es **`moneda`** (`String(3)`). La auditoría de campos contrasta contra el **SQL de referencia del módulo**; si la base desplegada coincide con ese script, hay desalineación a corregir en capa de aplicación (sin cambiar DDL).

---

## 2. Endpoints existentes

Criterios: **tenant** = uso de `cliente_id` del usuario autenticado en servicio/query (y, cuando aplica, filtro o validación de `empresa_id`). **RBAC** = presencia de `Depends(require_permission(...))` en la ruta.

Rutas relativas a **`/prc`** (el router agregador monta `listas-precio` y `promociones`).

### 2.1 Listas de precio y detalle (`/prc/listas-precio`)

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | RBAC |
|------|--------|-----------------|------------------------|------|
| `/listas-precio` | GET | `prc_lista_precio` | Sí (servicio + queries) | `prc.lista_precio.leer` |
| `/listas-precio/{lista_precio_id}` | GET | `prc_lista_precio` | Sí | `prc.lista_precio.leer` |
| `/listas-precio` | POST | `prc_lista_precio` | Sí | `prc.lista_precio.crear` |
| `/listas-precio/{lista_precio_id}` | PUT | `prc_lista_precio` | Sí | `prc.lista_precio.actualizar` |
| `/listas-precio/{lista_precio_id}/detalles` | GET | `prc_lista_precio_detalle` | Sí | `prc.lista_precio.leer` |
| `/listas-precio/{lista_precio_id}/detalles` | POST | `prc_lista_precio_detalle` | Sí | **No** (solo `get_current_active_user`) |
| `/listas-precio/detalles/{lista_precio_detalle_id}` | GET | `prc_lista_precio_detalle` | Sí | `prc.lista_precio.leer` |
| `/listas-precio/detalles/{lista_precio_detalle_id}` | PUT | `prc_lista_precio_detalle` | Sí | `prc.lista_precio.actualizar` |

### 2.2 Promociones (`/prc/promociones`)

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | RBAC |
|------|--------|-----------------|------------------------|------|
| `/promociones` | GET | `prc_promocion` | Sí | `prc.promocion.leer` |
| `/promociones/{promocion_id}` | GET | `prc_promocion` | Sí | `prc.promocion.leer` |
| `/promociones` | POST | `prc_promocion` | Sí | `prc.promocion.crear` |
| `/promociones/{promocion_id}` | PUT | `prc_promocion` | Sí | `prc.promocion.actualizar` |

**Observación patrón PRC vs ORG:** En PRC se usa explícitamente `Depends(get_current_active_user)` junto con `require_permission`; el usuario sigue autenticado en ambos casos. El hueco es funcional (permiso), no de identidad.

---

## 3. Brechas frente al estándar MAESTRO del prompt

Estándar del prompt: crear, listar, detalle, actualizar, **activar/desactivar**.

| Tabla | Crear | Listar | Detalle | Actualizar | Activar/desactivar explícito |
|-------|-------|--------|---------|------------|------------------------------|
| `prc_lista_precio` | Sí (`POST`) | Sí (`GET`) | Sí (`GET /{id}`) | Sí (`PUT`) | **Parcial:** solo vía `PUT` con `es_activo` en body; sin `DELETE` lógico ni `POST .../reactivar` como en varios recursos ORG |
| `prc_lista_precio_detalle` | Sí (`POST …/detalles`) | Sí (`GET …/detalles`) | Sí (`GET …/detalles/{id}`) | Sí (`PUT`) | **Parcial:** mismo criterio (`es_activo` en `PUT`); **RBAC ausente en creación** |
| `prc_promocion` | Sí | Sí | Sí | Sí | **Parcial:** solo `PUT` + `es_activo` |

No aplica el patrón transaccional (borrador / aprobar / procesar) de documentos para estas tablas según `PRC_TABLAS.sql`.

---

## 4. Endpoints faltantes o sugeridos (Fase 3)

| Ruta sugerida (bajo `/prc`) | Método | Motivo |
|-----------------------------|--------|--------|
| `/listas-precio/{lista_precio_id}/desactivar` o alinear con ORG: `DELETE` con baja lógica | DELETE o POST | Paridad con estándar “desactivar” sin depender del cliente para armar el body completo del `PUT` |
| `/listas-precio/{lista_precio_id}/reactivar` | POST | Paridad con ORG (`es_activo = 1`) |
| `/promociones/{promocion_id}/desactivar` / `reactivar` | DELETE / POST | Idem |
| Query opcional `empresa_id` en `GET …/listas-precio/{id}` y `GET …/promociones/{id}` | GET | Refuerzo de alcance multi-empresa (patrón ORG en varios recursos) |

**RBAC:** Añadir `Depends(require_permission("prc.lista_precio.crear"))` (o recurso dedicado `lista_precio_detalle` si se separa el permiso) en `POST /listas-precio/{lista_precio_id}/detalles`.

**Seeds RBAC:** No se encontraron inserciones de permisos `prc.*` en los `SEED_PERMISOS*.sql` revisados por búsqueda en el repo; si en BD no existen esos códigos, los endpoints fallarán en 403 salvo administración manual. Conviene añadir seeds en Fase 3 alineados a `prc.lista_precio.{leer,crear,actualizar}` y `prc.promocion.{leer,crear,actualizar}`.

---

## 5. Campos en BD (`PRC_TABLAS.sql`) no reflejados o divergentes en schemas

Comparación explícita contra columnas del script de referencia del módulo.

### 5.1 `prc_lista_precio` ↔ `ListaPrecioCreate` / `Update` / `Read`

| Columna / contrato BD | Observación |
|------------------------|-------------|
| `moneda_id` | En el SQL de referencia existe **`moneda_id`** (UUID, FK `cat_moneda`). Los schemas usan **`moneda`** como texto (código ISO); el ORM `tables_prc.py` también define `moneda` string. Hay **divergencia nombre/tipo** respecto al script `PRC_TABLAS.sql`. |
| Resto de columnas de cabecera | Cubiertas en Read salvo el punto anterior; Create/Update alinean con el modelo actual del código (`moneda` string), no con `moneda_id` del SQL de referencia. |

### 5.2 `prc_lista_precio_detalle` ↔ `ListaPrecioDetalleCreate` / `Update` / `Read`

| Columna BD | Observación |
|--------------|-------------|
| `empresa_id` | Existe en tabla; **`ListaPrecioDetalleRead` no lo expone** (sí se persiste en insert vía derivación desde cabecera en `lista_precio_queries.create_lista_precio_detalle`). Conviene incluirlo en Read para coherencia multi-empresa y con otros módulos. |

### 5.3 `prc_promocion` ↔ `PromocionCreate` / `Update` / `Read`

| Columna BD | Observación |
|--------------|-------------|
| — | Las columnas del script están representadas en los schemas de lectura/escritura con nombres coherentes. El SQL de referencia **no** define `fecha_actualizacion` en promoción; el código tampoco la expone en `PromocionRead` (correcto respecto a ese script). |

---

## 6. Problemas de tenant o RBAC (resumen)

| Problema | Severidad | Ubicación / notas |
|----------|-----------|-------------------|
| `POST …/listas-precio/{lista_precio_id}/detalles` sin `require_permission` | Alta | `endpoints_listas_precio.py` — cualquier usuario autenticado con token podría crear líneas si el resto del stack no bloquea por otro medio. |
| Detalle GET/PUT sin query opcional `empresa_id` | Media | Menor que ORG: las queries filtran por `cliente_id`; la fila incluye `empresa_id` en BD pero no se exige en ruta para reforzar aislamiento por empresa. |
| Permisos `prc.*` posiblemente ausentes en seeds | Media | Riesgo operativo al desplegar en entornos nuevos. |
| Divergencia `moneda` vs `moneda_id` | Alta (si BD = script referencia) | Riesgo de error en runtime o datos inconsistentes si la tabla real usa FK UUID y el código espera string. |

---

## 7. Código marcado como revisión (no eliminar en esta fase)

- Toda la implementación actual de PRC se mantiene; la Fase 3 debe **completar** RBAC en el `POST` de detalle, valorar endpoints de baja/reactivación, alinear schemas con la BD **real** del tenant (respetando la regla de no modificar DDL: si la BD ya es `moneda_id`, ajustar solo capa app/ORM mapeado al contrato existente).
- `tables_prc.py` y `lista_precio_queries.py` son la fuente de verdad del **código** hasta que se alinee con `PRC_TABLAS.sql`; documentar la decisión en `PRC_IMPLEMENTACION.md` en Fase 4.

---

## 8. Checkpoint Fase 2 (respuestas cortas)

1. **Routers / services / queries:** Cubiertos; no hay carpeta `repositories` en el módulo (patrón queries en infraestructura).  
2. **Endpoints:** 8 rutas PRC bajo `/prc` (4 lista + 4 detalle en subárbol listas; 4 promociones).  
3. **Brechas maestro:** Falta RBAC en un `POST`; activar/desactivar solo vía `PUT` con `es_activo` (sin rutas dedicadas estilo ORG).  
4. **Schemas vs BD:** Principal brecha nominal `moneda_id` (BD referencia) vs `moneda` (código); `empresa_id` ausente en `ListaPrecioDetalleRead`.  
5. **Permisos en seeds:** No detectados por búsqueda; asumir pendiente de verificación en BD real.

⛔ **Fin Fase 2.** Continuar con Fase 3 solo tras confirmación explícita.
