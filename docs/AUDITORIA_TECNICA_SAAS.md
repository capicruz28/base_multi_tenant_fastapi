# Auditoría técnica SaaS – Base Multi-Tenant FastAPI

**Fecha:** Febrero 2025  
**Alcance:** Arquitectura multi-tenant, seguridad, aislamiento, escalabilidad, BD, errores/logging, riesgos de fuga de datos, producción y buenas prácticas SaaS.

---

## 1. Arquitectura multi-tenant

### Implementación actual

- **Modelo híbrido:** Single-DB (shared) + Multi-DB (dedicated) con routing por `cliente_conexion` y `TenantContext.database_type`.
- **Resolución de tenant:** Subdominio → BD (tabla `cliente`) → `cliente_id` + metadata de conexión.
- **Contexto:** `ContextVar` (`current_client_id`, `current_tenant_context`) con establecimiento en `TenantMiddleware` y limpieza en `finally`.
- **Conexiones:** `get_connection_for_tenant()` en `app/core/tenant/routing.py` centraliza el routing; BD dedicada usa credenciales de `cliente_conexion` (desencriptadas).

### Fortalezas

- Separación clara Single vs Multi-DB.
- Cache de metadata de conexión (`connection_cache`).
- Fallback a Single-DB si no hay metadata o falla la conexión dedicada.

### Debilidades / riesgos

- **Host en desarrollo:** En desarrollo se usa `Origin`/`Referer` como fallback para el tenant; aunque se valida subdominio en BD, sigue siendo una superficie de ataque mayor que en producción.
- **Superadmin por defecto sin subdominio:** Si no hay subdominio se usa `SUPERADMIN_CLIENTE_ID`; en producción un error de DNS o proxy podría enviar tráfico a “sin subdominio” y asignarlo al sistema.
- **Pool key por tenant:** En `connection_pool.py`, `_get_pool_for_tenant(client_id: int, ...)` está tipado como `int` pero se usa con `UUID`; el código funciona porque se interpola en string, pero la firma es engañosa.

---

## 2. Seguridad (auth, tokens, permisos)

### Auth y tokens

- **Access token:** JWT con `sub`, `jti`, `type`, `access_level`, `is_super_admin`, `user_type`. En el **login por password** se incluye `cliente_id` en el payload (endpoints ~líneas 202–206).
- **Validación de tenant en token:** `ENABLE_TENANT_TOKEN_VALIDATION=true` y en `AuthService.get_current_user()` se compara `token_cliente_id` con `current_cliente_id`; si no coinciden (y no es superadmin) se rechaza.
- **Refresh token:** Almacenado por hash en BD, asociado a `cliente_id` y `usuario_id`; validación en `RefreshTokenService.validate_refresh_token()` usa `get_current_client_id()` para acotar por tenant.
- **Revocación:** Blacklist por `jti` en Redis; si Redis falla, el código hace fail-soft y no bloquea el acceso (tokens revocados podrían seguir válidos hasta expiración).
- **Rotación:** Rotación de refresh con detección de reuso y revocación de todas las sesiones del usuario en caso de reuso en login.

### RBAC / LBAC

- **RoleChecker:** Compara `current_user.access_level` con nivel mínimo requerido por roles (`RolService.get_min_required_access_level`).
- **Permisos por menú:** `rol_menu_permiso` con flags (puede_ver, puede_crear, etc.); en BD dedicada `menu_id` referencia `modulo_menu` en **BD central** (cross-database, sin FK).

### Hallazgos críticos de seguridad

1. **SSO (Azure AD / Google):** En `endpoints.py` (~1107 y ~1230), los tokens se crean solo con `{"sub": user_full_data['nombre_usuario']}` **sin `cliente_id`**. Cuando SSO esté implementado, esos tokens no llevarán tenant en el payload y la validación `token_cliente_id != current_cliente_id` no podrá aplicarse correctamente (payload sin `cliente_id`).
2. **Token sin `jti`:** Si por un bug se emite un token sin `jti`, no se puede revocar vía Redis; el código solo registra un warning y sigue.
3. **Redis fail-soft:** Con Redis caído, la revocación no se aplica; riesgo aceptable si está documentado, pero debe estar asumido y monitoreado.

---

## 3. Aislamiento por cliente

### Capas de aislamiento

1. **Middleware:** Tenant fijado por subdominio; request sin tenant válido → 404.
2. **Auth:** Usuario resuelto en la BD del tenant (Single o Multi); `validate_tenant_access()` impide que un usuario de tenant A use el token en tenant B (y token con `cliente_id` lo refuerza en login password).
3. **Queries:** `execute_query` aplica `apply_tenant_filter()` (solo SQLAlchemy Core) y opcionalmente `QueryAuditor.validate_tenant_filter()`.
4. **Tablas globales:** `GLOBAL_TABLES = {'cliente', 'cliente_modulo', 'cliente_conexion', 'sistema_config'}` no reciben filtro de tenant.

### Riesgos de fuga entre tenants

- **Queries raw/TextClause:** Para `TextClause` y string SQL, el auditor solo hace análisis de string (búsqueda de `cliente_id =`). Un `WHERE` con alias o subquery podría no detectarse; además, **no se aplica** `apply_tenant_filter()` a `TextClause` ni a string SQL, solo a objetos Core. Por tanto, las queries que usan `text(...).bindparams()` dependen 100% de que el desarrollador incluya `cliente_id`; no hay inyección automática.
- **execute_auth_query:** No recibe `client_id`; usa `_get_connection_context(connection_type)` sin `client_id`, por lo que en DEFAULT toma el contexto actual. Correcto si se llama siempre dentro de un request con tenant; en jobs o scripts sin contexto podría usar conexión equivocada.
- **Tablas de catálogo central:** `modulo`, `modulo_seccion`, `modulo_menu` están solo en BD central. Las consultas que las usan sin `cliente_id` (p. ej. por `modulo_id`) pueden ser marcadas por el auditor como “sin filtro tenant”. Hoy `GLOBAL_TABLES` no incluye estas tablas; o se amplía la lista (con cuidado con `modulo_menu.cliente_id`) o se documentan excepciones para no generar falsos positivos en producción.
- **BD dedicada y `rol_menu_permiso.menu_id`:** La FK lógica a `modulo_menu` está en otra BD; no hay validación en BD de que `menu_id` exista. La aplicación debe validar o usar una capa que consulte la central; riesgo de datos huérfanos o inconsistentes si no se hace.

---

## 4. Escalabilidad horizontal

- **Stateless API:** Contexto en `ContextVar`; una instancia no guarda estado de tenant entre requests; adecuado para varias réplicas detrás de un balanceador.
- **Connection pooling:** Por tenant en Multi-DB (`tenant_{client_id}`), con límite `MAX_TENANT_POOLS=200`, limpieza LRU por inactividad (`POOL_INACTIVITY_TIMEOUT`), y evicción cuando se alcanza el límite.
- **Redis:** Usado para blacklist de `jti`; si se usa para cache (p. ej. `ENABLE_REDIS_CACHE`), hay que definir estrategia de clave por tenant para no mezclar datos.
- **Limitación:** Con muchos tenants dedicados, 200 pools y 5+3 conexiones por pool pueden ser muchos file descriptors y memoria; conviene métricas y alertas (p. ej. `get_pool_stats()`).

---

## 5. Índices y rendimiento de base de datos

### TABLAS_BD_CENTRAL.sql

- **cliente:** `UQ_cliente_subdominio` (WHERE es_activo=1), `IDX_cliente_codigo`, `IDX_cliente_estado`, `IDX_cliente_tipo` — adecuado para resolución por subdominio y filtros por estado/tipo.
- **cliente_conexion:** `IDX_conexion_cliente`, `IDX_conexion_principal` — bueno para routing por tenant.
- **usuario:** `IDX_usuario_cliente` (cliente_id, es_activo) con filtro `WHERE es_eliminado=0`; `IDX_usuario_correo`, `IDX_usuario_dni`, `IDX_usuario_referencia_externa` (con WHERE no null). Cubren bien login y listados por tenant.
- **usuario_rol / rol:** Índices por usuario, rol y cliente; adecuados para permisos y LBAC.
- **refresh_tokens:** `IDX_refresh_token_usuario_cliente`, `IDX_refresh_token_active`, `IDX_refresh_token_cleanup`, `IDX_refresh_token_device` — buenos para validación, limpieza y sesiones por dispositivo.
- **auth_audit_log:** Índices por cliente, usuario, evento, éxito, IP — adecuados para auditoría y análisis.
- **modulo_menu:** `IDX_menu_modulo`, `IDX_menu_seccion`, `IDX_menu_cliente`, `IDX_menu_ruta` — coherentes con filtros por módulo y cliente.
- **cliente_modulo:** `IDX_cliente_modulo_cliente`, `IDX_cliente_modulo_vencimiento` (filtro WHERE) — correctos para activación y vencimientos.

Posibles mejoras:

- **cliente:** Si se hacen búsquedas por `contacto_email` o `ruc`, valorar índices (o filtros en aplicación) para no hacer full scan.
- **log_sincronizacion_usuario:** Si crece mucho, considerar partición o archivado por fecha además de `IDX_log_sync_fecha`.

### TABLAS_BD_DEDICADA.sql

- Misma estructura de índices que la central para usuario, rol, usuario_rol, rol_menu_permiso, refresh_tokens, auth_audit_log.
- **rol_menu_permiso:** Sin FK a `modulo_menu` (está en central); índices locales por rol y menú están bien para consultas dentro de la BD dedicada.

En ambas BDs no se ven índices compuestos que combinen, por ejemplo, (cliente_id, fecha_ultimo_acceso) para “usuarios recientes”; se puede añadir si ese patrón de consulta existe.

---

## 6. Manejo de errores y logging

- **Excepciones:** Jerarquía clara (`CustomException`, `ClientNotFoundException`, `DatabaseError`, `ValidationError`, `SecurityError`, etc.) y `configure_exception_handlers()` devuelve JSON con `detail` y `error_code`. En respuestas 5xx se oculta el detalle interno (“Error interno del servidor”).
- **Logging:** Uso de `logging` con niveles; mensajes útiles en tenant, auth y conexiones. No se ve un formato estructurado (JSON) ni correlación request-id; en producción dificulta agregación y búsqueda.
- **PII:** En logs aparecen `username`, `cliente_id`, `usuario_id`; no hay ofuscación ni política explícita de no registrar datos sensibles (ej. correo, IP) según entorno.
- **Auditoría de auth:** `AuditService.registrar_auth_event` y `registrar_tenant_access` para login y acceso cross-tenant de superadmin; buena base para cumplimiento.

Recomendación: Estructurar logs (JSON), añadir request_id y revisar qué PII se escribe según política de privacidad y normativa.

---

## 7. Riesgos de fuga de datos entre tenants (resumen)

| Riesgo | Severidad | Mitigación actual | Recomendación |
|--------|-----------|-------------------|---------------|
| Query sin `cliente_id` (Core) | Media | `apply_tenant_filter` + auditor en prod | Mantener; migrar más queries a Core. |
| Query TextClause/string sin `cliente_id` | Alta | Solo auditor por string; no inyección automática | No usar string/TextClause para tablas tenant sin pasar siempre `cliente_id`; revisar todos los usos. |
| Token usado en otro tenant | Baja | Validación tenant en token + `validate_tenant_access` | Corregir SSO para incluir `cliente_id` en payload. |
| Host/Origin falsificado (prod) | Baja | Solo Host en prod | Mantener; no confiar en Origin en prod. |
| Tablas globales incompletas en auditor | Baja | Lista fija GLOBAL_TABLES | Añadir `modulo`, `modulo_seccion` (y excepciones para `modulo_menu`) o documentar y desactivar auditor para esas consultas. |
| BD dedicada: menu_id sin validar contra central | Media | Ninguna en BD | Validar en aplicación al asignar permisos o al cargar menús. |
| execute_auth_query sin contexto | Media | Depende del contexto de request | En jobs/cron, pasar siempre un tenant explícito o usar conexión ADMIN con lógica explícita. |

---

## 8. Problemas potenciales en producción

- **SUPERADMIN_CLIENTE_ID vacío:** En desarrollo se usa un UUID por defecto; en producción debe estar configurado o el arranque falla (validación en middleware).
- **SECRET_KEY / REFRESH_SECRET_KEY:** Validadas al cargar config (longitud, distintas entre sí); bien.
- **cleanup_expired_tokens:** Llama a `execute_update(text(DELETE_EXPIRED_TOKENS))` sin `client_id`. En Single-DB puede ejecutarse en la BD central y limpiar todos los tenants; en Multi-DB la conexión depende del contexto, por lo que un job sin contexto fallará o no hará nada. Definir si el cleanup es por tenant (job que itera tenants con contexto) o solo para Single-DB.
- **revoke_refresh_token_by_id(token_id):** No recibe `cliente_id`; es operación “admin” y puede ejecutarse sobre cualquier BD según dónde se invoque; asegurar que solo se use en contexto controlado (ej. admin del propio tenant).
- **CORS:** Lista fija de orígenes; en producción añadir solo dominios necesarios y evitar `*` con credenciales (ya evitado).
- **Rate limiting:** slowapi en login (ej. 10/min) y API (ej. 200/min); por defecto por IP, no por tenant. Un tenant podría consumir la cuota global; valorar límites por tenant o por (tenant, IP).

---

## 9. Cumplimiento de buenas prácticas SaaS

- **Multi-tenancy:** Modelo híbrido bien definido; documentación en ORGANIZACION_TABLAS_CENTRAL_VS_DEDICADA.md.
- **Aislamiento:** Capas middleware + auth + filtro de queries + auditor; falta cerrar el hueco de TextClause/string y SSO.
- **Seguridad:** JWT con tipo, jti, REFRESH_SECRET_KEY separada, cookies HttpOnly/Secure/SameSite, validación de tenant en token.
- **Escalabilidad:** Stateless, pooling por tenant, límites y LRU en pools.
- **Observabilidad:** Logs y auditoría de auth; falta métricas (latencia por tenant, errores por tenant, uso de pools) y logs estructurados.
- **Configuración:** Variables de entorno y feature flags (ENABLE_QUERY_TENANT_VALIDATION, ALLOW_TENANT_FILTER_BYPASS, etc.); ALLOW_TENANT_FILTER_BYPASS en false por defecto es correcto.

---

## 10. Lista de riesgos críticos

1. **SSO: tokens sin `cliente_id`** — Al implementar Azure AD/Google, los tokens no llevan tenant; riesgo de uso del token en otro tenant. **Acción:** Incluir `cliente_id` (y level_info) en el payload en los flujos SSO, igual que en login por password.
2. **Queries TextClause/string sin filtro tenant automático** — No se aplica `apply_tenant_filter`; un desarrollador puede olvidar `cliente_id`. **Acción:** Revisar todos los `text(...).bindparams()` que toquen tablas por tenant; preferir SQLAlchemy Core; si se mantienen strings, checklist de revisión y tests de aislamiento.
3. **Validación de `menu_id` en BD dedicada** — `rol_menu_permiso.menu_id` apunta a central sin FK. **Acción:** Validar en aplicación que el `menu_id` exista en central y corresponda al cliente antes de insertar/actualizar permisos.
4. **cleanup_expired_tokens en Multi-DB** — Sin contexto no hay conexión tenant. **Acción:** Definir diseño: o job que itera tenants con contexto, o ejecutar cleanup solo en BD central (Single-DB).
5. **Redis como single point of failure para revocación** — Si Redis cae, la revocación no se aplica. **Acción:** Documentar y monitorear; opcionalmente, en logout revocar también en BD además de Redis para que al menos el refresh quede invalidado en BD.

---

## 11. Mejoras recomendadas (priorizadas)

### Alta prioridad

- Incluir `cliente_id` (y level_info) en tokens generados en flujos SSO (Azure AD y Google).
- Revisar todas las queries que usan `text()` o string contra tablas con `cliente_id` y asegurar que siempre reciban y usen `cliente_id`; añadir tests de aislamiento para esos endpoints.
- Validar en aplicación `menu_id` contra BD central al crear/actualizar `rol_menu_permiso` en BD dedicada.
- Definir y documentar el flujo de `cleanup_expired_tokens` para Multi-DB (por tenant con contexto o solo central).

### Media prioridad

- Añadir a QueryAuditor/query_helpers las tablas globales de catálogo (`modulo`, `modulo_seccion`) o documentar excepciones para no bloquear consultas legítimas sin `cliente_id`.
- Logging estructurado (JSON) y request_id para trazabilidad en producción.
- Métricas: latencia por tenant, errores por tenant, uso de connection pools (get_pool_stats) y alertas cuando se acerque MAX_TENANT_POOLS.
- Revisar PII en logs (emails, IPs) y alinear con política de privacidad y normativa.

### Baja prioridad

- Tipo de parámetro `client_id` en `_get_pool_for_tenant` (UUID en lugar de int) para coherencia.
- Rate limiting por tenant (o por tenant+IP) si un cliente puede afectar al resto.
- Documentar explícitamente el comportamiento “fail-soft” de Redis para revocación y criterios de monitoreo.

---

## 12. Nivel de madurez del sistema

**Evaluación: intermedio-alto.**

- **Arquitectura:** Clara separación Single/Multi-DB, contexto y routing bien definidos.
- **Seguridad:** Auth sólida para login password (tenant en token, validación, refresh en BD, rotación); huecos en SSO y en validación de queries no-Core.
- **Aislamiento:** Múltiples capas; el eslabón débil son las queries no-Core y la validación de `menu_id` en dedicada.
- **Escalabilidad:** Stateless y pooling con límites; falta observabilidad y posible ajuste de límites según carga.
- **Operación:** Buen manejo de excepciones y configuración; logging y limpieza de tokens en Multi-DB mejorables.

---

## 13. ¿Listo para fase de módulos ERP?

**Sí, con condiciones.**

- La base multi-tenant, auth, permisos y catálogo de módulos (modulo, modulo_seccion, modulo_menu, cliente_modulo) están listos para que los módulos ERP se integren por tenant y por cliente.
- Antes de considerar la fase ERP “cerrada” para producción:

  - Corregir los flujos SSO para que los tokens incluyan `cliente_id`.
  - Revisar y asegurar todas las queries que toquen datos por tenant (especialmente TextClause/string).
  - Resolver el diseño de `cleanup_expired_tokens` en Multi-DB y la validación de `menu_id` en BD dedicada.

Con esas condiciones cubiertas, el sistema está en condiciones de avanzar a fase de módulos ERP con un nivel de riesgo controlado y un buen estándar SaaS.
