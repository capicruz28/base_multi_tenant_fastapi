# F12-E2B3O — Runtime Narrative Logging Cleanup Audit (Phase 2)

**Fecha:** 2026-06-25  
**Modo:** Solo auditoría — **sin cambios de código**  
**Referencias:** F12-E2B3I (backlog D/C/B/A), F12-E2B3J (implementación fase 1 auth/users/roles/branding), F12-E2B3N (Platform global query)

---

## 1. Conclusión ejecutiva

F12-E2B3J cerró la **fase 1** del backlog narrativo en el smoke crítico (auth login/refresh, GET usuarios/roles paginados, branding tenant). Queda un **residual significativo** de `logger.info()` con semántica narrativa en módulos Platform Admin, maestros SaaS (menús, módulos, tenant) y mutaciones CRUD (presentation + service duplicado).

| Métrica | Valor |
|---------|------:|
| `logger.info` narrativos activos (inventario) | **179** |
| Clasificación **A** (mantener INFO) | **1** |
| Clasificación **B** (migrar DEBUG) | **178** |
| Archivos afectados | **31** |
| `logger.info` operacionales **A** fuera del scan narrativo (preservar) | **5** |
| Total `logger.info` en `app/` (contexto) | **508** |

**Impacto estimado post-limpieza fase 2:** reducción adicional **~60–75%** de líneas INFO en navegación Platform Admin completa (auditoría + usuarios + menús + módulos + clientes), sin afectar eventos de seguridad (login, logout, `[AUDIT] auth_audit_log`, Redis blacklist, `[MENU_USUARIO]`).

**Restricciones respetadas en esta auditoría:** sin cambios en lógica, SQL, RBAC, Gateway, QueryAuditor, Tenant Filter, Connection Resolver, rutas, contratos HTTP, OpenAPI ni tests.

---

## 2. Metodología

### 2.1 Criterios de inclusión (narrativo activo)

Se escanearon todos los `logger.info()` bajo `app/` cuyo mensaje coincide con patrones narrativos de la fase 2:

- `Solicitud GET|POST|PUT|DELETE…`, `Recibida solicitud`
- `Obteniendo…`, `Listando…`, `Listados…`, `Consultando…`, `Procesando…`
- `Recuperad…`, `…obtenido exitosamente`, `Estadísticas obtenidas…`
- Trazas diagnósticas `[AUDIT]` (lookup CP, **no** persistencia), `[USUARIO]`, `[ACTIVIDAD]`, `[SESIONES]`, `[VALIDAR_ROL]`
- Confirmaciones de mutación `…creado/actualizado/eliminado… exitosamente`

### 2.2 Clasificación A / B (alcance E2B3O)

| Clase | Criterio | Destino fase 2 |
|-------|----------|----------------|
| **A** | Operacional obligatorio: login/logout, `[AUDIT] auth_audit_log`, Redis blacklist, `[MENU_USUARIO]` Inicio/Fin, `[ADMIN]` revocación/cleanup tokens, errores/warnings | **Mantener INFO** |
| **B** | Narrativa request-path, pipeline duplicado presentation↔service, confirmaciones CRUD informales | **Migrar DEBUG** |

> Nota: F12-E2B3I usaba clases C/D adicionales. En E2B3O el residual C/D no migrado en E2B3J se reclasifica como **B** salvo que ya esté gateado por flag.

### 2.3 Frecuencia aproximada

Estimación estática por patrón de emisión (no smoke ejecutado en este ticket):

| Símbolo | Significado |
|---------|-------------|
| **1×/req** | Una línea por invocación HTTP del endpoint |
| **2×/req** | Presentation + service (duplicado típico) |
| **1×/mut** | Una línea por mutación exitosa (POST/PUT/DELETE) |
| **1–3×/pantalla** | Navegación Platform Admin (varias queries internas) |

---

## 3. Clase A — Operacional obligatorio (no migrar)

### 3.1 Dentro del inventario narrativo (excepciones)

| ID | Archivo | Método | Línea | Mensaje | Freq |
|----|---------|--------|------:|---------|------|
| O-007 | `auth/presentation/endpoints.py` | `admin_cleanup_expired_tokens_all_tenants` | 2287 | `logger.info(f"[ADMIN] Solicitud /admin/cleanup-expired-tokens/ por usuario: {use…` | 1×/invocación |

### 3.2 Preservados fuera del scan narrativo (referencia E2B3J)

Estos emisores **no** aparecen como narrativos pero deben permanecer INFO según política acordada:

| Archivo | Línea | Patrón |
|---------|------:|--------|
| `core/security/encryption.py` | 245 | `logger.info("Credencial rotada exitosamente")` |
| `infrastructure/redis/client.py` | 141 | `logger.info("[REDIS_BLACKLIST] Cliente Redis cerrado")` |
| `auth/presentation/endpoints.py` | 485 | `logger.info(f"Usuario {form_data.username} autenticado exitosamente (MOBILE) para cliente {cliente_i` |
| `auth/presentation/endpoints.py` | 2149 | `logger.info(f"[ADMIN] Solicitud de revocación de sesión {token_id} por: {username}")` |
| `auth/presentation/endpoints.py` | 2287 | `logger.info(f"[ADMIN] Solicitud /admin/cleanup-expired-tokens/ por usuario: {username}")` |

Familias adicionales **A** verificadas en E2B3J (no re-auditadas aquí): `[AUTH] Login exitoso`, `[LOGIN-V2]`, `[LOGOUT-V2-*]`, `[AUDIT] auth_audit_log registrado`, `[REDIS_BLACKLIST]`, `[MENU_USUARIO] Inicio/Fin`.

---

## 4. Resumen por archivo (clase B dominante)

| # | Archivo | Ocurrencias B | Riesgo agregado |
|--:|---------|:-------------:|-----------------|
| 1 | `superadmin/application/services/superadmin_auditoria_service.py` | 17 | Medio — útil troubleshooting CP; no sustituye BD audit |
| 2 | `rbac/presentation/endpoints.py` | 13 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 3 | `users/presentation/endpoints.py` | 13 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 4 | `modulos/presentation/endpoints_modulos.py` | 11 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 5 | `tenant/presentation/endpoints_clientes.py` | 11 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 6 | `superadmin/application/services/superadmin_usuario_service.py` | 10 | Bajo |
| 7 | `tenant/application/services/cliente_service.py` | 9 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 8 | `menus/presentation/endpoints.py` | 8 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 9 | `menus/presentation/endpoints_areas.py` | 8 | Bajo — duplica access log / sin valor operacional |
| 10 | `tenant/presentation/endpoints_conexiones.py` | 7 | Bajo — duplica access log / sin valor operacional |
| 11 | `menus/application/services/menu_service.py` | 6 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 12 | `rbac/application/services/permiso_service.py` | 6 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 13 | `rbac/application/services/rol_service.py` | 6 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 14 | `users/application/services/user_service.py` | 6 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 15 | `auth/presentation/endpoints_auth_config.py` | 5 | Bajo — duplica access log / sin valor operacional |
| 16 | `auth/presentation/endpoints_sso.py` | 4 | Bajo — duplica access log / sin valor operacional |
| 17 | `modulos/application/services/cliente_modulo_service.py` | 4 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 18 | `modulos/application/services/modulo_menu_service.py` | 4 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 19 | `modulos/application/services/modulo_service.py` | 4 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 20 | `modulos/presentation/endpoints_cliente_modulo.py` | 4 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 21 | `modulos/presentation/endpoints_menus.py` | 4 | Bajo — duplica access log / sin valor operacional |
| 22 | `auth/presentation/endpoints.py` | 2 (+1 A) | Bajo — duplica access log / sin valor operacional |
| 23 | `rbac/presentation/endpoints_permisos.py` | 3 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 24 | `superadmin/presentation/endpoints_auditoria.py` | 3 | Bajo |
| 25 | `auth/application/services/auth_config_service.py` | 2 | Bajo |
| 26 | `menus/application/services/area_service.py` | 2 | Bajo |
| 27 | `superadmin/presentation/endpoints_usuarios.py` | 2 | Bajo |
| 28 | `core/authorization/permission_catalog_sync_core.py` | 1 | Bajo |
| 29 | `auth/application/services/refresh_token_service.py` | 1 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 30 | `modulos/application/helpers/rol_plantilla_applier.py` | 1 | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth |
| 31 | `tenant/application/services/conexion_service.py` | 1 | Bajo |

---

## 5. Inventario completo — `logger.info` narrativos activos

Inventario **179 entradas** (`O-001` … `O-179`), agrupadas por dominio. El orden de subsecciones es alfabético por etiqueta de dominio; la priorización de limpieza está en §7.

### Menus / Áreas

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-017 | `menus/application/services/area_service.py` | `obtener_areas_paginadas` | 210 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo áreas paginadas para cliente {cliente_id}: skip={skip}, limit={li` |
| O-018 | `menus/application/services/area_service.py` | `obtener_lista_simple_areas_activas` | 405 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo lista simple de áreas activas para cliente {cliente_id}")` |
| O-019 | `menus/application/services/menu_service.py` | `get_menu_for_user` | 74 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo menú filtrado para usuario_id: {usuario_id}")` |
| O-020 | `menus/application/services/menu_service.py` | `obtener_todos_menus_estructurados_admin` | 126 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo estructura completa de menús para cliente {cliente_id}")` |
| O-021 | `menus/application/services/menu_service.py` | `?` | 500 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú ID: {menu_id} del cliente {cliente_id_validacion} actualizado exitosame` |
| O-022 | `menus/application/services/menu_service.py` | `desactivar_menu` | 563 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú ID: {menu_id} desactivado exitosamente.")` |
| O-023 | `menus/application/services/menu_service.py` | `reactivar_menu` | 619 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú ID: {menu_id} reactivado exitosamente.")` |
| O-024 | `menus/application/services/menu_service.py` | `obtener_arbol_menu_por_area` | 663 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo árbol de menú para cliente {cliente_id}, area_id: {area_id}")` |
| O-025 | `menus/presentation/endpoints.py` | `get_menu` | 94 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /menus/getmenu/ recibida para usuario ID: {current_user.usuari` |
| O-026 | `menus/presentation/endpoints.py` | `create_menu_endpoint` | 204 | 1×/request menú-área-módulo | **B** | Bajo | `logger.info(f"Recibida solicitud POST /menus/ por usuario {current_user.usuario_id} del cl` |
| O-027 | `menus/presentation/endpoints.py` | `update_menu_endpoint` | 331 | 1×/request menú-área-módulo | **B** | Bajo | `logger.info(f"Recibida solicitud PUT /menus/{menu_id}/ por usuario {current_user.usuario_i` |
| O-028 | `menus/presentation/endpoints.py` | `deactivate_menu_endpoint` | 404 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /menus/{menu_id}/ recibida (desactivar) por usuario {curren` |
| O-029 | `menus/presentation/endpoints.py` | `deactivate_menu_endpoint` | 415 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú ID {menu_id} desactivado exitosamente")` |
| O-030 | `menus/presentation/endpoints.py` | `reactivate_menu_endpoint` | 464 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /menus/{menu_id}/reactivate/ recibida por usuario {current_use` |
| O-031 | `menus/presentation/endpoints.py` | `reactivate_menu_endpoint` | 475 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú ID {menu_id} reactivado exitosamente")` |
| O-032 | `menus/presentation/endpoints.py` | `get_menu_tree_by_area_endpoint` | 524 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /menus/area/{area_id}/tree/ recibida por usuario {current_user` |
| O-033 | `menus/presentation/endpoints_areas.py` | `crear_area_endpoint` | 86 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /areas/ recibida por usuario {current_user.usuario_id} del cl` |
| O-034 | `menus/presentation/endpoints_areas.py` | `obtener_areas_paginadas_endpoint` | 173 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud GET /areas/ recibida por usuario {current_user.usuario_id} del cl` |
| O-035 | `menus/presentation/endpoints_areas.py` | `obtener_areas_paginadas_endpoint` | 188 | 1×/request menú-área-módulo | **B** | Bajo | `logger.info( f"Lista paginada de áreas recuperada para cliente {current_user.cliente_id} -` |
| O-036 | `menus/presentation/endpoints_areas.py` | `obtener_lista_simple_areas_endpoint` | 242 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /areas/list/ recibida por usuario {current_user.usuario_id} de` |
| O-037 | `menus/presentation/endpoints_areas.py` | `obtener_lista_simple_areas_endpoint` | 247 | 1×/request menú-área-módulo | **B** | Bajo | `logger.info(f"Lista simple de áreas recuperada para cliente {current_user.cliente_id} - To` |
| O-038 | `menus/presentation/endpoints_areas.py` | `actualizar_area_endpoint` | 380 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /areas/{area_id}/ recibida por usuario {current_user.usuario_i` |
| O-039 | `menus/presentation/endpoints_areas.py` | `desactivar_area_endpoint` | 465 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /areas/{area_id}/ recibida (desactivar) por usuario {curren` |
| O-040 | `menus/presentation/endpoints_areas.py` | `reactivar_area_endpoint` | 536 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /areas/{area_id}/reactivate/ recibida por usuario {current_use` |

### Módulos / Menús tenant

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-041 | `modulos/application/helpers/rol_plantilla_applier.py` | `aplicar_plantillas_roles` | 66 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol '{rol_creado['nombre']}' creado con ID {rol_creado['rol_id']}")` |
| O-042 | `modulos/application/services/cliente_modulo_service.py` | `obtener_modulos_activos_cliente` | 69 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo módulos activos para cliente ID: {cliente_id}")` |
| O-043 | `modulos/application/services/cliente_modulo_service.py` | `activar_modulo_cliente` | 366 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"[ACTIVAR] Módulo reactivado exitosamente (ID: {cliente_modulo_id})")` |
| O-044 | `modulos/application/services/cliente_modulo_service.py` | `?` | 401 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"[ACTIVAR] Módulo activado exitosamente con ID: {resultado['cliente_modulo_id` |
| O-045 | `modulos/application/services/cliente_modulo_service.py` | `desactivar_modulo_cliente` | 502 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo {modulo_id} desactivado para cliente {cliente_id} exitosamente.")` |
| O-046 | `modulos/application/services/modulo_menu_service.py` | `crear_menu` | 266 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú creado exitosamente con ID: {resultado['menu_id']}")` |
| O-047 | `modulos/application/services/modulo_menu_service.py` | `obtener_menus_modulo` | 366 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo menús para módulo {modulo_id}, seccion_id={seccion_id}, solo_acti` |
| O-048 | `modulos/application/services/modulo_menu_service.py` | `actualizar_menu` | 691 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú ID {menu_id} actualizado exitosamente.")` |
| O-049 | `modulos/application/services/modulo_menu_service.py` | `eliminar_menu` | 745 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Menú ID {menu_id} eliminado exitosamente.")` |
| O-050 | `modulos/application/services/modulo_service.py` | `obtener_modulos` | 57 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo catálogo de módulos - skip: {skip}, limit: {limit}")` |
| O-051 | `modulos/application/services/modulo_service.py` | `crear_modulo` | 319 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo creado exitosamente con ID: {resultado['modulo_id']}")` |
| O-052 | `modulos/application/services/modulo_service.py` | `actualizar_modulo` | 384 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo ID {modulo_id} actualizado exitosamente.")` |
| O-053 | `modulos/application/services/modulo_service.py` | `eliminar_modulo` | 451 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo ID {modulo_id} desactivado exitosamente.")` |
| O-054 | `modulos/presentation/endpoints_cliente_modulo.py` | `activar_modulo_cliente` | 127 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /cliente-modulo/activar/ - cliente: {modulo_data.cliente_id},` |
| O-055 | `modulos/presentation/endpoints_cliente_modulo.py` | `activar_modulo_cliente` | 135 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo {modulo_data.modulo_id} activado exitosamente para cliente {modulo_da` |
| O-056 | `modulos/presentation/endpoints_cliente_modulo.py` | `desactivar_modulo_cliente` | 184 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /cliente-modulo/cliente/{cliente_id}/modulo/{modulo_id}/ re` |
| O-057 | `modulos/presentation/endpoints_cliente_modulo.py` | `desactivar_modulo_cliente` | 189 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo {modulo_id} desactivado exitosamente para cliente {cliente_id}")` |
| O-058 | `modulos/presentation/endpoints_menus.py` | `obtener_mi_menu` | 74 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /modulos-menus/me/ recibida para usuario {current_user.usuario` |
| O-059 | `modulos/presentation/endpoints_menus.py` | `obtener_mi_menu` | 95 | 1×/GET /auth/me | **B** | Bajo | `logger.info(f"Menú /me/ obtenido exitosamente para usuario {current_user.usuario_id}")` |
| O-060 | `modulos/presentation/endpoints_menus.py` | `obtener_menu_usuario` | 155 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /modulos-menus/usuario/{usuario_id}/ recibida")` |
| O-061 | `modulos/presentation/endpoints_menus.py` | `obtener_menu_usuario` | 168 | 1×/request menú-área-módulo | **B** | Bajo | `logger.info(f"Menú del usuario {usuario_id} obtenido exitosamente")` |
| O-062 | `modulos/presentation/endpoints_modulos.py` | `listar_modulos` | 73 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud GET /modulos/ recibida - skip: {skip}, limit: {limit}, " f"solo_a` |
| O-063 | `modulos/presentation/endpoints_modulos.py` | `listar_modulos` | 98 | 1×/invocación | **B** | Bajo | `logger.info(f"Catálogo de módulos recuperado: {len(modulos)} módulos")` |
| O-064 | `modulos/presentation/endpoints_modulos.py` | `obtener_modulo` | 150 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /modulos/{modulo_id}/ recibida")` |
| O-065 | `modulos/presentation/endpoints_modulos.py` | `obtener_modulo` | 160 | 1×/invocación | **B** | Bajo | `logger.info(f"Módulo {modulo_id} recuperado exitosamente")` |
| O-066 | `modulos/presentation/endpoints_modulos.py` | `obtener_modulo_por_codigo` | 205 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /modulos/codigo/{codigo}/ recibida")` |
| O-067 | `modulos/presentation/endpoints_modulos.py` | `crear_modulo` | 264 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /modulos/ recibida - nombre: {modulo_data.nombre}")` |
| O-068 | `modulos/presentation/endpoints_modulos.py` | `crear_modulo` | 269 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo creado exitosamente con ID: {modulo.modulo_id}")` |
| O-069 | `modulos/presentation/endpoints_modulos.py` | `actualizar_modulo` | 319 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /modulos/{modulo_id}/ recibida")` |
| O-070 | `modulos/presentation/endpoints_modulos.py` | `actualizar_modulo` | 324 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo {modulo_id} actualizado exitosamente")` |
| O-071 | `modulos/presentation/endpoints_modulos.py` | `eliminar_modulo` | 373 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /modulos/{modulo_id}/ recibida")` |
| O-072 | `modulos/presentation/endpoints_modulos.py` | `eliminar_modulo` | 378 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Módulo {modulo_id} eliminado exitosamente")` |

### Core

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-001 | `core/authorization/permission_catalog_sync_core.py` | `sync_permission_catalog` | 67 | 1×/invocación | **B** | Bajo | `logger.info("%s Permission catalog sync: catálogo vacío.", RBAC_LOG_PREFIX)` |

### Platform / Superadmin

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-101 | `superadmin/application/services/superadmin_auditoria_service.py` | `get_logs_autenticacion` | 93 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo logs de autenticación - cliente_id: {cliente_id}, page: {page}")` |
| O-102 | `superadmin/application/services/superadmin_auditoria_service.py` | `obtener_log_autenticacion` | 322 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo log de autenticación ID {log_id}, cliente_id: {cliente_id}")` |
| O-103 | `superadmin/application/services/superadmin_auditoria_service.py` | `obtener_log_autenticacion` | 356 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Cliente_id proporcionado ({cliente_id}), consultando log {log_id} di` |
| O-104 | `superadmin/application/services/superadmin_auditoria_service.py` | `obtener_log_autenticacion` | 383 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Log {log_id} encontrado en BD del cliente {cliente_id}")` |
| O-105 | `superadmin/application/services/superadmin_auditoria_service.py` | `obtener_log_autenticacion` | 400 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Contexto de tenant detectado (cliente_id={context_cliente_id}), busc` |
| O-106 | `superadmin/application/services/superadmin_auditoria_service.py` | `obtener_log_autenticacion` | 412 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Log {log_id} encontrado en BD del tenant {context_cliente_id} (clien` |
| O-107 | `superadmin/application/services/superadmin_auditoria_service.py` | `obtener_log_autenticacion` | 420 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Contexto de SuperAdmin detectado, identificando tenant del log {log_` |
| O-108 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 455 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Cliente_id del log {log_id} obtenido desde BD central: {log_cliente_` |
| O-109 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 463 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Log {log_id} no encontrado en BD central, buscando en BDs Multi-DB")` |
| O-110 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 506 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Cliente_id del log {log_id} obtenido desde BD del cliente {cliente_i` |
| O-111 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 517 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Consultando log {log_id} completo en BD del cliente {log_cliente_id}` |
| O-112 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 528 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Log {log_id} encontrado en BD del cliente {log_cliente_id}")` |
| O-113 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 538 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Log {log_id} no encontrado en contexto del tenant, buscando en todas` |
| O-114 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 562 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Buscando log {log_id} en {len(clientes_ids)} clientes activos: {clie` |
| O-115 | `superadmin/application/services/superadmin_auditoria_service.py` | `?` | 580 | 1–3×/pantalla auditoría Platform | **B** | Medio — útil troubleshooting CP; no sustituye BD audit | `logger.info(f"[AUDIT] Log {log_id} encontrado en BD del cliente {cliente_id}")` |
| O-116 | `superadmin/application/services/superadmin_auditoria_service.py` | `get_logs_sincronizacion` | 682 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo logs de sincronización - page: {page}")` |
| O-117 | `superadmin/application/services/superadmin_auditoria_service.py` | `obtener_estadisticas` | 954 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo estadísticas de auditoría - cliente_id: {cliente_id}")` |
| O-118 | `superadmin/application/services/superadmin_usuario_service.py` | `get_usuarios_globales` | 152 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo usuarios globales - cliente_id: {cliente_id}, page: {page}, limit` |
| O-119 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_usuario_completo` | 426 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo usuario completo ID {usuario_id} (Superadmin), cliente_id: {clien` |
| O-120 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_usuario_completo` | 450 | 1×/detalle usuario Platform | **B** | Bajo — diagnóstico post-E2B3N | `logger.info(f"[USUARIO] Cliente_id del usuario {usuario_id} obtenido desde BD ADMIN: {usua` |
| O-121 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_usuario_completo` | 452 | 1×/detalle usuario Platform | **B** | Bajo — diagnóstico post-E2B3N | `logger.info(f"[USUARIO] Usando cliente_id proporcionado: {usuario_cliente_id}")` |
| O-122 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_actividad_usuario` | 565 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo actividad para usuario {usuario_id}, cliente_id: {cliente_id}")` |
| O-123 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_actividad_usuario` | 599 | 1×/detalle usuario Platform | **B** | Bajo — diagnóstico post-E2B3N | `logger.info(f"[ACTIVIDAD] Cliente_id del usuario {usuario_id} obtenido desde BD ADMIN: {us` |
| O-124 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_actividad_usuario` | 601 | 1×/detalle usuario Platform | **B** | Bajo — diagnóstico post-E2B3N | `logger.info(f"[ACTIVIDAD] Usando cliente_id proporcionado: {usuario_cliente_id}")` |
| O-125 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_sesiones_usuario` | 728 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo sesiones para usuario {usuario_id}, cliente_id: {cliente_id}")` |
| O-126 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_sesiones_usuario` | 755 | 1×/detalle usuario Platform | **B** | Bajo — diagnóstico post-E2B3N | `logger.info(f"[SESIONES] Cliente_id del usuario {usuario_id} obtenido desde BD ADMIN: {usu` |
| O-127 | `superadmin/application/services/superadmin_usuario_service.py` | `obtener_sesiones_usuario` | 757 | 1×/detalle usuario Platform | **B** | Bajo — diagnóstico post-E2B3N | `logger.info(f"[SESIONES] Usando cliente_id proporcionado: {usuario_cliente_id}")` |
| O-128 | `superadmin/presentation/endpoints_auditoria.py` | `list_logs_autenticacion` | 115 | 1×/invocación | **B** | Bajo | `logger.info( f"Logs de autenticación recuperados - " f"Total: {paginated_data['total_logs'` |
| O-129 | `superadmin/presentation/endpoints_auditoria.py` | `list_logs_sincronizacion` | 275 | 1×/invocación | **B** | Bajo | `logger.info( f"Logs de sincronización recuperados - " f"Total: {paginated_data['total_logs` |
| O-130 | `superadmin/presentation/endpoints_auditoria.py` | `get_estadisticas_auditoria` | 342 | 1×/invocación | **B** | Bajo | `logger.info("Estadísticas de auditoría recuperadas exitosamente")` |
| O-131 | `superadmin/presentation/endpoints_usuarios.py` | `list_usuarios_global` | 105 | 1×/invocación | **B** | Bajo | `logger.info( f"Listado global de usuarios recuperado - " f"Total: {paginated_data['total_u` |
| O-132 | `superadmin/presentation/endpoints_usuarios.py` | `list_usuarios_por_cliente` | 373 | 1×/invocación | **B** | Bajo | `logger.info( f"Usuarios del cliente {cliente_id} recuperados - " f"Total: {paginated_data[` |

### Auth / IAM (residual)

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-002 | `auth/application/services/auth_config_service.py` | `obtener_config_cliente` | 99 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo configuración de autenticación para cliente ID: {cliente_id}")` |
| O-003 | `auth/application/services/auth_config_service.py` | `obtener_config_global` | 274 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info("Obteniendo configuración de autenticación global por defecto")` |
| O-004 | `auth/application/services/refresh_token_service.py` | `revoke_token` | 751 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info( f"[REVOKE-TOKEN] Token específico revocado exitosamente - " f"Cliente {client` |
| O-005 | `auth/presentation/endpoints.py` | `get_me` | 899 | 1×/GET /auth/me | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud /me/ recibida para usuario: {current_user.nombre_usuario}")` |
| O-006 | `auth/presentation/endpoints.py` | `logout_all_sessions` | 1831 | 1×/invocación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud /logout_all/ recibida para usuario: {username}")` |
| O-007 | `auth/presentation/endpoints.py` | `admin_cleanup_expired_tokens_all_tenants` | 2287 | 1×/invocación | **A** | N/A — conservar INFO | `logger.info(f"[ADMIN] Solicitud /admin/cleanup-expired-tokens/ por usuario: {username}")` |
| O-008 | `auth/presentation/endpoints_auth_config.py` | `obtener_config_auth_cliente` | 58 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /auth-config/clientes/{cliente_id} recibida")` |
| O-009 | `auth/presentation/endpoints_auth_config.py` | `obtener_config_auth_cliente` | 61 | 1×/auth-config op | **B** | Bajo | `logger.info(f"Configuración de autenticación recuperada para cliente {cliente_id}")` |
| O-010 | `auth/presentation/endpoints_auth_config.py` | `actualizar_config_auth_cliente` | 101 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /auth-config/clientes/{cliente_id} recibida")` |
| O-011 | `auth/presentation/endpoints_auth_config.py` | `obtener_config_auth_global` | 139 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info("Solicitud GET /auth-config/global recibida")` |
| O-012 | `auth/presentation/endpoints_auth_config.py` | `obtener_config_auth_global` | 142 | 1×/auth-config op | **B** | Bajo | `logger.info("Configuración global de autenticación recuperada")` |
| O-013 | `auth/presentation/endpoints_sso.py` | `configurar_azure_ad` | 79 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info("Solicitud POST /sso/azure/config/ recibida")` |
| O-014 | `auth/presentation/endpoints_sso.py` | `configurar_google` | 117 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info("Solicitud POST /sso/google/config/ recibida")` |
| O-015 | `auth/presentation/endpoints_sso.py` | `listar_proveedores_sso` | 153 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info("Solicitud GET /sso/providers/ recibida")` |
| O-016 | `auth/presentation/endpoints_sso.py` | `eliminar_proveedor_sso` | 201 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /sso/{provider_id}/ recibida")` |

### Users

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-161 | `users/application/services/user_service.py` | `obtener_usuario_completo_por_id` | 351 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo usuario completo ID {usuario_id} para cliente {cliente_id}")` |
| O-162 | `users/application/services/user_service.py` | `?` | 564 | 1×/invocación | **B** | Bajo | `logger.info(f"Usuario completo obtenido exitosamente: ID {usuario_id} con {len(usuario_com` |
| O-163 | `users/application/services/user_service.py` | `crear_usuario` | 857 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario creado exitosamente con ID: {result.get('usuario_id')} para cliente ` |
| O-164 | `users/application/services/user_service.py` | `?` | 1020 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario ID {usuario_id} actualizado exitosamente en cliente {cliente_id}")` |
| O-165 | `users/application/services/user_service.py` | `eliminar_usuario` | 1155 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario ID {usuario_id} eliminado lógicamente exitosamente en cliente {clien` |
| O-166 | `users/application/services/user_service.py` | `reactivar_usuario` | 1272 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario ID {usuario_id} reactivado exitosamente en cliente {cliente_id}")` |
| O-167 | `users/presentation/endpoints.py` | `crear_usuario` | 195 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /usuarios/ recibida para crear usuario: '{usuario_in.nombre_u` |
| O-168 | `users/presentation/endpoints.py` | `crear_usuario` | 206 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario '{created_usuario['nombre_usuario']}' creado exitosamente en cliente` |
| O-169 | `users/presentation/endpoints.py` | `actualizar_usuario` | 357 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /usuarios/{usuario_id}/ recibida para actualizar en cliente {c` |
| O-170 | `users/presentation/endpoints.py` | `actualizar_usuario` | 374 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario ID {usuario_id} actualizado exitosamente: '{updated_usuario['nombre_` |
| O-171 | `users/presentation/endpoints.py` | `eliminar_usuario` | 435 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /usuarios/{usuario_id}/ recibida (eliminar lógicamente) en ` |
| O-172 | `users/presentation/endpoints.py` | `eliminar_usuario` | 442 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario ID {usuario_id} eliminado lógicamente exitosamente en cliente {curre` |
| O-173 | `users/presentation/endpoints.py` | `reactivate_usuario` | 484 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud POST /usuarios/{usuario_id}/reactivate/ recibida en cliente {curr` |
| O-174 | `users/presentation/endpoints.py` | `reactivate_usuario` | 492 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Usuario ID {usuario_id} reactivado exitosamente en cliente {current_user.cli` |
| O-175 | `users/presentation/endpoints.py` | `reset_usuario_password_admin` | 547 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( "Solicitud POST /usuarios/%s/reset-password/ por admin %s en cliente %s", usu` |
| O-176 | `users/presentation/endpoints.py` | `assign_rol_to_usuario` | 636 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /usuarios/{usuario_id}/roles/{rol_id}/ recibida en cliente {c` |
| O-177 | `users/presentation/endpoints.py` | `assign_rol_to_usuario` | 661 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol {rol_id} asignado exitosamente al usuario {usuario_id} en cliente {curre` |
| O-178 | `users/presentation/endpoints.py` | `revoke_rol_from_usuario` | 725 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /usuarios/{usuario_id}/roles/{rol_id}/ recibida en cliente ` |
| O-179 | `users/presentation/endpoints.py` | `revoke_rol_from_usuario` | 739 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol {rol_id} revocado exitosamente del usuario {usuario_id} en cliente {curr` |

### RBAC

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-073 | `rbac/application/services/permiso_service.py` | `_validar_rol_y_menu` | 75 | 1×/invocación | **B** | Bajo | `logger.info(f"[VALIDAR_ROL] Rol ID: {rol_id}, Rol cliente_id (raw): {rol_cliente_id_raw} (` |
| O-074 | `rbac/application/services/permiso_service.py` | `_validar_rol_y_menu` | 107 | 1×/invocación | **B** | Bajo | `logger.info(f"[VALIDAR_ROL] Después de normalización - Rol cliente_id: {rol_cliente_id}, C` |
| O-075 | `rbac/application/services/permiso_service.py` | `_validar_rol_y_menu` | 121 | 1×/invocación | **B** | Bajo | `logger.info(f"[VALIDAR_ROL] Validación exitosa - Rol {rol_id} es {'rol del sistema' if es_` |
| O-076 | `rbac/application/services/permiso_service.py` | `?` | 318 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Permiso ID {perm_id} actualizado exitosamente para cliente {cliente_id}")` |
| O-077 | `rbac/application/services/permiso_service.py` | `?` | 364 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Permiso creado exitosamente con ID {result['permiso_id']} para cliente {clie` |
| O-078 | `rbac/application/services/permiso_service.py` | `revocar_permiso` | 559 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Permiso revocado exitosamente - Cliente: {cliente_id}, Rol: {rol_id}, Menú: ` |
| O-079 | `rbac/application/services/rol_service.py` | `crear_rol` | 351 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol '{result.get('nombre')}' creado con ID: {result.get('rol_id')} para clie` |
| O-080 | `rbac/application/services/rol_service.py` | `actualizar_rol` | 695 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol '{result.get('nombre')}' actualizado exitosamente")` |
| O-081 | `rbac/application/services/rol_service.py` | `desactivar_rol` | 791 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol ID {rol_id} desactivado exitosamente")` |
| O-082 | `rbac/application/services/rol_service.py` | `reactivar_rol` | 887 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol ID {rol_id} reactivado exitosamente")` |
| O-083 | `rbac/application/services/rol_service.py` | `obtener_permisos_por_rol` | 981 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo permisos para el rol ID: {rol_id}")` |
| O-084 | `rbac/application/services/rol_service.py` | `actualizar_permisos_rol` | 1140 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Permisos actualizados exitosamente para el rol ID: {rol_id}")` |
| O-085 | `rbac/presentation/endpoints.py` | `create_rol` | 112 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /roles/ recibida por usuario {current_user.usuario_id} del cl` |
| O-086 | `rbac/presentation/endpoints.py` | `create_rol` | 144 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol '{created_rol['nombre']}' creado exitosamente en cliente {current_user.c` |
| O-087 | `rbac/presentation/endpoints.py` | `read_all_active_roles` | 279 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud GET /roles/all-active/ recibida por usuario {current_user.usuario` |
| O-088 | `rbac/presentation/endpoints.py` | `read_all_active_roles` | 290 | 1×/invocación | **B** | Bajo | `logger.info( f"Lista simple de roles activos recuperada para cliente {session_client_id} "` |
| O-089 | `rbac/presentation/endpoints.py` | `update_rol` | 421 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /roles/{rol_id}/ recibida por usuario {current_user.usuario_id` |
| O-090 | `rbac/presentation/endpoints.py` | `update_rol` | 445 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol ID {rol_id} actualizado exitosamente: '{updated_rol['nombre']}'")` |
| O-091 | `rbac/presentation/endpoints.py` | `deactivate_rol` | 499 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /roles/{rol_id}/ recibida (desactivar) por usuario {current` |
| O-092 | `rbac/presentation/endpoints.py` | `deactivate_rol` | 514 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol ID {rol_id} desactivado exitosamente en cliente {current_user.cliente_id` |
| O-093 | `rbac/presentation/endpoints.py` | `reactivate_rol` | 564 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /roles/{rol_id}/reactivate/ recibida por usuario {current_use` |
| O-094 | `rbac/presentation/endpoints.py` | `reactivate_rol` | 579 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Rol ID {rol_id} reactivado exitosamente en cliente {current_user.cliente_id}` |
| O-095 | `rbac/presentation/endpoints.py` | `update_permisos_rol` | 712 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Permisos para rol {rol_id} actualizados exitosamente")` |
| O-096 | `rbac/presentation/endpoints.py` | `get_permisos_negocio_rol` | 745 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /roles/{rol_id}/permisos-negocio/ por usuario {current_user.us` |
| O-097 | `rbac/presentation/endpoints.py` | `update_permisos_negocio_rol` | 789 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /roles/{rol_id}/permisos-negocio/ por usuario {current_user.us` |
| O-098 | `rbac/presentation/endpoints_permisos.py` | `set_permission` | 118 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /permisos/roles/{rol_id}/menus/{menu_id}/ recibida por usuario` |
| O-099 | `rbac/presentation/endpoints_permisos.py` | `revoke_permission` | 330 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /permisos/roles/{rol_id}/menus/{menu_id}/ recibida por usua` |
| O-100 | `rbac/presentation/endpoints_permisos.py` | `revoke_permission` | 337 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Permiso para Rol {rol_id} y Menú {menu_id} revocado exitosamente en cliente ` |

### Tenant / Clientes / Conexiones

| ID | Archivo | Método | Línea | Freq | Clase | Riesgo DEBUG | Mensaje (truncado) |
|----|---------|--------|------:|------|:-----:|--------------|-------------------|
| O-133 | `tenant/application/services/cliente_service.py` | `suspender_cliente` | 289 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Cliente ID {cliente_id} suspendido exitosamente.")` |
| O-134 | `tenant/application/services/cliente_service.py` | `activar_cliente` | 359 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Cliente ID {cliente_id} activado exitosamente.")` |
| O-135 | `tenant/application/services/cliente_service.py` | `?` | 497 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Cliente ID {cliente_id} actualizado exitosamente.")` |
| O-136 | `tenant/application/services/cliente_service.py` | `eliminar_cliente` | 543 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Cliente ID {cliente_id} eliminado exitosamente (marcado como inactivo).")` |
| O-137 | `tenant/application/services/cliente_service.py` | `listar_clientes` | 561 | 1×/listado GET | **B** | Bajo | `logger.info( f"Listando clientes - skip: {skip}, limit: {limit}, " f"solo_activos: {solo_a` |
| O-138 | `tenant/application/services/cliente_service.py` | `listar_clientes` | 625 | 1×/listado GET | **B** | Bajo | `logger.info(f"Listados {len(clientes)} clientes de {total} totales")` |
| O-139 | `tenant/application/services/cliente_service.py` | `obtener_estadisticas` | 635 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo estadísticas para cliente ID: {cliente_id}")` |
| O-140 | `tenant/application/services/cliente_service.py` | `obtener_estadisticas` | 714 | 1×/invocación | **B** | Bajo | `logger.info(f"Estadísticas obtenidas para cliente {cliente_id}")` |
| O-141 | `tenant/application/services/cliente_service.py` | `get_branding_by_subdomain` | 893 | 1×/invocación | **B** | Bajo | `logger.info(f"Branding obtenido exitosamente para subdominio={subdominio}")` |
| O-142 | `tenant/application/services/conexion_service.py` | `obtener_conexiones_cliente` | 46 | 1×/service call (duplica presentation) | **B** | Bajo | `logger.info(f"Obteniendo conexiones para cliente ID: {cliente_id}")` |
| O-143 | `tenant/presentation/endpoints_clientes.py` | `crear_cliente` | 116 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud POST /clientes/ recibida para crear cliente: '{cliente_data.razon` |
| O-144 | `tenant/presentation/endpoints_clientes.py` | `crear_cliente` | 122 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Cliente '{created_cliente.razon_social}' creado con ID: {created_cliente.cli` |
| O-145 | `tenant/presentation/endpoints_clientes.py` | `listar_clientes` | 170 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud GET /clientes/ recibida - skip: {skip}, limit: {limit}, " f"solo_` |
| O-146 | `tenant/presentation/endpoints_clientes.py` | `obtener_cliente` | 224 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /clientes/{cliente_id} recibida por usuario: {current_user.nom` |
| O-147 | `tenant/presentation/endpoints_clientes.py` | `actualizar_cliente` | 421 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud PUT /clientes/{cliente_id} recibida para actualizar " f"por usuar` |
| O-148 | `tenant/presentation/endpoints_clientes.py` | `actualizar_cliente` | 426 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Cliente {cliente_id} actualizado exitosamente")` |
| O-149 | `tenant/presentation/endpoints_clientes.py` | `eliminar_cliente` | 467 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /clientes/{cliente_id} recibida por usuario: {current_user.` |
| O-150 | `tenant/presentation/endpoints_clientes.py` | `eliminar_cliente` | 469 | 1×/mutación exitosa | **B** | Bajo–Medio — trazabilidad informal; auth_audit_log cubre auth | `logger.info(f"Cliente {cliente_id} eliminado exitosamente")` |
| O-151 | `tenant/presentation/endpoints_clientes.py` | `suspender_cliente` | 507 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud PUT /clientes/{cliente_id}/suspender recibida por usuario: {curre` |
| O-152 | `tenant/presentation/endpoints_clientes.py` | `activar_cliente` | 551 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud PUT /clientes/{cliente_id}/activar recibida por usuario: {current` |
| O-153 | `tenant/presentation/endpoints_clientes.py` | `obtener_estadisticas_cliente` | 591 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info( f"Solicitud GET /clientes/{cliente_id}/estadisticas recibida por usuario: {cu` |
| O-154 | `tenant/presentation/endpoints_conexiones.py` | `listar_conexiones_cliente` | 60 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /conexiones/clientes/{cliente_id} recibida")` |
| O-155 | `tenant/presentation/endpoints_conexiones.py` | `listar_conexiones_cliente` | 62 | 1×/invocación | **B** | Bajo | `logger.info(f"Conexiones recuperadas para cliente {cliente_id}: {len(conexiones)} conexion` |
| O-156 | `tenant/presentation/endpoints_conexiones.py` | `obtener_conexion_principal` | 94 | 1×/request GET | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud GET /conexiones/clientes/{cliente_id}/principal recibida")` |
| O-157 | `tenant/presentation/endpoints_conexiones.py` | `crear_conexion` | 135 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /conexiones/clientes/{cliente_id} recibida")` |
| O-158 | `tenant/presentation/endpoints_conexiones.py` | `actualizar_conexion` | 176 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud PUT /conexiones/{conexion_id} recibida")` |
| O-159 | `tenant/presentation/endpoints_conexiones.py` | `desactivar_conexion` | 211 | 1×/request mutación | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud DELETE /conexiones/{conexion_id} recibida")` |
| O-160 | `tenant/presentation/endpoints_conexiones.py` | `test_conexion` | 242 | 1×/request POST | **B** | Bajo — duplica access log / sin valor operacional | `logger.info(f"Solicitud POST /conexiones/test recibida para servidor: {conexion_test.servi` |

---

## 6. Matriz de riesgo al migrar B → DEBUG

| Nivel | Descripción | Módulos / patrones | Mitigación |
|-------|-------------|-------------------|------------|
| **Bajo** | Duplica access log HTTP o trazabilidad informal sin SLA operacional | Presentation `Solicitud GET…`, mutaciones CRUD, maestros menús/módulos | Migración directa; validar smoke Platform + Shared |
| **Bajo–Medio** | Confirmación mutación sin registro formal en `auth_audit_log` | Users/RBAC/Tenant DELETE/POST success | Mantener `[AUDIT]` BD para auth; DEBUG suficiente para maestros ERP |
| **Medio** | Trazas lookup multi-BD útiles en troubleshooting CP | `superadmin_auditoria_service` `[AUDIT]` resolución | Migrar DEBUG; documentar que troubleshooting CP requiere `LOG_LEVEL=DEBUG` |
| **N/A** | Clase A — no migrar | Admin cleanup/revocación, login, redis, menu inicio/fin | Sin acción |

**Riesgos explícitamente descartados:** no se pierde auditoría formal (persistida en BD), no afecta RBAC traces (ya gateados), no oculta errores (WARNING/ERROR intactos).

---

## 7. Orden recomendado de limpieza (implementación futura)

Prioridad por **impacto volumétrico en smoke Platform Admin** y **bajo riesgo**, sin tocar clase A.

### Onda 1 — Platform Admin presentation (impacto inmediato smoke E2B3M)

| Prioridad | Archivos | Ocurrencias | Justificación |
|-----------|----------|:-----------:|---------------|
| **P1** | `superadmin/presentation/endpoints_auditoria.py`, `endpoints_usuarios.py` | 5 | 1×/req en pantallas auditadas en E2B3M; riesgo bajo |
| **P1** | `superadmin/application/services/superadmin_auditoria_service.py` | 17 | Mayor volumen CP; `[AUDIT]` lookup ≠ persistencia |
| **P1** | `superadmin/application/services/superadmin_usuario_service.py` | 10 | `[USUARIO]`/`[ACTIVIDAD]`/`[SESIONES]` post-E2B3N |

### Onda 2 — Presentation SaaS maestros (alto volumen, bajo riesgo)

| Prioridad | Archivos | Ocurrencias | Justificación |
|-----------|----------|:-----------:|---------------|
| **P2** | `rbac/presentation/endpoints.py` | 13 | Mutaciones + GET permisos; duplica service |
| **P2** | `users/presentation/endpoints.py` | 13 | Idem usuarios tenant admin |
| **P2** | `modulos/presentation/endpoints_modulos.py` | 11 | Catálogo módulos Platform |
| **P2** | `tenant/presentation/endpoints_clientes.py` | 11 | Clientes + branding residual POST/PUT |
| **P2** | `menus/presentation/endpoints.py`, `endpoints_areas.py` | 16 | Áreas/menús administración |

### Onda 3 — Services pipeline duplicado (consolidar emisor único)

| Prioridad | Archivos | Ocurrencias | Justificación |
|-----------|----------|:-----------:|---------------|
| **P3** | `tenant/application/services/cliente_service.py` | 9 | Duplica presentation clientes |
| **P3** | `menus/application/services/menu_service.py`, `area_service.py` | 8 | Pipeline menú |
| **P3** | `rbac/application/services/rol_service.py`, `permiso_service.py` | 12 | Pipeline roles/permisos |
| **P3** | `users/application/services/user_service.py` | 6 | Pipeline usuarios |
| **P3** | `modulos/application/services/*` | 12 | Módulos/menús tenant |

### Onda 4 — Residual auth/config y core

| Prioridad | Archivos | Ocurrencias | Justificación |
|-----------|----------|:-------------:|---------------|
| **P4** | `auth/presentation/endpoints_auth_config.py`, `endpoints_sso.py`, `auth_config_service.py` | 11 | Baja freq admin auth-config |
| **P4** | `auth/presentation/endpoints.py` (residual `/me/`, `/logout_all/`) | 3 | E2B3J no migró `/me/` ni logout_all narrative |
| **P4** | `tenant/presentation/endpoints_conexiones.py`, `conexion_service.py` | 8 | Conexiones BD tenant |
| **P4** | `core/authorization/permission_catalog_sync_core.py`, helpers varios | 3 | Startup/sync esporádico |

### Reglas de implementación (fase código — fuera de alcance E2B3O)

1. Solo cambiar nivel `info` → `debug` en entradas clase **B**; no eliminar mensajes.
2. **No** migrar entradas clase **A** (tabla §3).
3. Preferir migrar **presentation + service** del mismo flujo en el mismo PR por onda.
4. Validación: smoke Platform (`superadmin`) + Shared (`admin`) con `LOG_LEVEL=INFO`, flags OFF — paridad E2B3J.
5. Opcional troubleshooting: repetir smoke con `LOG_LEVEL=DEBUG` para confirmar emisores.

---

## 8. Estimación volumétrica post-implementación

| Escenario | INFO narrativos (aprox.) | Notas |
|-----------|-------------------------:|-------|
| **Actual** (post-E2B3J, Platform nav completa) | **~120–160** líneas/ciclo | Depende pantallas visitadas; 179 emisores en código |
| **Post onda 1** (superadmin) | **−35~40** | Mayor ROI smoke E2B3M |
| **Post ondas 1–3** | **−150~170** | Casi cero narrativa INFO en maestros |
| **Post ondas 1–4** (completo) | **~0–5** INFO narrativos | Solo clase A residual |

---

## 9. Relación con fases anteriores

| Fase | Estado | Relación E2B3O |
|------|--------|----------------|
| F12-E2B3I | Backlog D/C/B/A definido | E2B3O = residual **no cubierto** por smoke E2B3J |
| F12-E2B3J | Auth/users/roles/branding migrados | Confirma 0 INFO narrativo en esos flujos GET |
| F12-E2B3N | Platform global query | Explica trazas `[USUARIO]`/`[SESIONES]` — candidatas B |
| **F12-E2B3O** | **Esta auditoría** | Inventario 179 → implementación futura por ondas |

---

## 10. Entregable y límites

- **Entregable:** este documento (`F12_E2B3O_RUNTIME_NARRATIVE_LOGGING_AUDIT.md`).
- **Sin implementación de código** en E2B3O.
- **Sin commits** en E2B3O.
- Inventario generado por escaneo estático `app/**/*.py` (2026-06-25); IDs `O-001`…`O-{len(entries):03d}`.

