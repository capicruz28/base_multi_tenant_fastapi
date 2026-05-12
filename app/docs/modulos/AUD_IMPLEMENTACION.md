## AUD — Implementación (Auditoría y Trazabilidad)

### Resumen
Se completó el ajuste del módulo **AUD** para alinear **RBAC** del endpoint de registro de auditoría y asegurar la existencia de **seeds** de permisos requeridos.

### Alcance (según BD)
- **Tabla**: `aud_log_auditoria` (log transaccional / consulta analítica)
- **Reglas**:
  - Filtro multi-tenant obligatorio por **`cliente_id`** en queries.
  - **`empresa_id`** presente en tabla y soportado como filtro en listado.
  - Sin CRUD completo (no `update/delete`) por tratarse de log.

### Endpoints del módulo
Base router: `app/modules/aud/presentation/endpoints.py` incluye:
- `prefix="/log-auditoria"`

Endpoints:
- **GET** `/log-auditoria` (listar con filtros)
  - **Tenant**: usa `current_user.cliente_id`
  - **RBAC**: `aud.log.leer`
- **GET** `/log-auditoria/{log_id}` (detalle)
  - **Tenant**: usa `current_user.cliente_id`
  - **RBAC**: `aud.log.leer`
- **POST** `/log-auditoria` (registro)
  - **Tenant**: inserta `cliente_id` desde `current_user.cliente_id`
  - **RBAC**: **`aud.log.crear`** (ajustado)

### Cambios realizados

#### 1) Routers
- **Archivo**: `app/modules/aud/presentation/endpoints_log_auditoria.py`
- **Cambio**: el permiso del endpoint **POST** se corrigió de `aud.log.leer` a **`aud.log.crear`**.
- **Contratos**: no se modificaron rutas, métodos, request models ni response models.

#### 2) RBAC (seeds)
- **Archivo nuevo**: `app/docs/database/SEED_PERMISOS_RBAC_AUD.sql`
- **Acción**: se agregó seed idempotente (`MERGE INTO permiso`) para asegurar los permisos:
  - `aud.log.leer`
  - `aud.log.crear`
- **Modulo_id** usado (catálogo módulos): `E100001B-0000-4000-8000-00000000001B` (AUD)

### Verificación final
- **Multi-tenant**:
  - `cliente_id` se aplica siempre en queries (`WHERE cliente_id = client_id`).
  - `empresa_id` se filtra cuando se envía como parámetro.
- **RBAC**:
  - Lectura protegida con `aud.log.leer`.
  - Registro protegido con `aud.log.crear`.
- **No se cambió** estructura de BD ni contratos de endpoints existentes.

### Archivos creados/modificados
- **Modificado**: `app/modules/aud/presentation/endpoints_log_auditoria.py`
- **Creado**: `app/docs/database/SEED_PERMISOS_RBAC_AUD.sql`
- **Creado (auditoría)**: `app/docs/modulos/AUDITORIA_AUD.md`
- **Creado (implementación)**: `app/docs/modulos/AUD_IMPLEMENTACION.md`

