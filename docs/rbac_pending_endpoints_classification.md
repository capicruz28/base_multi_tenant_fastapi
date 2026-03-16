# FASE 4 — Normalización semántica de endpoints pendientes

**Fecha:** 2026-02-18  
**Objetivo:** Definir correctamente el modelo de permisos antes de decorar, para garantizar coherencia definitiva del catálogo RBAC.  
**Alcance:** Solo endpoints con riesgo MEDIO y ALTO no decorados en FASE 3.  
**Importante:** Este documento es solo de diseño y validación; no se modifica código hasta su revisión y autorización.

---

## Categorías de clasificación

| Categoría | Descripción | Ejemplo |
|-----------|-------------|---------|
| **SUB_RECURSO** | Recurso lógico independiente bajo una entidad padre (path anidado o detalle). | `/asientos/{id}/detalles`, `/guias-remision/{id}/detalles` |
| **ACCION_NEGOCIO** | Operación no CRUD (activar, aprobar, cerrar, reactivar, reprocesar, etc.). | `PUT /menus/{id}/reactivate/` |
| **CONTEXTUAL_SECURITY** | Acceso basado en usuario actual, self-service o reglas internas (ej. “ver mi perfil” vs “admin ve cualquier usuario”). | `GET /usuarios/{id}/`, `GET /usuarios/{id}/roles/` |
| **SISTEMA** | Auth, health, metrics u otros fuera del RBAC de negocio. | `/auth/*`, `/health`, `/docs` |

---

# Paso 1 — Clasificación obligatoria

Tabla de todos los endpoints pendientes (MEDIO/ALTO), con categoría, recurso y acción RBAC propuestos y nivel de riesgo final.

## 1. LOG (Logística) — Sub-recursos

| Módulo | Archivo | Método | Ruta (sufijo bajo /api/v1) | Función | Categoría | Recurso RBAC propuesto | Acción RBAC propuesta | Riesgo final |
|--------|---------|--------|----------------------------|---------|------------|------------------------|------------------------|---------------|
| log | endpoints_guias_remision.py | GET | /log/guias-remision/{id}/detalles | get_guia_remision_detalles | SUB_RECURSO | guia_remision_detalle | leer | MEDIO |
| log | endpoints_guias_remision.py | POST | /log/guias-remision/{id}/detalles | post_guia_remision_detalle | SUB_RECURSO | guia_remision_detalle | crear | MEDIO |
| log | endpoints_guias_remision.py | GET | /log/guias-remision/detalles/{id} | get_guia_remision_detalle | SUB_RECURSO | guia_remision_detalle | leer | MEDIO |
| log | endpoints_guias_remision.py | PUT | /log/guias-remision/detalles/{id} | put_guia_remision_detalle | SUB_RECURSO | guia_remision_detalle | actualizar | MEDIO |
| log | endpoints_despachos.py | GET | /log/despachos/{id}/guias | get_despacho_guias | SUB_RECURSO | despacho_guia | leer | MEDIO |
| log | endpoints_despachos.py | POST | /log/despachos/{id}/guias | post_despacho_guia | SUB_RECURSO | despacho_guia | crear | MEDIO |
| log | endpoints_despachos.py | GET | /log/despachos/guias/{id} | get_despacho_guia | SUB_RECURSO | despacho_guia | leer | MEDIO |
| log | endpoints_despachos.py | PUT | /log/despachos/guias/{id} | put_despacho_guia | SUB_RECURSO | despacho_guia | actualizar | MEDIO |

## 2. INV (Inventarios) — Consulta contextual

| Módulo | Archivo | Método | Ruta (sufijo bajo /api/v1) | Función | Categoría | Recurso RBAC propuesto | Acción RBAC propuesta | Riesgo final |
|--------|---------|--------|----------------------------|---------|------------|------------------------|------------------------|---------------|
| inv | endpoints_stock.py | GET | /inv/stock/producto/{pid}/almacen/{aid} | stock_por_producto_almacen | SUB_RECURSO | stock | leer | MEDIO |

*Nota:* Es una variante de lectura de stock (por producto+almacén). Recurso lógico sigue siendo `stock`; acción `leer` reutilizable.

## 3. FIN (Finanzas) — Sub-recursos

| Módulo | Archivo | Método | Ruta (sufijo bajo /api/v1) | Función | Categoría | Recurso RBAC propuesto | Acción RBAC propuesta | Riesgo final |
|--------|---------|--------|----------------------------|---------|------------|------------------------|------------------------|---------------|
| fin | endpoints_asientos.py | GET | /fin/asientos/{id}/detalles | get_asiento_detalles | SUB_RECURSO | asiento_detalle | leer | MEDIO |
| fin | endpoints_asientos.py | POST | /fin/asientos/{id}/detalles | post_asiento_detalle | SUB_RECURSO | asiento_detalle | crear | MEDIO |
| fin | endpoints_asientos.py | GET | /fin/asientos/detalles/{id} | get_asiento_detalle | SUB_RECURSO | asiento_detalle | leer | MEDIO |
| fin | endpoints_asientos.py | PUT | /fin/asientos/detalles/{id} | put_asiento_detalle | SUB_RECURSO | asiento_detalle | actualizar | MEDIO |

## 4. USERS — Seguridad contextual

| Módulo | Archivo | Método | Ruta (sufijo bajo /api/v1) | Función | Categoría | Recurso RBAC propuesto | Acción RBAC propuesta | Riesgo final |
|--------|---------|--------|----------------------------|---------|------------|------------------------|------------------------|---------------|
| users | endpoints.py | GET | /usuarios/{id}/ | read_usuario | CONTEXTUAL_SECURITY | usuario | leer | ALTO |
| users | endpoints.py | GET | /usuarios/{id}/roles/ | read_usuario_roles | CONTEXTUAL_SECURITY | rol | leer | ALTO |

*Nota:* Hoy el acceso puede ser “usuario ve su propio perfil” o “admin ve cualquier usuario”. Introducir `admin.usuario.leer` / `admin.rol.leer` **cambia el modelo** (obligaría a tener el permiso para ver cualquier usuario/roles). Decisión de diseño requerida.

## 5. RBAC — Permisos (Rol-Menú)

| Módulo | Archivo | Método | Ruta (sufijo bajo /api/v1) | Función | Categoría | Recurso RBAC propuesto | Acción RBAC propuesta | Riesgo final |
|--------|---------|--------|----------------------------|---------|------------|------------------------|------------------------|---------------|
| rbac | endpoints_permisos.py | PUT | /permisos/roles/{rid}/menus/{mid}/ | (asignar/actualizar) | ACCION_NEGOCIO / asignación | rol | actualizar | MEDIO |
| rbac | endpoints_permisos.py | GET | /permisos/roles/{rid}/permisos/ | (listar permisos rol) | SUB_RECURSO (permisos del rol) | rol | leer | MEDIO |
| rbac | endpoints_permisos.py | GET | /permisos/roles/{rid}/menus/{mid}/ | (detalle) | SUB_RECURSO | rol | leer | MEDIO |
| rbac | endpoints_permisos.py | DELETE | /permisos/roles/{rid}/menus/{mid}/ | (revocar) | ACCION_NEGOCIO | rol | actualizar | MEDIO |

*Nota:* Estos endpoints gestionan la relación rol-menú/permisos. Convención existente: `admin.rol.leer` y `admin.rol.actualizar` [S]. Asignar/revocar menú a rol se modela como `actualizar` rol.

## 6. Menús (legacy) y Áreas

| Módulo | Archivo | Método | Ruta (sufijo bajo /api/v1) | Función | Categoría | Recurso RBAC propuesto | Acción RBAC propuesta | Riesgo final |
|--------|---------|--------|----------------------------|---------|------------|------------------------|------------------------|---------------|
| modulos | endpoints.py (menus) | GET | /menus/getmenu/ | (getmenu) | SUB_RECURSO / lectura | menu | leer | MEDIO |
| modulos | endpoints.py (menus) | GET | /menus/all-structured/ | (all-structured) | SUB_RECURSO | menu | leer | MEDIO |
| modulos | endpoints.py (menus) | POST | /menus/ | (create) | — | menu | administrar | MEDIO |
| modulos | endpoints.py (menus) | GET | /menus/{id}/ | (detail) | SUB_RECURSO | menu | leer | MEDIO |
| modulos | endpoints.py (menus) | PUT | /menus/{id}/ | (update) | — | menu | administrar | MEDIO |
| modulos | endpoints.py (menus) | DELETE | /menus/{id}/ | (delete) | — | menu | administrar | MEDIO |
| modulos | endpoints.py (menus) | PUT | /menus/{id}/reactivate/ | (reactivate) | ACCION_NEGOCIO | menu | administrar | MEDIO |
| modulos | endpoints.py (menus) | GET | /menus/area/{id}/tree/ | (tree) | SUB_RECURSO | menu | leer | MEDIO |
| modulos | endpoints_areas.py | POST | /areas/ | (create) | — | menu | administrar | MEDIO |
| modulos | endpoints_areas.py | GET | /areas/ | (list) | — | menu | leer | MEDIO |
| modulos | endpoints_areas.py | GET | /areas/list/ | (list simple) | — | menu | leer | MEDIO |
| modulos | endpoints_areas.py | GET | /areas/{id}/ | (detail) | — | menu | leer | MEDIO |
| modulos | endpoints_areas.py | PUT | /areas/{id}/ | (update) | — | menu | administrar | MEDIO |
| modulos | endpoints_areas.py | DELETE | /areas/{id}/ | (delete) | — | menu | administrar | MEDIO |
| modulos | endpoints_areas.py | PUT | /areas/{id}/reactivate/ | (reactivate) | ACCION_NEGOCIO | menu | administrar | MEDIO |

*Nota:* Excepción documentada en `rbac_patterns_and_conventions.md`: módulo **modulos** usa `modulos.menu.leer` y `modulos.menu.administrar` para menús, plantillas, secciones y **áreas**. No se crean recursos `modulos.area.*`.

---

# Paso 2 — Propuesta de permisos (sin modificar código)

Para cada endpoint: código `<modulo>.<recurso>.<accion>`, reutilizando permisos existentes cuando sea posible. `[S]` = existente en seed; `[C]` = candidato solo si es estrictamente necesario.

## 2.1 LOG — Sub-recursos

| Endpoint (función) | Permiso propuesto | Reutiliza / [C] |
|-------------------|-------------------|-----------------|
| get_guia_remision_detalles | log.guia_remision_detalle.leer | [C] |
| post_guia_remision_detalle | log.guia_remision_detalle.crear | [C] |
| get_guia_remision_detalle | log.guia_remision_detalle.leer | [C] |
| put_guia_remision_detalle | log.guia_remision_detalle.actualizar | [C] |
| get_despacho_guias | log.despacho_guia.leer | [C] |
| post_despacho_guia | log.despacho_guia.crear | [C] |
| get_despacho_guia | log.despacho_guia.leer | [C] |
| put_despacho_guia | log.despacho_guia.actualizar | [C] |

## 2.2 INV — Stock por producto/almacén

| Endpoint (función) | Permiso propuesto | Reutiliza / [C] |
|-------------------|-------------------|-----------------|
| stock_por_producto_almacen | inv.stock.leer | Reutiliza (mismo recurso y acción que list/detail stock). **[C] ya contemplado en FASE 3 para inv.stock.** |

No se añade permiso nuevo; se usa el mismo `inv.stock.leer` que los demás GET de stock.

## 2.3 FIN — Sub-recursos

| Endpoint (función) | Permiso propuesto | Reutiliza / [C] |
|-------------------|-------------------|-----------------|
| get_asiento_detalles | fin.asiento_detalle.leer | [C] |
| post_asiento_detalle | fin.asiento_detalle.crear | [C] |
| get_asiento_detalle | fin.asiento_detalle.leer | [C] |
| put_asiento_detalle | fin.asiento_detalle.actualizar | [C] |

## 2.4 USERS — Contextual

| Endpoint (función) | Permiso propuesto | Reutiliza / [C] |
|-------------------|-------------------|-----------------|
| read_usuario | admin.usuario.leer | [S] existente en seed. **Uso opcional:** si se decora, quien no tenga permiso no podrá ver ningún usuario (incl. self). Requiere decisión de producto. |
| read_usuario_roles | admin.rol.leer | [S] existente. Misma consideración. |

No se proponen permisos nuevos; se reutilizan códigos del seed. La decisión es **si** se añade la dependencia o se mantiene la lógica actual (ej. “solo admin” o “self o admin”).

## 2.5 RBAC — Permisos rol-menú

| Endpoint (función) | Permiso propuesto | Reutiliza / [C] |
|-------------------|-------------------|-----------------|
| PUT roles/{rid}/menus/{mid} (asignar/actualizar) | admin.rol.actualizar | [S] |
| GET roles/{rid}/permisos/ | admin.rol.leer | [S] |
| GET roles/{rid}/menus/{mid}/ | admin.rol.leer | [S] |
| DELETE roles/{rid}/menus/{mid}/ (revocar) | admin.rol.actualizar | [S] |

Todos reutilizan permisos existentes; no [C].

## 2.6 Menús y Áreas

| Endpoint (función) | Permiso propuesto | Reutiliza / [C] |
|-------------------|-------------------|-----------------|
| getmenu, all-structured, GET menus/{id}, GET menus/area/{id}/tree | modulos.menu.leer | [S] |
| POST/PUT/DELETE menus, reactivate menu | modulos.menu.administrar | [S] |
| POST/GET/PUT/DELETE areas, reactivate area | modulos.menu.leer / modulos.menu.administrar | [S] (según lectura vs escritura) |

Todos reutilizan; no [C]. Escritura/estructura/reactivate → `administrar`; lectura → `leer`.

---

# Paso 3 — Estrategia de alineamiento final

## 3.1 Endpoints que podrán alinearse de forma automática (tras revisión y autorización)

Una vez validado este documento y dado el visto bueno, se podrá decorar **sin decisión de producto adicional**:

| Grupo | Endpoints | Permisos | Nota |
|-------|-----------|----------|------|
| **LOG – guía detalle** | 4 | log.guia_remision_detalle.leer/crear/actualizar [C] | Alta de [C] en `permiso` antes o en mismo ciclo que la decoración. |
| **LOG – despacho-guía** | 4 | log.despacho_guia.leer/crear/actualizar [C] | Idem. |
| **INV – stock por producto/almacén** | 1 | inv.stock.leer (reutilizado) | Sin nuevos permisos. |
| **FIN – asiento detalle** | 4 | fin.asiento_detalle.leer/crear/actualizar [C] | Alta de [C] en `permiso`. |
| **RBAC – permisos rol-menú** | 4 | admin.rol.leer / admin.rol.actualizar [S] | Solo añadir `require_permission` además de `require_admin` si aplica. |
| **Menús y Áreas** | 15 | modulos.menu.leer / modulos.menu.administrar [S] | Solo añadir `require_permission`; hoy pueden usar solo rol. |

**Total alineables automáticamente (tras OK):** 32 endpoints.

## 3.2 Endpoints que requieren decisión manual

| Grupo | Endpoints | Motivo |
|-------|-----------|--------|
| **USERS** | read_usuario, read_usuario_roles (2) | Decisión de producto: ¿obligar `admin.usuario.leer` / `admin.rol.leer` para ver cualquier usuario/roles (rompe “usuario ve solo su perfil” sin permiso)? Opciones: (a) decorar con admin.usuario.leer / admin.rol.leer y restringir “ver otros” a quien tenga el permiso; (b) mantener lógica actual (ej. self + admin por rol) y no integrar en catálogo RBAC granular para estos dos; (c) definir permiso específico tipo “admin.usuario.ver_cualquiera” y mantener self sin permiso. |

**Total que requieren decisión manual:** 2 endpoints.

## 3.3 Endpoints que no deben integrarse al catálogo RBAC de negocio

| Grupo | Endpoints | Motivo |
|-------|-----------|--------|
| **SISTEMA** | `/auth/*` (login, refresh, logout, sessions, SSO, me, permissions/me, menu), `/health`, `/docs`, `/redoc`, `/openapi.json`, `/` | Fuera del modelo de permisos por recurso/acción; protegidos por autenticación o por diseño de infraestructura. No se decoran con `require_permission`. |

No se listan en la tabla de clasificación de Paso 1 porque ya están excluidos por convención del proyecto.

---

## Resumen de candidatos [C] estrictamente necesarios (Paso 2)

Solo para sub-recursos que no están en seed:

| Código | Módulo | Recurso |
|--------|--------|---------|
| log.guia_remision_detalle.leer | log | guia_remision_detalle |
| log.guia_remision_detalle.crear | log | guia_remision_detalle |
| log.guia_remision_detalle.actualizar | log | guia_remision_detalle |
| log.despacho_guia.leer | log | despacho_guia |
| log.despacho_guia.crear | log | despacho_guia |
| log.despacho_guia.actualizar | log | despacho_guia |
| fin.asiento_detalle.leer | fin | asiento_detalle |
| fin.asiento_detalle.crear | fin | asiento_detalle |
| fin.asiento_detalle.actualizar | fin | asiento_detalle |

**inv.stock.leer** ya está como [C] en FASE 3; se reutiliza para `stock_por_producto_almacen` sin nuevo candidato.

---

## Próximos pasos recomendados

1. **Revisar** este documento (clasificación, propuestas de permiso, estrategia).
2. **Decidir** para USERS: decorar con admin.usuario.leer / admin.rol.leer, no decorar, o permiso específico.
3. **Autorizar** la decoración de los 32 endpoints alineables y el alta en tabla `permiso` de los [C] listados.
4. **Tras autorización:** ejecutar decoración (require_permission) y sincronización con tabla `permiso` (seed o auto-registro).

**Este documento no modifica ningún endpoint.** FASE 4 queda como diseño y validación semántica previa al cierre RBAC.
