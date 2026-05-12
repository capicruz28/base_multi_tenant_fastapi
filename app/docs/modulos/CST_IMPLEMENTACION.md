# CST — Costos y Costeo — Implementación cerrada

Documento de cierre **Fase 4** del ciclo prompt maestro (lectura → auditoría → implementación → verificación).  
Código del módulo: **CST**. Prefijo de API: **`{API_V1_STR}/cst`** (p. ej. `/api/v1/cst`), definido en `app/api/v1/api.py`.

---

## 1. Alcance y tablas

| Tabla | Rol |
|-------|-----|
| `cst_centro_costo_tipo` | Maestro (tipos de centro de costo; baja lógica con `es_activo`) |
| `cst_producto_costo` | Registro de costeo por producto y período (sin flujo documental borrador/aprobación) |

Referencia de modelo: `docs/bd/CST_TABLAS.sql` y `app/infrastructure/database/tables_erp/tables_cst.py`.  
No se modificó la estructura física de la base de datos en este ciclo.

---

## 2. Archivos creados o modificados

| Archivo | Rol |
|---------|-----|
| `app/modules/cst/presentation/schemas.py` | `ProductoCostoUpdate.fecha_calculo` opcional |
| `app/modules/cst/presentation/endpoints_centro_costo_tipo.py` | Query opcional `empresa_id` en GET/PUT por id; `DELETE`; `POST .../reactivar` |
| `app/modules/cst/presentation/endpoints_producto_costo.py` | Query opcional `empresa_id` en GET/PUT por id |
| `app/modules/cst/application/services/centro_costo_tipo_service.py` | `empresa_id` en get/update; `deactivate_*` / `reactivate_*` |
| `app/modules/cst/application/services/producto_costo_service.py` | `empresa_id` en get/update; `fecha_calculo` en PUT |
| `app/modules/cst/application/services/__init__.py` | Exportes `deactivate_centro_costo_tipo`, `reactivate_centro_costo_tipo` |
| `app/infrastructure/database/queries/cst/centro_costo_tipo_queries.py` | Filtro opcional `empresa_id` en get/update |
| `app/infrastructure/database/queries/cst/producto_costo_queries.py` | Filtro opcional `empresa_id` en get/update |
| `app/docs/database/SEED_PERMISOS_RBAC_CST.sql` | **Nuevo:** MERGE idempotente de permisos CST |
| `app/docs/modulos/AUDITORIA_CST.md` | Auditoría Fase 2 (referencia) |

Sin cambios en `app/modules/cst/presentation/endpoints.py` (prefijos `/tipos-centro-costo` y `/producto-costo`).

---

## 3. Endpoints y contratos

### 3.1 Compatibilidad con rutas y métodos ya existentes

Los endpoints **GET lista**, **GET por id**, **POST** y **PUT** existentes conservan la misma **ruta relativa** y **método**; los `response_model` (`CentroCostoTipoRead`, listas, `ProductoCostoRead`) no cambiaron de forma incompatible.

**Extensión retrocompatible:** en GET y PUT por id se añadió el query opcional **`empresa_id`**. Los clientes que no lo envían conservan el comportamiento anterior (filtro solo por `cliente_id` + PK).

### 3.2 Inventario de rutas (bajo `/cst`)

| Ruta relativa | Método | `response_model` / cuerpo |
|---------------|--------|---------------------------|
| `/tipos-centro-costo` | GET | `list[CentroCostoTipoRead]` |
| `/tipos-centro-costo/{cc_tipo_id}` | GET | `CentroCostoTipoRead` |
| `/tipos-centro-costo` | POST | `CentroCostoTipoRead` |
| `/tipos-centro-costo/{cc_tipo_id}` | PUT | `CentroCostoTipoRead` |
| `/tipos-centro-costo/{cc_tipo_id}` | DELETE | `204` sin cuerpo |
| `/tipos-centro-costo/{cc_tipo_id}/reactivar` | POST | `CentroCostoTipoRead` |
| `/producto-costo` | GET | `list[ProductoCostoRead]` |
| `/producto-costo/{producto_costo_id}` | GET | `ProductoCostoRead` |
| `/producto-costo` | POST | `ProductoCostoRead` |
| `/producto-costo/{producto_costo_id}` | PUT | `ProductoCostoRead` |

### 3.3 Endpoints nuevos — tenant, empresa y RBAC

| Endpoint | `cliente_id` | `empresa_id` | RBAC |
|----------|--------------|--------------|------|
| `DELETE /tipos-centro-costo/{cc_tipo_id}` | Sí (`current_user` → servicios/queries) | Query opcional: si se envía, filtra/actualiza solo si coincide con la fila | `cst.centro_costo_tipo.eliminar` |
| `POST /tipos-centro-costo/{cc_tipo_id}/reactivar` | Sí | Query opcional (mismo criterio) | `cst.centro_costo_tipo.actualizar` |

**Producto costo — PUT:** `cliente_id` en todas las capas; query opcional `empresa_id` en GET/PUT por id; RBAC `cst.producto_costo.actualizar`. En cada **PUT**, si el cuerpo no incluye `fecha_calculo`, el servicio asigna marca de tiempo UTC naive para refrescar el cálculo; si el cliente envía `fecha_calculo`, se respeta.

**Creaciones:** `CentroCostoTipoCreate` y `ProductoCostoCreate` siguen exigiendo `empresa_id` en el body; `cliente_id` lo inyectan las queries.

---

## 4. Seeds RBAC

Script: **`app/docs/database/SEED_PERMISOS_RBAC_CST.sql`**

- `modulo_id` CST: `E1000014-0000-4000-8000-000000000014` (alineado con seeds de menú módulo CST).
- Permisos: `cst.centro_costo_tipo.leer`, `crear`, `actualizar`, `eliminar`; `cst.producto_costo.leer`, `crear`, `actualizar`.
- Alta idempotente con `MERGE` sobre `permiso.codigo`.

Ejecutar en SQL Server después de tener el módulo CST y la tabla `permiso` base cargados.

---

## 5. Verificación Fase 4 (checklist)

1. **Archivos:** listados en la sección 2; cierre del módulo en código y documentación de implementación.
2. **Endpoints nuevos:** `DELETE` y `POST .../reactivar` tipos centro costo cumplen `cliente_id`, validación opcional de `empresa_id` y RBAC indicados arriba.
3. **Endpoints existentes:** no se alteraron ruta, método ni forma del JSON de respuesta de los GET/POST/PUT previos; solo se añadió query opcional `empresa_id` donde se indicó.
4. **Este documento:** `app/docs/modulos/CST_IMPLEMENTACION.md` generado como cierre Fase 4.

---

## 6. Referencias

- Auditoría previa: `app/docs/modulos/AUDITORIA_CST.md`
- Prompt maestro: `docs/prompts/PROMPT_MODULO_MAESTRO.md`

---

**Módulo CST cerrado** en el alcance definido (tipos de centro de costo, costo de producto, permisos seed, endurecimiento opcional por empresa y `fecha_calculo` en actualización de costo de producto).
