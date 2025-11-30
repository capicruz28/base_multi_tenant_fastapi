# Propuesta de Arquitectura: DDD Ligera + Modular Monolith

## 📋 Análisis del Proyecto Actual

### Estructura Actual Identificada

```
app/
├── main.py                          # Punto de entrada FastAPI
├── core/                            # Configuración y utilidades centrales
│   ├── config.py                    # Settings y configuración
│   ├── auth.py                      # Autenticación JWT
│   ├── authorization.py             # Sistema de autorización
│   ├── tenant_context.py            # ContextVars para multi-tenant
│   ├── multi_db.py                  # Routing de conexiones híbridas
│   ├── security.py                  # Hashing de passwords
│   ├── encryption.py                # Encriptación de credenciales
│   ├── connection_cache.py          # Cache de metadata de conexiones
│   ├── exceptions.py                # Excepciones personalizadas
│   ├── logging_config.py            # Configuración de logging
│   └── level_authorization.py       # Sistema LBAC
├── api/                             # Capa de presentación (HTTP)
│   ├── deps.py                      # Dependencias FastAPI
│   └── v1/
│       ├── api.py                   # Router principal
│       └── endpoints/               # Endpoints por dominio
│           ├── auth.py
│           ├── usuarios.py
│           ├── roles.py
│           ├── permisos.py
│           ├── menus.py
│           ├── areas.py
│           ├── clientes.py
│           ├── modulos.py
│           ├── conexiones.py
│           ├── auth_config.py
│           ├── superadmin_usuarios.py
│           └── superadmin_auditoria.py
├── services/                        # Lógica de negocio
│   ├── base_service.py
│   ├── usuario_service.py
│   ├── rol_service.py
│   ├── permiso_service.py
│   ├── menu_service.py
│   ├── area_service.py
│   ├── cliente_service.py
│   ├── modulo_service.py
│   ├── conexion_service.py
│   ├── auth_config_service.py
│   ├── refresh_token_service.py
│   ├── audit_service.py
│   ├── tenant_service.py
│   └── superadmin_*_service.py
├── db/                              # Acceso a datos
│   ├── connection.py                # Gestión de conexiones
│   └── queries.py                   # Queries SQL
├── models/                          # Modelos de dominio (pocos)
│   ├── usuario.py
│   ├── menu.py
│   └── autorizacion.py
├── schemas/                         # DTOs Pydantic
│   ├── usuario.py
│   ├── rol.py
│   ├── menu.py
│   └── ...
├── middleware/                      # Middleware HTTP
│   └── tenant_middleware.py
└── utils/                           # Utilidades
    └── menu_helper.py
```

### Dominios Identificados

1. **Autenticación y Autorización** (auth)
   - Login, tokens, refresh tokens
   - SSO (Azure AD, Google)
   - Configuración de autenticación

2. **Gestión de Usuarios** (users)
   - CRUD usuarios
   - Asignación de roles
   - Perfiles

3. **Gestión de Roles y Permisos** (rbac)
   - Roles, permisos, asignaciones
   - Sistema LBAC (Level-Based Access Control)

4. **Gestión de Menús** (menus)
   - Menús, áreas, navegación
   - Permisos de menú

5. **Multi-Tenant** (tenant)
   - Clientes, conexiones
   - Routing híbrido (Single-DB / Multi-DB)
   - Contexto de tenant

6. **Super Admin** (superadmin)
   - Gestión global de clientes
   - Auditoría
   - Usuarios globales

7. **Módulos y Configuración** (modules)
   - Módulos activos por cliente
   - Configuración de módulos

---

## 🏗️ Estructura Propuesta: DDD Ligera + Modular Monolith

### Principios de Diseño

1. **Domain-Driven Design (DDD) Ligera**
   - Dominios claramente separados
   - Agregados y entidades por dominio
   - Servicios de dominio

2. **Modular Monolith**
   - Módulos independientes por dominio
   - Interfaces claras entre módulos
   - Preparado para extracción futura a microservicios

3. **Separación de Capas**
   - **Domain**: Entidades, value objects, reglas de negocio
   - **Application**: Casos de uso, servicios de aplicación
   - **Infrastructure**: BD, cache, external services
   - **Presentation**: API REST, DTOs

4. **Core/Shared**
   - Utilidades compartidas
   - Configuración global
   - Middleware común

---

## 📁 Estructura Final Propuesta

```
app/
├── main.py                          # Punto de entrada FastAPI
│
├── core/                            # ⚙️ CORE: Infraestructura compartida
│   ├── __init__.py
│   ├── config.py                    # Settings globales
│   ├── exceptions.py                # Excepciones base
│   ├── logging_config.py            # Logging
│   │
│   ├── security/                    # 🔐 Seguridad
│   │   ├── __init__.py
│   │   ├── password.py              # Hashing (security.py → aquí)
│   │   ├── encryption.py            # Encriptación de credenciales
│   │   └── jwt.py                   # JWT utilities (de auth.py)
│   │
│   ├── tenant/                      # 🏢 Multi-Tenant Core
│   │   ├── __init__.py
│   │   ├── context.py                # ContextVars (tenant_context.py)
│   │   ├── routing.py                # Routing híbrido (multi_db.py)
│   │   ├── cache.py                 # Cache de conexiones (connection_cache.py)
│   │   └── middleware.py            # TenantMiddleware
│   │
│   └── authorization/               # 🔒 Autorización
│       ├── __init__.py
│       ├── rbac.py                  # RBAC base (authorization.py)
│       └── lbac.py                   # Level-Based Access Control
│
├── infrastructure/                  # 🏗️ INFRAESTRUCTURA
│   ├── __init__.py
│   │
│   ├── database/                    # Base de datos
│   │   ├── __init__.py
│   │   ├── connection.py            # Gestión de conexiones (db/connection.py)
│   │   ├── queries.py                # Queries SQL (db/queries.py)
│   │   └── repositories/            # Repositorios base
│   │       ├── __init__.py
│   │       └── base_repository.py
│   │
│   └── cache/                       # Cache (si se expande)
│       └── __init__.py
│
├── modules/                          # 📦 MÓDULOS POR DOMINIO
│   │
│   ├── auth/                        # 🔐 MÓDULO: Autenticación
│   │   ├── __init__.py
│   │   │
│   │   ├── domain/                  # Dominio
│   │   │   ├── __init__.py
│   │   │   ├── entities.py          # Entidades (User, Token, etc.)
│   │   │   ├── value_objects.py      # Value Objects
│   │   │   └── repositories.py      # Interfaces de repositorios
│   │   │
│   │   ├── application/             # Aplicación
│   │   │   ├── __init__.py
│   │   │   ├── services/            # Servicios de aplicación
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── token_service.py
│   │   │   │   └── refresh_token_service.py
│   │   │   └── use_cases/           # Casos de uso
│   │   │       ├── __init__.py
│   │   │       ├── login.py
│   │   │       ├── refresh_token.py
│   │   │       └── logout.py
│   │   │
│   │   ├── infrastructure/          # Infraestructura del módulo
│   │   │   ├── __init__.py
│   │   │   └── repositories/        # Implementaciones de repositorios
│   │   │       ├── __init__.py
│   │   │       └── auth_repository.py
│   │   │
│   │   └── presentation/            # Presentación
│   │       ├── __init__.py
│   │       ├── schemas.py           # DTOs (de schemas/auth.py)
│   │       ├── dependencies.py      # Dependencias FastAPI
│   │       └── endpoints.py         # Endpoints (de api/v1/endpoints/auth.py)
│   │
│   ├── users/                       # 👥 MÓDULO: Usuarios
│   │   ├── __init__.py
│   │   │
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py           # Usuario entity
│   │   │   ├── value_objects.py      # Email, Username, etc.
│   │   │   └── repositories.py        # IUsuarioRepository
│   │   │
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_service.py   # (de services/usuario_service.py)
│   │   │   └── use_cases/
│   │   │       ├── __init__.py
│   │   │       ├── create_user.py
│   │   │       ├── update_user.py
│   │   │       ├── delete_user.py
│   │   │       └── list_users.py
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       └── user_repository.py
│   │   │
│   │   └── presentation/
│   │       ├── __init__.py
│   │       ├── schemas.py            # (de schemas/usuario.py)
│   │       ├── dependencies.py
│   │       └── endpoints.py          # (de api/v1/endpoints/usuarios.py)
│   │
│   ├── rbac/                        # 🛡️ MÓDULO: Roles y Permisos
│   │   ├── __init__.py
│   │   │
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py           # Rol, Permiso entities
│   │   │   ├── value_objects.py
│   │   │   └── repositories.py
│   │   │
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── rol_service.py     # (de services/rol_service.py)
│   │   │   │   └── permiso_service.py # (de services/permiso_service.py)
│   │   │   └── use_cases/
│   │   │       ├── __init__.py
│   │   │       ├── assign_role.py
│   │   │       └── check_permission.py
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── rol_repository.py
│   │   │       └── permiso_repository.py
│   │   │
│   │   └── presentation/
│   │       ├── __init__.py
│   │       ├── schemas.py            # (de schemas/rol.py, rol_menu_permiso.py)
│   │       ├── dependencies.py      # RoleChecker, etc.
│   │       └── endpoints.py          # (de api/v1/endpoints/roles.py, permisos.py)
│   │
│   ├── menus/                       # 📋 MÓDULO: Menús
│   │   ├── __init__.py
│   │   │
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py           # Menu, Area entities
│   │   │   ├── value_objects.py
│   │   │   └── repositories.py
│   │   │
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── menu_service.py    # (de services/menu_service.py)
│   │   │   │   └── area_service.py   # (de services/area_service.py)
│   │   │   └── use_cases/
│   │   │       ├── __init__.py
│   │   │       └── get_user_menu.py
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── menu_repository.py
│   │   │       └── area_repository.py
│   │   │
│   │   └── presentation/
│   │       ├── __init__.py
│   │       ├── schemas.py            # (de schemas/menu.py, area.py)
│   │       ├── dependencies.py
│   │       └── endpoints.py          # (de api/v1/endpoints/menus.py, areas.py)
│   │
│   ├── tenant/                       # 🏢 MÓDULO: Multi-Tenant
│   │   ├── __init__.py
│   │   │
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py           # Cliente, Conexion entities
│   │   │   ├── value_objects.py      # DatabaseType, etc.
│   │   │   └── repositories.py
│   │   │
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cliente_service.py    # (de services/cliente_service.py)
│   │   │   │   ├── conexion_service.py    # (de services/conexion_service.py)
│   │   │   │   └── tenant_service.py      # (de services/tenant_service.py)
│   │   │   └── use_cases/
│   │   │       ├── __init__.py
│   │   │       ├── resolve_tenant.py
│   │   │       └── get_connection.py
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── cliente_repository.py
│   │   │       └── conexion_repository.py
│   │   │
│   │   └── presentation/
│   │       ├── __init__.py
│   │       ├── schemas.py            # (de schemas/cliente.py, conexion.py)
│   │       ├── dependencies.py
│   │       └── endpoints.py          # (de api/v1/endpoints/clientes.py, conexiones.py)
│   │
│   ├── superadmin/                  # 👑 MÓDULO: Super Admin
│   │   ├── __init__.py
│   │   │
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py
│   │   │   └── repositories.py
│   │   │
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── superadmin_usuario_service.py
│   │   │   │   └── superadmin_auditoria_service.py
│   │   │   └── use_cases/
│   │   │       ├── __init__.py
│   │   │       └── audit_log.py
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       └── audit_repository.py
│   │   │
│   │   └── presentation/
│   │       ├── __init__.py
│   │       ├── schemas.py            # (de schemas/superadmin_*.py)
│   │       ├── dependencies.py
│   │       └── endpoints.py          # (de api/v1/endpoints/superadmin_*.py)
│   │
│   └── modules/                     # 📦 MÓDULO: Gestión de Módulos
│       ├── __init__.py
│       │
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities.py           # Modulo, ModuloActivo entities
│       │   └── repositories.py
│       │
│       ├── application/
│       │   ├── __init__.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── modulo_service.py
│       │   │   └── modulo_activo_service.py
│       │   └── use_cases/
│       │       ├── __init__.py
│       │       └── activate_module.py
│       │
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   └── repositories/
│       │       ├── __init__.py
│       │       └── modulo_repository.py
│       │
│       └── presentation/
│           ├── __init__.py
│           ├── schemas.py            # (de schemas/modulo.py, modulo_activo.py)
│           ├── dependencies.py
│           └── endpoints.py         # (de api/v1/endpoints/modulos.py)
│
└── api/                             # 🌐 API: Router principal y configuración
    ├── __init__.py
    ├── dependencies.py               # Dependencias globales (de api/deps.py)
    └── v1/
        ├── __init__.py
        └── router.py                 # Router principal (de api/v1/api.py)
```

---

## 📋 Mapeo de Archivos Actuales → Nueva Estructura

### Core

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/core/config.py` | `app/core/config.py` |
| `app/core/exceptions.py` | `app/core/exceptions.py` |
| `app/core/logging_config.py` | `app/core/logging_config.py` |
| `app/core/security.py` | `app/core/security/password.py` |
| `app/core/encryption.py` | `app/core/security/encryption.py` |
| `app/core/auth.py` (JWT utils) | `app/core/security/jwt.py` |
| `app/core/tenant_context.py` | `app/core/tenant/context.py` |
| `app/core/multi_db.py` | `app/core/tenant/routing.py` |
| `app/core/connection_cache.py` | `app/core/tenant/cache.py` |
| `app/middleware/tenant_middleware.py` | `app/core/tenant/middleware.py` |
| `app/core/authorization.py` | `app/core/authorization/rbac.py` |
| `app/core/level_authorization.py` | `app/core/authorization/lbac.py` |

### Infrastructure

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/db/connection.py` | `app/infrastructure/database/connection.py` |
| `app/db/queries.py` | `app/infrastructure/database/queries.py` |

### Modules

#### Auth Module

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/refresh_token_service.py` | `app/modules/auth/application/services/refresh_token_service.py` |
| `app/services/auth_config_service.py` | `app/modules/auth/application/services/auth_config_service.py` |
| `app/api/v1/endpoints/auth.py` | `app/modules/auth/presentation/endpoints.py` |
| `app/api/v1/endpoints/auth_config.py` | `app/modules/auth/presentation/endpoints.py` (merge) |
| `app/api/v1/endpoints/sso.py` | `app/modules/auth/presentation/endpoints.py` (merge) |
| `app/schemas/auth.py` | `app/modules/auth/presentation/schemas.py` |
| `app/schemas/auth_config.py` | `app/modules/auth/presentation/schemas.py` (merge) |
| `app/schemas/federacion.py` | `app/modules/auth/presentation/schemas.py` (merge) |

#### Users Module

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/usuario_service.py` | `app/modules/users/application/services/user_service.py` |
| `app/api/v1/endpoints/usuarios.py` | `app/modules/users/presentation/endpoints.py` |
| `app/schemas/usuario.py` | `app/modules/users/presentation/schemas.py` |
| `app/schemas/usuario_rol.py` | `app/modules/users/presentation/schemas.py` (merge) |
| `app/models/usuario.py` | `app/modules/users/domain/entities.py` (merge) |

#### RBAC Module

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/rol_service.py` | `app/modules/rbac/application/services/rol_service.py` |
| `app/services/permiso_service.py` | `app/modules/rbac/application/services/permiso_service.py` |
| `app/api/v1/endpoints/roles.py` | `app/modules/rbac/presentation/endpoints.py` |
| `app/api/v1/endpoints/permisos.py` | `app/modules/rbac/presentation/endpoints.py` (merge) |
| `app/schemas/rol.py` | `app/modules/rbac/presentation/schemas.py` |
| `app/schemas/rol_menu_permiso.py` | `app/modules/rbac/presentation/schemas.py` (merge) |

#### Menus Module

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/menu_service.py` | `app/modules/menus/application/services/menu_service.py` |
| `app/services/area_service.py` | `app/modules/menus/application/services/area_service.py` |
| `app/api/v1/endpoints/menus.py` | `app/modules/menus/presentation/endpoints.py` |
| `app/api/v1/endpoints/areas.py` | `app/modules/menus/presentation/endpoints.py` (merge) |
| `app/schemas/menu.py` | `app/modules/menus/presentation/schemas.py` |
| `app/schemas/area.py` | `app/modules/menus/presentation/schemas.py` (merge) |
| `app/models/menu.py` | `app/modules/menus/domain/entities.py` (merge) |
| `app/utils/menu_helper.py` | `app/modules/menus/application/services/menu_helper.py` |

#### Tenant Module

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/cliente_service.py` | `app/modules/tenant/application/services/cliente_service.py` |
| `app/services/conexion_service.py` | `app/modules/tenant/application/services/conexion_service.py` |
| `app/services/tenant_service.py` | `app/modules/tenant/application/services/tenant_service.py` |
| `app/api/v1/endpoints/clientes.py` | `app/modules/tenant/presentation/endpoints.py` |
| `app/api/v1/endpoints/conexiones.py` | `app/modules/tenant/presentation/endpoints.py` (merge) |
| `app/schemas/cliente.py` | `app/modules/tenant/presentation/schemas.py` |
| `app/schemas/conexion.py` | `app/modules/tenant/presentation/schemas.py` (merge) |

#### Superadmin Module

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/superadmin_usuario_service.py` | `app/modules/superadmin/application/services/superadmin_usuario_service.py` |
| `app/services/superadmin_auditoria_service.py` | `app/modules/superadmin/application/services/superadmin_auditoria_service.py` |
| `app/services/audit_service.py` | `app/modules/superadmin/application/services/audit_service.py` |
| `app/api/v1/endpoints/superadmin_usuarios.py` | `app/modules/superadmin/presentation/endpoints.py` |
| `app/api/v1/endpoints/superadmin_auditoria.py` | `app/modules/superadmin/presentation/endpoints.py` (merge) |
| `app/schemas/superadmin_usuario.py` | `app/modules/superadmin/presentation/schemas.py` |
| `app/schemas/superadmin_auditoria.py` | `app/modules/superadmin/presentation/schemas.py` (merge) |

#### Modules Module

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/modulo_service.py` | `app/modules/modules/application/services/modulo_service.py` |
| `app/services/modulo_activo_service.py` | `app/modules/modules/application/services/modulo_activo_service.py` |
| `app/api/v1/endpoints/modulos.py` | `app/modules/modules/presentation/endpoints.py` |
| `app/schemas/modulo.py` | `app/modules/modules/presentation/schemas.py` |
| `app/schemas/modulo_activo.py` | `app/modules/modules/presentation/schemas.py` (merge) |

#### Autorización (Domain Logic)

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/api/v1/endpoints/autorizacion.py` | `app/modules/rbac/presentation/endpoints.py` (merge) |
| `app/models/autorizacion.py` | `app/modules/rbac/domain/entities.py` (merge) |

### API Layer

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/api/deps.py` | `app/api/dependencies.py` |
| `app/api/v1/api.py` | `app/api/v1/router.py` |
| `app/main.py` | `app/main.py` (mantener) |

### Base Services

| Archivo Actual | Nueva Ubicación |
|----------------|----------------|
| `app/services/base_service.py` | `app/infrastructure/database/repositories/base_repository.py` (adaptar) |

---

## 🔄 Plan de Refactorización Paso a Paso

### Fase 1: Preparación y Core (Sin romper funcionalidad)

**Objetivo**: Reorganizar core sin afectar funcionalidad

1. **Crear estructura de carpetas**
   - Crear `app/core/security/`, `app/core/tenant/`, `app/core/authorization/`
   - Crear `app/infrastructure/database/`
   - Crear estructura base de `app/modules/`

2. **Mover archivos de Core**
   - Mover `security.py` → `core/security/password.py`
   - Mover `encryption.py` → `core/security/encryption.py`
   - Extraer JWT utils de `auth.py` → `core/security/jwt.py`
   - Mover `tenant_context.py` → `core/tenant/context.py`
   - Mover `multi_db.py` → `core/tenant/routing.py`
   - Mover `connection_cache.py` → `core/tenant/cache.py`
   - Mover `tenant_middleware.py` → `core/tenant/middleware.py`
   - Mover `authorization.py` → `core/authorization/rbac.py`
   - Mover `level_authorization.py` → `core/authorization/lbac.py`

3. **Actualizar imports**
   - Buscar y reemplazar todos los imports afectados
   - Verificar que no se rompa funcionalidad

4. **Mover Infrastructure**
   - Mover `db/connection.py` → `infrastructure/database/connection.py`
   - Mover `db/queries.py` → `infrastructure/database/queries.py`
   - Actualizar imports

### Fase 2: Módulo Auth (Primer módulo completo)

**Objetivo**: Refactorizar módulo de autenticación como ejemplo

1. **Crear estructura del módulo**
   - Crear `modules/auth/domain/`, `application/`, `infrastructure/`, `presentation/`

2. **Mover Domain**
   - Crear `domain/entities.py` con entidades de autenticación
   - Crear `domain/repositories.py` con interfaces

3. **Mover Application**
   - Mover servicios de auth a `application/services/`
   - Crear casos de uso en `application/use_cases/`

4. **Mover Infrastructure**
   - Crear repositorios en `infrastructure/repositories/`

5. **Mover Presentation**
   - Mover schemas a `presentation/schemas.py`
   - Mover endpoints a `presentation/endpoints.py`
   - Crear `presentation/dependencies.py`

6. **Actualizar router principal**
   - Importar endpoints desde nuevo módulo

7. **Testing**
   - Verificar que auth funciona correctamente

### Fase 3: Módulo Users

**Objetivo**: Refactorizar módulo de usuarios

1. **Crear estructura del módulo**
2. **Mover Domain** (entidades, value objects)
3. **Mover Application** (servicios, casos de uso)
4. **Mover Infrastructure** (repositorios)
5. **Mover Presentation** (schemas, endpoints)
6. **Actualizar imports y router**
7. **Testing**

### Fase 4: Módulo RBAC

**Objetivo**: Refactorizar roles y permisos

1. **Crear estructura del módulo**
2. **Mover Domain**
3. **Mover Application**
4. **Mover Infrastructure**
5. **Mover Presentation**
6. **Actualizar imports y router**
7. **Testing**

### Fase 5: Módulo Menus

**Objetivo**: Refactorizar menús y áreas

1. **Crear estructura del módulo**
2. **Mover Domain**
3. **Mover Application**
4. **Mover Infrastructure**
5. **Mover Presentation**
6. **Actualizar imports y router**
7. **Testing**

### Fase 6: Módulo Tenant

**Objetivo**: Refactorizar multi-tenant

1. **Crear estructura del módulo**
2. **Mover Domain**
3. **Mover Application**
4. **Mover Infrastructure**
5. **Mover Presentation**
6. **Actualizar imports y router**
7. **Testing**

### Fase 7: Módulo Superadmin

**Objetivo**: Refactorizar superadmin

1. **Crear estructura del módulo**
2. **Mover Domain**
3. **Mover Application**
4. **Mover Infrastructure**
5. **Mover Presentation**
6. **Actualizar imports y router**
7. **Testing**

### Fase 8: Módulo Modules

**Objetivo**: Refactorizar gestión de módulos

1. **Crear estructura del módulo**
2. **Mover Domain**
3. **Mover Application**
4. **Mover Infrastructure**
5. **Mover Presentation**
6. **Actualizar imports y router**
7. **Testing**

### Fase 9: Limpieza y Optimización

**Objetivo**: Limpiar código antiguo y optimizar

1. **Eliminar carpetas antiguas**
   - Eliminar `app/services/` (vacío)
   - Eliminar `app/api/v1/endpoints/` (vacío)
   - Eliminar `app/schemas/` (vacío)
   - Eliminar `app/models/` (vacío)
   - Eliminar `app/db/` (vacío)
   - Eliminar `app/middleware/` (vacío)
   - Eliminar `app/utils/` (vacío)

2. **Actualizar `main.py`**
   - Actualizar imports del router principal

3. **Actualizar `api/v1/router.py`**
   - Importar endpoints desde módulos

4. **Documentación**
   - Actualizar README con nueva estructura
   - Documentar arquitectura

5. **Testing completo**
   - Ejecutar todos los tests
   - Verificar que todo funciona

---

## ✅ Checklist de Validación

### Antes de Empezar

- [ ] Backup completo del código actual
- [ ] Crear branch de refactorización
- [ ] Documentar dependencias entre módulos
- [ ] Identificar tests existentes

### Durante el Refactor

- [ ] Cada fase debe mantener funcionalidad
- [ ] Actualizar imports inmediatamente
- [ ] Ejecutar tests después de cada fase
- [ ] No eliminar código antiguo hasta que el nuevo funcione

### Después del Refactor

- [ ] Todos los endpoints funcionan
- [ ] Autenticación funciona
- [ ] Multi-tenant funciona
- [ ] Tests pasan
- [ ] Documentación actualizada
- [ ] Código antiguo eliminado

---

## 🎯 Beneficios de la Nueva Arquitectura

1. **Separación de Responsabilidades**
   - Cada módulo es independiente
   - Fácil de entender y mantener

2. **Escalabilidad**
   - Preparado para extraer módulos a microservicios
   - Módulos pueden escalar independientemente

3. **Testabilidad**
   - Fácil mockear repositorios
   - Casos de uso aislados

4. **Mantenibilidad**
   - Código organizado por dominio
   - Fácil encontrar código relacionado

5. **Onboarding**
   - Nueva estructura más clara para nuevos desarrolladores
   - Documentación por módulo

---

## ⚠️ Consideraciones Importantes

1. **No romper funcionalidad**: Cada fase debe mantener la funcionalidad existente
2. **Imports**: Actualizar imports inmediatamente después de mover archivos
3. **Testing**: Ejecutar tests después de cada fase
4. **Git**: Hacer commits frecuentes por fase
5. **Documentación**: Actualizar documentación conforme se avanza

---

## 📝 Notas Finales

- Esta arquitectura mantiene **100% de compatibilidad** con el código actual
- **No se elimina ningún archivo** hasta que el nuevo esté funcionando
- La refactorización es **incremental** y **reversible**
- Cada módulo puede evolucionar **independientemente**

---

**¿Listo para comenzar el refactor?** 🚀




