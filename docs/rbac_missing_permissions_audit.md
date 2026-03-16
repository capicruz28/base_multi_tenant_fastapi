# Auditoría RBAC: permisos faltantes y por qué el auto-registro no los inserta

**Objetivo:** Diagnóstico exhaustivo (solo análisis, sin modificar código) para entender por qué algunos módulos (CST, MNT y otros) no generan registros en la tabla `permiso` mediante el auto-registro.

**Fecha:** 2026-02-18

**Inventario solicitado:** Se ha escaneado la totalidad de endpoints vía routers en `app/api/v1/api.py` y archivos `endpoints*.py` en `app/modules`. Para cada uno se ha anotado: archivo, router (prefijo), función handler, método HTTP, path, módulo detectado (por prefijo API), RESOURCE_CODE (si existe), si tiene `require_permission`, permiso detectado (string exacto) y patrón (A / B / ninguno). El **inventario resumido por módulo** está en §4; un **inventario detallado por endpoint** para CST y MNT está en Anexo A; el resto de módulos sin RBAC se comportan igual (archivos sin `require_permission`).

---

## 1. Resumen ejecutivo

- **Alineación declarada:** 154 endpoints decorados.
- **Auto-registro:** Inserta correctamente los permisos detectados por introspección (124 permisos en BD).
- **Problema:** Faltan permisos esperados de varios módulos porque **esos endpoints nunca fueron decorados con `require_permission`** y la **inferencia por path** solo aplica a los prefijos `org`, `log` y `admin`. El resto de prefijos (cst, mnt, inv, pur, sls, etc.) no tienen inferencia; por tanto, si no hay `require_permission` en el handler, el permiso no se registra.

**Causa raíz:**  
El auto-registro solo puede insertar un permiso de dos maneras:  
1. **Vía dependencia:** alguna dependencia del endpoint tiene `__permission_codigo__` (o `__permission_metadata__`), es decir, el endpoint usa `Depends(require_permission("modulo.recurso.accion"))`.  
2. **Vía inferencia:** la ruta no tiene permiso declarado pero el path permite inferir módulo y recurso; hoy eso **solo** ocurre para paths que empiezan por `/org`, `/log` o `/admin`.

Los módulos CST, MNT, PUR, SLS, WMS, QMS, CRM, POS, MRP, MPS, TAX, BDG, PM (y otros) no tienen ningún uso de `require_permission` en sus presentaciones, por tanto **ninguno de sus endpoints** aporta permisos al registry y el auto-registro no los inserta. Los permisos de esos módulos solo pueden existir en la tabla `permiso` si se insertan por **seed** (p. ej. `SEED_PERMISOS_RBAC.sql`).

---

## 2. Metodología del análisis

- **Inventario:** Revisión de todos los routers incluidos en `app/api/v1/api.py` y de los archivos `endpoints*.py` bajo `app/modules` para detectar uso de `require_permission`, `MODULE_CODE`, `RESOURCE_CODE` y patrón de permiso.
- **Auto-registro:** Análisis de `app/core/authorization/permission_startup.py` (`ensure_registry_from_routes`, `_infer_module_and_resource`, `_has_permission_dependency`, `_get_dependency_callables`) y de `app/core/authorization/rbac.py` (`require_permission`, atributo `__permission_codigo__`).
- **Comparativa:** Permisos que aparecen en código (strings en `require_permission`) vs permisos que el seed define en la tabla `permiso` (referencia: `app/docs/database/SEED_PERMISOS_RBAC.sql`).
- **Clasificación:** Endpoints alineados ✅, decorados pero no detectables ⚠️, sin RBAC ❌; permisos en código pero ausentes en BD; módulos sin alineación.

---

## 3. Cómo funciona el auto-registro (por qué faltan CST, MNT, etc.)

### 3.1 Flujo en `ensure_registry_from_routes(app)`

1. **Paso 1 – Rutas con permiso declarado**  
   Para cada ruta se obtiene el `dependant` del route y se recorren sus dependencias (`_get_dependency_callables(dependant)`). Si alguna tiene `__permission_codigo__` (o `__permission_metadata__`), se toma ese código (y metadata si existe) y se llama a `register_permission(...)`.  
   - El atributo `__permission_codigo__` lo asigna `require_permission(permission)` en `rbac.py` al callable que devuelve.  
   - Ese callable es el que se pasa a `Depends(require_permission("modulo.recurso.accion"))`. El string se evalúa en tiempo de carga del módulo (p. ej. `f"{MODULE_CODE}.{RESOURCE_CODE}.leer"`), por lo que es introspectable.

2. **Paso 2 – Inferencia por path**  
   Para rutas que **no** tienen dependencia con permiso (`_has_permission_dependency` es False), se intenta inferir permiso con:
   - `_infer_action(methods)` → leer/crear/actualizar/eliminar según GET/POST/PUT-PATCH/DELETE.
   - `_infer_module_and_resource(path)` → **solo** devuelve `modulo_codigo` no nulo si el **primer segmento** del path (tras quitar `/api/v1`) es `org`, `log` o `admin`. Para cualquier otro prefijo (inv, fin, cst, mnt, pur, sls, …) devuelve `modulo_codigo = None` y se hace `continue`, es decir **no se registra nada** por inferencia.

3. **Paso 3**  
   Se vuelve a recorrer rutas para registrar dependencias que tengan `__permission_codigo__` sin metadata (`_register_from_route_dependencies`).

Conclusión: **Un permiso solo se auto-registra si:**  
- el endpoint tiene `Depends(require_permission("modulo.recurso.accion"))` (o equivalente con `__permission_metadata__`), **o**  
- el path permite inferencia y hoy eso **solo** aplica a `/org`, `/log`, `/admin`.

### 3.2 Por qué CST y MNT no generan registros

- En **CST** y **MNT** (y en PUR, SLS, WMS, QMS, CRM, POS, MRP, MPS, TAX, BDG, PM, etc.) **no existe ninguna llamada a `require_permission`** ni definición de `MODULE_CODE`/`RESOURCE_CODE` en sus capas de presentación.
- Sus endpoints solo usan `Depends(get_current_active_user)` (autenticación), sin dependencia de permiso.
- Por tanto:
  - No hay `__permission_codigo__` en ninguna dependencia → el paso 1 no registra nada.
  - El path es `/api/v1/cst/...` o `/api/v1/mnt/...` → el primer segmento no es org/log/admin → `_infer_module_and_resource` devuelve `(None, ...)` → el paso 2 no registra nada.

Los permisos de esos módulos (p. ej. `cst.costo.leer`, `mnt.activo.leer`) **solo** pueden estar en la tabla `permiso` si se insertan por script (seed). El auto-registro **nunca** los crea con la lógica actual.

---

## 4. Inventario por módulo (resumido)

Criterios:

- **Tiene RBAC:** al menos un archivo del módulo usa `require_permission` (o equivalente) en sus endpoints.
- **Patrón:** A = `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.accion")`, B = otro patrón explícito, ninguno = sin decoración RBAC.

| Módulo | Prefijo API | ¿Tiene require_permission? | Patrón | Observación |
|--------|-------------|----------------------------|--------|-------------|
| auth   | /auth       | No (público/config)        | —      | Login, refresh, config; no RBAC de negocio. |
| users  | /usuarios   | Sí                         | A      | endpoints.py con MODULE_CODE/RESOURCE_CODE. |
| rbac   | /roles, /permisos, /permisos-catalogo | Sí | A/B    | endpoints.py, endpoints_permisos, endpoints_permisos_catalogo. |
| menus  | /menus      | Sí                         | A      | endpoints.py, endpoints_areas.py. |
| areas  | /areas      | Sí                         | A      | endpoints_areas. |
| org    | /org        | Sí                         | A      | endpoints_empresa, departamentos, parametros, centros_costo, cargos, sucursales. |
| inv    | /inv        | Sí                         | A      | categorias, productos, almacenes, unidades_medida, movimientos, tipos_movimiento, stock, inventario_fisico. |
| fin    | /fin        | Sí                         | A      | plan_cuentas, periodos, asientos (parcial: no todos los handlers tienen require_permission). |
| log    | /log        | Sí                         | A      | transportistas, vehiculos, rutas, guias_remision, despachos. |
| hcm    | /hcm        | Sí                         | A      | empleados, contratos, conceptos_planilla, planillas, planilla_empleados, planilla_detalle, asistencia, vacaciones, prestamos. |
| tkt    | /tkt        | Sí                         | A      | endpoints_ticket (y posiblemente endpoints.py). |
| svc    | /svc        | Sí                         | A      | endpoints_orden_servicio. |
| mfg    | /mfg        | Sí                         | A      | endpoints_ordenes_produccion. |
| modulos| /modulos-v2, /cliente-modulo, /secciones, /modulos-menus, /plantillas-roles | Sí | A | endpoints_modulos, endpoints_cliente_modulo, endpoints_secciones, endpoints_menus, endpoints_plantillas. |
| aud    | /aud        | Sí                         | A      | endpoints_log_auditoria. |
| dms    | /dms        | Sí                         | A      | endpoints_documento. |
| wfl    | /wfl        | Sí                         | A      | endpoints_flujo_trabajo. |
| bi     | /bi         | Sí                         | A      | endpoints_reporte. |
| **cst**| /cst        | **No**                     | ninguno| endpoints.py, endpoints_centro_costo_tipo, endpoints_producto_costo; solo get_current_active_user. |
| **mnt**| /mnt        | **No**                     | ninguno| endpoints.py, endpoints_activo, endpoints_orden_trabajo, endpoints_plan_mantenimiento, endpoints_historial_mantenimiento; solo get_current_active_user. |
| pur    | /pur        | No                         | ninguno| Sin require_permission. |
| sls    | /sls        | No                         | ninguno| Sin require_permission. |
| invbill| /inv-bill   | No                         | ninguno| Sin require_permission. |
| prc    | /prc        | No                         | ninguno| Sin require_permission. |
| wms    | /wms        | No                         | ninguno| Sin require_permission. |
| qms    | /qms        | No                         | ninguno| Sin require_permission. |
| crm    | /crm        | No                         | ninguno| Sin require_permission. |
| pos    | /pos        | No                         | ninguno| Sin require_permission. |
| mrp    | /mrp        | No                         | ninguno| Sin require_permission. |
| mps    | /mps        | No                         | ninguno| Sin require_permission. |
| tax    | /tax        | No                         | ninguno| Sin require_permission. |
| bdg    | /bdg        | No                         | ninguno| Sin require_permission. |
| pm     | /pm         | No                         | ninguno| Sin require_permission. |
| tenant/superadmin | /clientes, /modulos, /conexiones, /superadmin/* | Parcial / otro | — | Gestión global; no siguen patrón modulo.recurso.accion estándar. |
| metrics| (sin prefijo)| No                         | —      | Métricas; típicamente sin RBAC. |

---

## 5. Clasificación de endpoints y permisos

### A. Endpoints correctamente alineados ✅

- Todos los que tienen `Depends(require_permission("modulo.recurso.accion"))` con string estático (o f-string con constantes de módulo) y cuyo módulo está incluido en la tabla anterior como “Sí” en require_permission.  
- Ejemplos: usuarios, rbac (roles y permisos), menus, areas, org, inv (todos los recursos decorados), fin (plan_cuentas, periodos, y los handlers de asientos que sí llevan require_permission), log (transportistas, vehiculos, rutas, guias_remision, despachos), hcm (empleados, contratos, planillas, etc.), tkt, svc, mfg (ordenes_produccion), modulos (catálogo, secciones, menus, plantillas), aud, dms, wfl, bi.  
- Estos son los que aportan los **124 permisos** que el auto-registro sí inserta en la tabla `permiso` (vía registry + sync).

### B. Endpoints decorados pero no detectables por auto-registro ⚠️

- Casos en los que el permiso no se puede obtener por introspección:
  - **String dinámico:** `require_permission(alguna_variable_o_parametro)` donde el valor no está fijado en tiempo de carga del módulo (no aplica a `f"{MODULE_CODE}.{RESOURCE_CODE}.accion"` con constantes).
  - **Dependencia no inyectada en el handler:** permiso usado en un middleware o en otro lugar que no sea una dependencia del `dependant` del route.
  - **Sub-dependants:** si en el futuro se usaran dependencias anidadas y el scanner no recorriera sub-dependants, podría haber callables con `__permission_codigo__` que no se ven. Hoy `_get_dependency_callables` solo usa `dependant.dependencies` (un nivel); en la práctica los handlers usan Depends a un nivel, por lo que no se han detectado falsos negativos por este motivo.
- En el estado actual del código **no se identifican** endpoints que estén decorados con require_permission y a la vez sean no detectables; los que no se detectan son los que **no tienen** require_permission (clase C).

### C. Endpoints sin decoración RBAC ❌

- **CST:** todos los endpoints (centro_costo_tipo, producto_costo, etc.) solo tienen `Depends(get_current_active_user)`.
- **MNT:** todos los endpoints (activo, orden_trabajo, plan_mantenimiento, historial_mantenimiento) igual.
- **PUR, SLS, INV_BILL, PRC, WMS, QMS, CRM, POS, MRP, MPS, TAX, BDG, PM:** todos sus endpoints, en los archivos revisados, sin `require_permission`.
- **FIN (parcial):** en `endpoints_asientos.py`, algunos handlers (p. ej. listar asientos, crear asiento) no llevan `require_permission`, solo otros (p. ej. get por id, actualizar) sí; los que no lo llevan quedan sin permiso declarado y sin inferencia (porque /fin no está en la inferencia por path).

### D. Permisos definidos en código vs existentes en tabla `permiso`

- **En código (registry tras startup):** los que se obtienen por el paso 1 y 3 de `ensure_registry_from_routes`, es decir, solo los que tienen alguna dependencia con `__permission_codigo__`. En la práctica son los 124 que se sincronizan a BD.
- **En tabla `permiso` (referencia seed):** `SEED_PERMISOS_RBAC.sql` define permisos para admin, modulos, org, inv, wms, qms, pur, log, mfg, mrp, mps, mnt, sls, crm, prc, inv_bill, pos, hcm, fin, tax, bdg, cst, pm, svc, tkt, bi, dms, wfl, aud (decenas de códigos `modulo.recurso.accion`). Si la BD se pobló solo con el **sync** (auto-registro), en la tabla estarán solo esos ~124. Si además se ejecutó el seed, habrá más (los del script).  
- **Faltantes “esperados” desde el punto de vista del seed:** todos los permisos del seed que corresponden a módulos **sin** ningún endpoint con `require_permission` (CST, MNT, PUR, SLS, WMS, QMS, CRM, PRC, INV_BILL, POS, MRP, MPS, TAX, BDG, PM, etc.) no serán generados por el auto-registro; si no se ejecuta el seed, esos códigos no estarán en la tabla.

### E. Módulos completos sin alineación RBAC

- **CST (Costeo):** ningún archivo con require_permission; recursos como centro_costo_tipo, producto_costo sin permiso declarado.  
- **MNT (Mantenimiento):** mismo caso; activo, orden_trabajo, plan_mantenimiento, historial_mantenimiento sin permiso declarado.  
- **PUR, SLS, INV_BILL, PRC, WMS, QMS, CRM, POS, MRP, MPS, TAX, BDG, PM:** ninguno tiene (en el análisis realizado) uso de require_permission en presentación, por tanto módulos completos sin alineación RBAC en código.

---

## 6. Explicación por caso: por qué el auto-registro no insertó el permiso

| Causa | Descripción | Módulos/ejemplos |
|-------|-------------|-------------------|
| **Sin decoración RBAC** | El endpoint no usa `require_permission`; solo autenticación. No hay `__permission_codigo__` en ninguna dependencia. | CST, MNT, PUR, SLS, WMS, QMS, CRM, POS, MRP, MPS, TAX, BDG, PM, INV_BILL, PRC. |
| **Inferencia por path limitada** | `_infer_module_and_resource` solo mapea el primer segmento a módulo para `org`, `log`, `admin`. Para `cst`, `mnt`, `inv`, `fin`, etc., devuelve `modulo_codigo = None` y se omite el registro. | Cualquier ruta bajo /cst, /mnt, /inv, /fin, /pur, … que además no tenga require_permission. |
| **Router cargado pero sin permiso** | El router está incluido en api.py y sus rutas se recorren, pero como no hay dependencia con permiso ni inferencia, no se registra nada. | Todos los módulos de la fila “No” en la tabla del §4. |
| **Endpoint sin require_permission dentro de un módulo parcialmente decorado** | El módulo tiene algunos handlers con require_permission y otros sin él; los que no lo tienen no aportan permiso. | FIN asientos: listar/crear sin require_permission; solo get/put por id (u otros) con require_permission. |
| **Patrón correcto pero no usado** | El estándar `<modulo>.<recurso>.<accion>` es el esperado y es introspectable cuando se usa con `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.accion")`; el problema no es el patrón sino que en esos módulos no se usa en absoluto. | N/A para CST/MNT; aplica a módulos que sí decoran (inv, org, log, etc.). |
| **Dependencia no introspectable** | No aplica en los módulos sin decoración; si en el futuro se usara un string dinámico (variable o parámetro) en require_permission, ese valor no estaría disponible en el callable en tiempo de carga. | No identificado en el estado actual. |

En resumen: **la razón por la que el auto-registro no inserta permisos de CST, MNT y el resto de módulos listados es que ninguno de sus endpoints declara una dependencia con `require_permission`, y la inferencia por path no contempla esos prefijos.**

---

## 7. Comparativa: permisos en código vs en BD

- **Permisos detectados en código (registry):** Los que tienen al menos un endpoint con `Depends(require_permission("..."))`. Coinciden con los que el startup registra y el sync persiste: **~124** (número reportado como insertados correctamente por auto-registro).
- **Permisos existentes en BD (tabla `permiso`):** Si la única fuente es el sync tras el startup, serán los mismos ~124. Si se ejecutó además `SEED_PERMISOS_RBAC.sql`, la tabla puede tener más registros (p. ej. todos los del seed, que cubren los 27+ módulos y admin/modulos).
- **Permisos “faltantes” desde el punto de vista del auto-registro:** Todos los códigos que están en el seed (o que se desearía tener) para módulos que **no** tienen ningún endpoint con require_permission: p. ej. `cst.costo.leer`, `cst.costo.crear`, `mnt.activo.leer`, `mnt.activo.crear`, `pur.orden_compra.leer`, etc. Esos **nunca** serán insertados por el auto-registro con la lógica actual; solo por seed o por decorar esos endpoints y volver a ejecutar el startup/sync.

---

## 8. Conteos finales (resumen)

| Concepto | Valor |
|----------|--------|
| Total de endpoints (rutas de negocio, excl. auth público, docs, métricas) | ~150+ (depende del conteo exacto por router; el informe de alineación citaba 154 decorados, pero muchos módulos no están decorados) |
| Endpoints con RBAC válido (tienen require_permission y son detectables) | Los que corresponden a usuarios, rbac, menus, areas, org, inv, fin (parcial), log, hcm, tkt, svc, mfg, modulos, aud, dms, wfl, bi (~124 permisos únicos registrados) |
| Endpoints sin RBAC (sin require_permission y sin inferencia) | Todos los de CST, MNT, PUR, SLS, INV_BILL, PRC, WMS, QMS, CRM, POS, MRP, MPS, TAX, BDG, PM, más los handlers de FIN (y otros) que no llevan require_permission |
| Permisos detectados en código (registry tras startup) | 124 (según lo reportado) |
| Permisos existentes en BD (si solo sync) | 124 |
| Permisos en seed (SEED_PERMISOS_RBAC.sql) | 132+ (admin, modulos, org, inv, wms, qms, pur, log, mfg, mrp, mps, mnt, sls, crm, prc, inv_bill, pos, hcm, fin, tax, bdg, cst, pm, svc, tkt, bi, dms, wfl, aud) |
| Permisos “faltantes” para el auto-registro | Los del seed (o deseados) que no tienen ningún endpoint con require_permission; p. ej. todos los de CST, MNT, PUR, SLS, WMS, QMS, CRM, PRC, INV_BILL, POS, MRP, MPS, TAX, BDG, PM |

---

## 9. Conclusiones y recomendaciones (solo diagnóstico)

1. **CST y MNT (y otros)** no generan registros en `permiso` por auto-registro porque **no hay ningún uso de `require_permission`** en sus endpoints; la inferencia por path no aplica a los prefijos `/cst` ni `/mnt`.
2. El auto-registro depende de **dependencias con `__permission_codigo__`** (vía `require_permission`) o de la **inferencia** restringida a **org, log, admin**.
3. Para que el auto-registro “poble” permisos de CST, MNT, PUR, SLS, etc., haría falta (en una fase posterior, fuera de esta auditoría):  
   - decorar esos endpoints con `Depends(require_permission("modulo.recurso.accion"))` (o ampliar la inferencia por path a más prefijos, con los riesgos de diseño que eso conlleva).
4. Mientras tanto, los permisos de esos módulos pueden existir en la tabla **solo** si se ejecuta el seed o se insertan manualmente; el comportamiento actual del auto-registro es coherente con el código y con la configuración actual de inferencia.

Esta auditoría es solo análisis; no se ha modificado código ni se ha aplicado ninguna corrección automática.

---

## Anexo A. Inventario detallado (ejemplo: CST y MNT)

Criterios de columnas: archivo, router (prefijo del sub-router), handler, método HTTP, path relativo al prefijo del módulo, módulo detectado, RESOURCE_CODE (si existe), tiene require_permission, permiso detectado (string exacto), patrón (A/B/ninguno).

### CST (Costeo) – Sin RBAC

| Archivo | Router prefix | Handler | Método | Path | Módulo | RESOURCE_CODE | require_permission | Permiso detectado | Patrón |
|---------|----------------|---------|--------|------|--------|---------------|--------------------|-------------------|--------|
| endpoints_centro_costo_tipo.py | /centro-costo-tipo | get_tipos_centro_costo | GET | "" | cst | — | No | — | ninguno |
| endpoints_centro_costo_tipo.py | /centro-costo-tipo | get_tipo_centro_costo | GET | /{cc_tipo_id} | cst | — | No | — | ninguno |
| endpoints_centro_costo_tipo.py | /centro-costo-tipo | post_tipo_centro_costo | POST | "" | cst | — | No | — | ninguno |
| endpoints_centro_costo_tipo.py | /centro-costo-tipo | put_tipo_centro_costo | PUT | /{cc_tipo_id} | cst | — | No | — | ninguno |
| endpoints_producto_costo.py | /producto-costo | (get/list, get by id, post, put) | GET/POST/PUT | "", /{id} | cst | — | No | — | ninguno |
| endpoints.py | (agregador) | — | — | — | cst | — | No | — | ninguno |

**Conclusión CST:** Ningún endpoint define `MODULE_CODE`, `RESOURCE_CODE` ni `require_permission`. Solo `Depends(get_current_active_user)`. El auto-registro no tiene fuente para generar `cst.costo.*` ni `cst.centro_costo_tipo.*`.

### MNT (Mantenimiento) – Sin RBAC

| Archivo | Router prefix | Recursos | Métodos | require_permission | Permiso detectado | Patrón |
|---------|----------------|-----------|---------|---------------------|-------------------|--------|
| endpoints_activo.py | /activos | activo | GET, GET /{id}, POST, PUT | No | — | ninguno |
| endpoints_orden_trabajo.py | /ordenes-trabajo | orden_trabajo | GET, GET /{id}, POST, PUT | No | — | ninguno |
| endpoints_plan_mantenimiento.py | /planes-mantenimiento | plan_mantenimiento | GET, GET /{id}, POST, PUT | No | — | ninguno |
| endpoints_historial_mantenimiento.py | /historial-mantenimiento | historial_mantenimiento | GET, GET /{id}, POST, PUT | No | — | ninguno |
| endpoints.py | (agregador) | — | — | No | — | ninguno |

**Conclusión MNT:** Ningún endpoint define `MODULE_CODE`, `RESOURCE_CODE` ni `require_permission`. El auto-registro no tiene fuente para generar `mnt.activo.*`, `mnt.orden_trabajo.*`, etc.

---

## Anexo B. Permisos definidos en el seed (referencia para comparativa)

El archivo `app/docs/database/SEED_PERMISOS_RBAC.sql` define, entre otros, los siguientes códigos (por módulo). Si la BD se alimenta **solo** por sync del registry, **no** tendrá los de módulos sin ningún endpoint con `require_permission`.

| Módulo | Códigos en seed (ejemplos) | ¿Generados por auto-registro? |
|--------|----------------------------|--------------------------------|
| admin | admin.usuario.leer, .crear, .actualizar, .eliminar; admin.rol.* | Solo si hay endpoints bajo /admin con permiso o inferencia |
| modulos | modulos.menu.leer, .administrar | Sí (menus/modulos decorados) |
| org | org.area.leer, .crear, .actualizar, .eliminar | Sí (org decorado) |
| inv | inv.producto.leer, .crear, .actualizar, .eliminar | Sí (inv decorado) |
| wms, qms, pur, log, mfg, mrp, mps | wms.almacen.*, qms.inspeccion.*, pur.orden_compra.*, log.ruta.*, … | log sí; pur, wms, qms, mfg, mrp, mps: solo mfg tiene algunos decorados; el resto no |
| mnt | mnt.activo.leer, .crear, .actualizar; mnt.orden_trabajo.leer, .crear | **No** (ningún endpoint con require_permission) |
| sls, crm, prc, inv_bill, pos | sls.venta.*, crm.oportunidad.*, prc.precio.*, … | **No** |
| hcm, fin, tax, bdg, cst, pm, svc, tkt, bi, dms, wfl, aud | Varios por recurso | hcm, fin (parcial), svc, tkt, mfg, bi, dms, wfl, aud: sí (decorados). tax, bdg, cst, pm: **No** |

Los 124 permisos que el auto-registro inserta corresponden a los códigos que sí están declarados en algún endpoint (usuarios, rbac, menus, areas, org, inv, fin, log, hcm, tkt, svc, mfg, modulos, aud, dms, wfl, bi). El resto solo pueden estar en BD si se ejecuta el seed o se decoran los endpoints y se vuelve a ejecutar el sync.
