# AUDITORÍA FINAL BACKEND — MULTI-COMPANY ARCHITECTURE REFACTORING (V2)

**Fecha de auditoría:** 2026-05-18  
**Alcance:** Solo lectura del código y seeds en repo. Sin modificaciones.  
**Referencias principales:** `app/core/security/jwt.py`, `app/modules/auth/application/services/auth_service.py`, `app/modules/auth/presentation/endpoints.py`, `app/modules/tenant/application/services/cliente_onboarding_service.py`, seeds SQL en `app/docs/database/`.

---

## PUNTO 1 — JWT y proceso de login multi-empresa

### 1.1 Payload del access token

Fuente: `create_access_token()` en `app/core/security/jwt.py`. El payload se arma desde `data` (claims base) + campos fijos + `_apply_empresa_claims()`.

**Claims siempre presentes en access token emitido por `create_access_token`:**

| Campo | ¿Presente? | Tipo/Valor |
|---|---|---|
| `sub` | ✅ | `str` — nombre de usuario (desde `data`, obligatorio en login) |
| `cliente_id` | ✅ | `str` — UUID del tenant serializado (`str(target_cliente_id)` en login) |
| `empresa_id` | ⚠️ Condicional | `str` (UUID) — solo si hay empresa activa; **omitido del JWT** si `empresa_id` es `None` (`_apply_empresa_claims` no añade la clave) |
| `es_admin_cliente` | ✅ | `bool` — default `False` si no se pasa explícito |
| `access_level` | ✅ | `int` — de `level_info` (1–5), default `1` |
| `is_super_admin` | ✅ | `bool` — de `level_info`, default `False` |
| `user_type` | ✅ | `str` — de `level_info`, default `'user'` |
| `es_superadmin` | ⚠️ Condicional | `bool` — solo si login/SSO añade `es_superadmin: True` en `data` (superadmin cross-tenant) |
| `type` | ✅ | `str` — siempre `'access'` |
| `jti` | ✅ | `str` — UUID v4 por emisión |
| `exp` / `iat` | ✅ | `datetime` en código → serializado por `python-jose` como timestamps Unix en el JWT |
| `empresa_selection_pending` | ⚠️ Condicional | `bool` — solo en **selection token**; viene en `data` del login multi-empresa y **no se elimina** en `create_access_token` |

**Notas:**

- `level_info` se usa al construir el token y se **elimina** del payload final (`to_encode.pop('level_info', None)`).
- Refresh token (`create_refresh_token`) incluye los mismos claims de nivel/empresa, con `type: 'refresh'`.
- Selection token: `empresa_id` ausente + `empresa_selection_pending: true` (ver `endpoints.py` login ~L287–294).

---

### 1.2 Resolución de empresa en login

**Función:** `AuthService.get_empresa_activa_para_login(usuario_id, cliente_id)` — ✅ existe (`auth_service.py` ~L117–238).

| Verificación | Estado |
|---|---|
| Consulta empresas disponibles (`DISTINCT usuario_rol.empresa_id`, activos, no NULL) | ✅ |
| Consulta `empresa_default_id` en `usuario` | ✅ (query adaptada `database_type` single/multi) |
| Devuelve `empresas_disponibles` | ✅ `List[UUID]` |
| Devuelve `empresa_activa` | ✅ `Optional[UUID]` |
| Devuelve `es_admin_sin_empresa` | ✅ (count roles con `empresa_id IS NULL`) |
| Devuelve `requiere_seleccion` | ✅ `len(empresas) > 1 and empresa_default_id is None` |

**Manejo en `POST /auth/login/` (`endpoints.py`):**

| Caso | Comportamiento | Estado |
|---|---|---|
| `requiere_seleccion=True` | `LoginEmpresaSelectionResponse` + `selection_token` (sin refresh) | ✅ |
| `empresa_activa` definida (1 empresa o default válido) | `Token` completo con `empresa_id` en JWT | ✅ |
| `es_admin_sin_empresa` y sin empresas | `Token` sin `empresa_id` (onboarding admin tenant) | ✅ (~L308–312) |

**Flujo post-login multi-empresa (complemento reciente):**

| Endpoint | Estado |
|---|---|
| `POST /api/v1/auth/empresa/seleccionar/` | ✅ Implementado |
| `POST /api/v1/auth/empresa/cambiar/` | ✅ Implementado |
| Blacklist `jti` del selection token tras seleccionar | ✅ `AuthService.blacklist_access_token_jti` |

---

### 1.3 Filtro de roles y permisos por `empresa_id`

Patrón esperado: `AND (ur.empresa_id IS NULL OR ur.empresa_id = :empresa_id)` vía `sql_empresa_filter_usuario_rol()` en `empresa_context.py`.

| Función | ¿Tiene filtro empresa_id? | Detalle |
|---|---|---|
| `UsuarioService.get_user_role_names` | ✅ Condicional | Aplica `sql_empresa_filter_usuario_rol("ur")` solo si `resolve_empresa_id(empresa_id)` no es `None` |
| `GET_USER_ACCESS_LEVEL_INFO_COMPLETE` (constante SQL) | ✅ En texto | `auth_queries.py` L62 incluye el filtro con `:empresa_id` |
| `AuthService.get_user_access_level_info` (runtime) | ✅ Condicional | Misma lógica dinámica que la constante; **sin filtro si no hay empresa** |
| `build_user_with_roles` | ✅ Condicional | Filtro SQLAlchemy `or_(empresa_id IS NULL, empresa_id == ctx)` solo si `try_get_current_empresa_id()` tiene valor |
| `obtener_codigos_permiso_usuario` | ✅ Condicional | `_permisos_single` / `_permisos_dedicated` usan `sql_empresa_filter_usuario_rol` si hay `empresa_id` |

**Riesgo conocido (documentado en auditorías previas):** con `empresa_id` **null** en JWT/contexto, roles/permisos/nivel se calculan **agregando todas las empresas** del usuario (sin filtro). Estado: 🟡 comportamiento intencional para admin sin empresa; 🟡 riesgo si un usuario multi-empresa operara sin seleccionar.

---

### 1.4 Refresh token con `empresa_id`

| Verificación | Estado | Evidencia |
|---|---|---|
| `insert_refresh_token_core` incluye `empresa_id` en INSERT | ✅ | `refresh_token_queries_core.py` L96, L144–158 |
| `get_refresh_token_by_hash_core` devuelve `empresa_id` | ✅ | SELECT incluye `RefreshTokensTable.c.empresa_id` L69 |
| Endpoint refresh lee `empresa_id` de BD y lo usa en nuevo token | ✅ | `get_current_user_from_refresh`: BD prioritaria sobre JWT (`auth_service.py` ~L1055–1058); `endpoints.py` refresh ~L841–880 |
| Nuevo refresh persiste `empresa_id` en rotación | ✅ | `store_refresh_token(..., empresa_id=refresh_empresa_id, is_rotation=True)` |
| JWT refresh incluye claim `empresa_id` | ✅ | `create_refresh_token(..., empresa_id=...)` |

**Legacy:** constantes `INSERT_REFRESH_TOKEN` / `GET_REFRESH_TOKEN_BY_HASH` en `auth_queries.py` **no** incluyen `empresa_id`; el flujo activo usa **Core** (`refresh_token_queries_core.py`). 🟡

---

### 1.5 Expiración desde `cliente_auth_config`

| Verificación | Estado |
|---|---|
| Consulta `cliente_auth_config` por `cliente_id` | ✅ `leer_expiracion_tokens_cliente()` |
| Usa `access_token_minutes` del tenant si existe | ✅ |
| Fallback a `settings.ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ |
| Mismo patrón `refresh_token_days` | ✅ |
| Usado en login, refresh, seleccionar/cambiar empresa | ✅ vía `AuthService.get_token_expiration_for_cliente()` |

---

### 1.6 `es_admin_cliente`

| Verificación | Estado |
|---|---|
| `usuario_tiene_es_admin_cliente` existe | ✅ |
| Consulta `rol.es_admin_cliente = 1` | ✅ |
| Filtro `(ur.empresa_id IS NULL OR ur.empresa_id = :empresa_id)` cuando hay empresa | ✅ |
| Se llama en flujo login password | ✅ |
| Se incluye en JWT access/refresh | ✅ `_apply_empresa_claims` |
| Se recalcula en seleccionar/cambiar empresa | ✅ `emitir_sesion_completa_con_empresa` |

---

### 1.7 Schemas del response de login

| Campo / schema | Estado |
|---|---|
| `user_data.es_admin_cliente` | ✅ `UserDataWithRoles` + asignación en login |
| `user_data.empresa_activa` | ✅ string UUID o `null` |
| `LoginEmpresaSelectionResponse` | ✅ |
| → `requiere_seleccion_empresa` | ✅ default `True` |
| → `empresas_disponibles` | ✅ `List[UUID]` |
| → `selection_token` | ✅ |
| `GET /auth/me/` con `empresa_activa`, `es_admin_cliente`, `requiere_seleccion_empresa` | ✅ |
| `EmpresaIdRequest` para seleccionar/cambiar | ✅ |

**Gap SSO (Azure/Google):** flujo SSO **no** llama `get_empresa_activa_para_login`, **no** emite `LoginEmpresaSelectionResponse`, **no** pasa `empresa_id`/`es_admin_cliente` a `create_access_token`, **no** persiste `empresa_id` en `store_refresh_token`, **no** enriquece `user_data` con `empresa_activa` / `es_admin_cliente`. 🟡 incompleto respecto a login password.

---

## PUNTO 2 — Onboarding automático de cliente nuevo

Fuente: `cliente_onboarding_service.py`, `CfgCodigoSecuenciaRepository`, `ClienteCreateResponse`.

### 2.1 Transacción

| Verificación | Estado |
|---|---|
| `async with get_db_connection(ADMIN)` + `async with session.begin()` | ✅ L120–121 |
| Rollback si falla cualquier paso | ✅ transacción SQLAlchemy |

### 2.2 Paso 1 — Roles base (3 roles)

| codigo_rol | nivel_acceso | es_admin_cliente | empresa_id (INSERT) |
|---|---|---|---|
| ADMIN_TENANT | 5 | True | NULL ✅ |
| MANAGER_TENANT | 3 | False | NULL ✅ |
| USER_TENANT | 1 | False | NULL ✅ |

Definidos en `ROLES_BASE` y insertados en `_insertar_roles_base`.

### 2.3 Paso 2 — Usuario admin

| Campo | Estado |
|---|---|
| `nombre_usuario = 'admin'` | ✅ `ADMIN_USERNAME` |
| Contraseña bcrypt | ✅ `get_password_hash` |
| Contraseña aleatoria 12+ chars | ✅ `_generar_contrasena_segura(12)` |
| `requiere_cambio_contrasena = True` | ✅ INSERT valor `1` |
| `empresa_default_id = NULL` | ✅ |
| `correo = contacto_email` del cliente | ✅ `cliente_data.contacto_email` |

### 2.4 Paso 3 — `usuario_rol`

| Campo | Estado |
|---|---|
| `rol_id` = ADMIN_TENANT creado | ✅ `admin_rol_id` |
| `empresa_id = NULL` | ✅ |
| `es_empresa_default = False` | ✅ (fallback INSERT sin columna si BD no la tiene) |
| `es_activo = True` | ✅ |

### 2.5 Paso 4 — `cliente_auth_config`

| Verificación | Estado |
|---|---|
| Solo inserta si no existe | ✅ `IF NOT EXISTS ... INSERT` |
| Usa defaults de tabla | ✅ `INSERT (cliente_id) VALUES (:cliente_id)` |

### 2.6 Paso 5 — `cfg_codigo_secuencia` (9 entidades)

| Entidad | Prefijo | Longitud | empresa_id | ultimo_numero |
|---|---|---|---|---|
| org_empresa | EMP | 3 | NULL ✅ | 0 ✅ |
| org_sucursal | SUC | 3 | NULL ✅ | 0 ✅ |
| org_departamento | DEP | 3 | NULL ✅ | 0 ✅ |
| org_cargo | CAR | 3 | NULL ✅ | 0 ✅ |
| org_centro_costo | CC | 3 | NULL ✅ | 0 ✅ |
| inv_almacen | ALM | 3 | NULL ✅ | 0 ✅ |
| inv_producto | P | 5 | NULL ✅ | 0 ✅ |
| inv_categoria | CAT | 3 | NULL ✅ | 0 ✅ |
| inv_movimiento | MOV | 6 | NULL ✅ | 0 ✅ |

| Idempotencia insert | ✅ `insert_secuencia` → `get_by_entidad` antes de insertar |

### 2.7 Repositorio `CfgCodigoSecuenciaRepository`

| Método | Estado |
|---|---|
| `get_by_cliente` | ✅ (audit pedía `get_by_cliente`; implementado como `get_by_cliente`) |
| `get_by_entidad` | ✅ |
| `insert_secuencia` | ✅ |
| `update_ultimo_numero` | ✅ |
| `update_secuencia` | ✅ |
| `CfgCodigoSecuenciaTable` en `tables.py` | ✅ L511 |

### 2.8 Response `POST /api/v1/clientes/`

| Campo | Estado |
|---|---|
| `data` con campos del cliente (`ClienteRead`) | ✅ `ClienteCreateResponse.data` |
| `credenciales_iniciales.nombre_usuario` | ✅ |
| `credenciales_iniciales.contrasena` (plano, una vez) | ✅ |
| `credenciales_iniciales.requiere_cambio` | ✅ |
| Mensaje de advertencia | ✅ `MENSAJE_CREACION_EXITOSA` en `message` |

**Dependencia BD:** si `usuario.empresa_default_id` es NOT NULL sin default, el onboarding documenta error explícito (`USER_ONBOARDING_EMPRESA_DEFAULT`). 🟡 requiere DDL alineado en entornos nuevos.

---

## PUNTO 3 — Separación de rutas (impacto en backend)

### 3.1 `GET /auth/menu` y rutas en BD

El endpoint delega en `MenuResolverService` → `ModuloMenuService.obtener_menu_usuario`; las rutas vienen de `modulo_menu.ruta` en BD (seeds SQL).

**Seeds revisados:** `app/docs/database/4.- SEED_MODULO_MENU_COMPLETO.sql` (y variantes `SEED_MODULO_MENU.SQL`).

| Módulo | Ejemplo ruta en BD | ¿Actualizada a `/app/*`? |
|---|---|---|
| ORG | `/org/empresa`, `/org/sucursales`, … | ❌ Sin prefijo `/app` |
| INV | `/inv/productos`, `/inv/categorias`, … | ❌ Sin prefijo `/app` |
| Resto ERP (LOG, MFG, MRP, …) | `/log/...`, `/mfg/...`, `/mrp/...` | ❌ Sin prefijo `/app` |

**Menú SYS_ADMIN** (`6.- SEED_ADMIN_MENU.sql`): rutas tipo `/admin/usuarios`, `/admin/roles` — tampoco usan `/app/*`.

> **Pendiente crítico (datos/FE, no código Python del resolver):** si el frontend ERP migra a rutas `/app/inv/*`, `/app/org/*`, etc., los seeds y las filas ya desplegadas en `modulo_menu` deben actualizarse o el sidebar dinámico navegará a rutas incorrectas. El backend **expone** lo que hay en BD; no reescribe rutas.

### 3.2 `GET /auth/menu` — `empresa_id`

| Pregunta | Respuesta |
|---|---|
| ¿Filtra módulos por `empresa_id` del JWT? | ❌ No hay filtro por empresa en `MenuResolverService` |
| ¿Qué filtra? | Tenant (`cliente_id`), módulos contratados (`cliente_modulo`), permisos efectivos (Permission Resolver con `empresa_id` vía contexto), `rol_menu_permiso` |

Los permisos del menú **sí** pueden variar por empresa si el JWT estableció `empresa_id` en `empresa_context` (deps → Permission Resolver). Los **ítems y rutas** del menú no están particionados por empresa en BD.

---

## PUNTO 4 — Sidebar y contextos (impacto en backend)

### 4.1 Estructura de `GET /auth/menu`

Response: `MenuUsuarioResponse` → `modulos: List[ModuloMenuResponse]` con `codigo`, `nombre`, `categoria`, `secciones[]` → ítems con `ruta`, `codigo`, etc.

| Verificación | Estado |
|---|---|
| Campo explícito “contexto del sidebar” (p. ej. `sidebar_context`) | ❌ No existe |
| Diferencia SYS_ADMIN vs ERP | ⚠️ Implícita por `modulo.codigo` (`SYS_ADMIN`, `ORG`, `INV`, …) y secciones `TENANT_ADMIN` / `SUPER_ADMIN` en seeds admin |
| Separación TENANT_ADMIN vs SUPER_ADMIN en response | ⚠️ Por **módulo/sección** en árbol (`modulo_menu` + `modulo_seccion`), no por flag dedicado en JSON |

El endpoint acepta `as_tenant_admin` en resolver (desde lógica del caller en `get_menu`); la separación de 3 sidebars en FE debe inferirse de `codigo` de módulo + `access_level` / `user_type` del JWT, no de un contrato único de “contexto”.

**Protección selection token:** `GET /auth/menu` usa `get_current_active_user_full_session` → **409** si `empresa_selection_pending`. ✅

---

## PUNTO 5 — Impersonación

| Verificación | Estado |
|---|---|
| `POST /auth/impersonate` | ❌ No existe (correcto — diferido) |
| Endpoints “login as” / impersonación | ❌ No encontrados (`grep` sin matches) |
| Estado “diferir” | ✅ Cerrado como pendiente futuro |

---

## PASO FINAL — Diagnóstico consolidado

### Tabla de estado por área

| Área | Estado | Pendiente |
|---|---|---|
| `empresa_id` en JWT | 🟢 | Omitido solo cuando sesión sin empresa (admin onboarding) |
| `es_admin_cliente` en JWT | 🟢 | — |
| `user_data` con `empresa_activa` | 🟢 | Login password + seleccionar/cambiar + `/me`; SSO sin campos |
| `LoginEmpresaSelectionResponse` | 🟢 | Solo login password |
| Resolución empresa en login | 🟢 | SSO sin multi-empresa |
| Filtro roles por `empresa_id` | 🟡 | Correcto **con** empresa en contexto; agregado **sin** empresa |
| Refresh con `empresa_id` | 🟢 | Queries legacy en `auth_queries.py` obsoletas |
| Expiración por tenant | 🟢 | — |
| Onboarding transaccional | 🟢 | Validar DDL `empresa_default_id` nullable |
| Roles base ADMIN/MANAGER/USER | 🟢 | — |
| Usuario admin con credenciales | 🟢 | — |
| `cfg_codigo_secuencia` 9 seeds | 🟢 | — |
| Repositorio `CfgCodigoSecuencia` | 🟢 | — |
| Rutas `/app/*` en BD `modulo_menu` | 🔴 | Actualizar seeds + migración datos en BD desplegadas |
| `/auth/menu` diferencia contextos | 🟡 | Por `modulo.codigo`, sin campo `contexto` |
| Seleccionar / cambiar empresa API | 🟢 | Implementado en esta iteración |
| Endurecer menú/permisos con selection token | 🟢 | 409 en `/permissions/me` y `/menu` |
| Impersonación diferida | 🟢 | Sin implementar (esperado) |
| SSO alineado multi-empresa | 🟡 | Sin `empresa_id`, sin selección, sin `user_data` empresa |

---

### Preguntas de cierre

#### 1. ¿Qué está implementado correctamente y no necesita ningún cambio?

- JWT access/refresh con `empresa_id`, `es_admin_cliente`, niveles LBAC, `jti`, revocación Redis.
- Login password: resolución multi-empresa, `LoginEmpresaSelectionResponse`, tokens completos, refresh con `empresa_id` en BD.
- Endpoints `POST /auth/empresa/seleccionar/` y `POST /auth/empresa/cambiar/` con auditoría `empresa_seleccionada` / `empresa_cambiada`.
- `/me` ampliado; bloqueo 409 de menú/permisos con selection token.
- Expiración por `cliente_auth_config`.
- Filtros de roles/permisos por empresa cuando hay `empresa_id` en contexto.
- Onboarding transaccional completo (roles, admin, auth_config, secuencias, credenciales en response).
- Repositorio y tabla `cfg_codigo_secuencia`.
- Impersonación correctamente **no** implementada (diferida).

#### 2. ¿Qué está implementado pero incompleto o con detalle a corregir?

- **Filtro sin `empresa_id`:** permisos/roles agregados cross-empresa si el token no lleva empresa (riesgo si se usa sesión incompleta).
- **SSO Azure/Google:** no replica login multi-empresa ni claims `empresa_*` en JWT/`user_data`/refresh BD.
- **Rutas en `modulo_menu`:** seeds siguen en `/org/*`, `/inv/*`, `/admin/*` — no `/app/*`.
- **`/auth/menu`:** no filtra ítems por empresa; contexto de sidebar no es un campo explícito del contrato.
- **Queries SQL legacy** de refresh en `auth_queries.py` sin `empresa_id` (no usadas por el path Core activo).
- **Onboarding:** requiere `empresa_default_id` nullable en DDL para no fallar en BDs estrictas.

#### 3. ¿Qué falta implementar completamente para el backend listo para FE multi-empresa?

| Prioridad | Item |
|---|---|
| 🔴 Alta | Migración SQL/seed de `modulo_menu.ruta` a prefijo `/app/...` (y datos en producción) si el router FE ya usa `/app/*`. |
| 🟡 Media | Alinear flujos **SSO** con login password (empresa, selección, refresh `empresa_id`, `user_data`). |
| 🟡 Media | Opcional: campo de contrato en menú (`contexto` / `sidebar_type`) para 3 sidebars sin heurísticas frágiles. |
| 🟢 Baja | Limpiar constantes legacy refresh en `auth_queries.py` para evitar confusión. |
| 🟢 Futuro | Impersonación (diferida). |

#### 4. ¿El backend ya puede soportar estos flujos del frontend?

| Flujo FE | ¿Soportado? | Notas |
|---|---|---|
| Login usuario **una empresa** → JWT con `empresa_id` | ✅ | Login password |
| Login **varias empresas** → selección | ✅ | `LoginEmpresaSelectionResponse` + `POST .../empresa/seleccionar/` |
| Login **admin cliente sin empresa** → onboarding | ✅ | Token sin `empresa_id`; roles globales `empresa_id NULL` |
| Login **super admin CAXIS** → panel plataforma | ✅ | `es_superadmin` / `is_super_admin`; menú SYS_ADMIN por permisos/módulos |
| **Refresh** mantiene `empresa_id` | ✅ | BD `refresh_tokens.empresa_id` + rotación |
| **Cambio de empresa** en sesión (header ERP) | ✅ | `POST .../empresa/cambiar/` |
| Sidebar con rutas `/app/*` desde BD | ❌ | Rutas en seeds aún sin `/app` |
| SSO multi-empresa | ❌ | Mismo gap que arriba |

---

## Resumen ejecutivo

El **núcleo multi-empresa en auth (Punto 1)** y el **onboarding de tenant (Punto 2)** están en estado **verde** para login password, refresh, selección/cambio de empresa y contrato FE de tokens. Los puntos **3 y 4** dependen sobre todo de **datos de menú en BD** y de un contrato de menú aún **implícito** por código de módulo, no de lógica ausente en el resolver. El **Punto 5** está correctamente diferido. El bloqueador principal para integración FE de rutas ERP es la **actualización de `modulo_menu.ruta` a `/app/*`**, no la ausencia del endpoint `/auth/menu`.

---

*Documento generado por auditoría estática del repositorio. No sustituye pruebas E2E contra BD real ni validación de datos ya migrados en cada entorno.*
