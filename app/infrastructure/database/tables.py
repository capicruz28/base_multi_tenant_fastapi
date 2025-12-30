# app/infrastructure/database/tables.py
"""
Definiciones de tablas usando SQLAlchemy Core (Table).

✅ FASE 1: Refactorización de acceso a datos
- Todas las tablas del esquema SQL Server mapeadas a SQLAlchemy Core
- Permite construir queries tipadas y programáticas
- Elimina necesidad de raw SQL strings

USO:
    from app.infrastructure.database.tables import UsuarioTable, RolTable
    
    query = select(UsuarioTable).where(UsuarioTable.c.nombre_usuario == username)
    result = await execute_query(query)
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date, 
    ForeignKey, Text, Index, UniqueConstraint, CheckConstraint,
    MetaData, Numeric
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func
from datetime import datetime

# Metadata para todas las tablas
metadata = MetaData()

# ============================================================================
# TABLA: cliente
# ============================================================================
ClienteTable = Table(
    'cliente',
    metadata,
    Column('cliente_id', UNIQUEIDENTIFIER, primary_key=True),
    
    # Identificación y branding
    Column('codigo_cliente', String(20), nullable=False, unique=True),
    Column('subdominio', String(63), nullable=False, unique=True),
    Column('razon_social', String(200), nullable=False),
    Column('nombre_comercial', String(150), nullable=True),
    Column('ruc', String(11), nullable=True),
    
    # Configuración de instalación
    Column('tipo_instalacion', String(20), nullable=False, server_default='shared'),
    Column('servidor_api_local', String(255), nullable=True),
    
    # Autenticación
    Column('modo_autenticacion', String(20), nullable=False, server_default='local'),
    
    # Personalización visual
    Column('logo_url', String(500), nullable=True),
    Column('favicon_url', String(500), nullable=True),
    Column('color_primario', String(7), nullable=True, server_default='#1976D2'),
    Column('color_secundario', String(7), nullable=True, server_default='#424242'),
    Column('tema_personalizado', Text, nullable=True),
    
    # Estado y suscripción
    Column('plan_suscripcion', String(30), nullable=True, server_default='trial'),
    Column('estado_suscripcion', String(20), nullable=True, server_default='activo'),
    Column('fecha_inicio_suscripcion', Date, nullable=True),
    Column('fecha_fin_trial', Date, nullable=True),
    
    # Contacto principal
    Column('contacto_nombre', String(100), nullable=True),
    Column('contacto_email', String(100), nullable=False),
    Column('contacto_telefono', String(20), nullable=True),
    
    # Control de estado
    Column('es_activo', Boolean, nullable=False, server_default='1'),
    Column('es_demo', Boolean, nullable=True, server_default='0'),
    
    # Auditoría
    Column('fecha_creacion', DateTime, nullable=False, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    Column('fecha_ultimo_acceso', DateTime, nullable=True),
    
    # Sincronización
    Column('api_key_sincronizacion', String(255), nullable=True),
    Column('sincronizacion_habilitada', Boolean, nullable=True, server_default='0'),
    Column('ultima_sincronizacion', DateTime, nullable=True),
    
    # Metadatos extensibles
    Column('metadata_json', Text, nullable=True),
    
    # Índices
    Index('IDX_cliente_codigo', 'codigo_cliente'),
    Index('IDX_cliente_estado', 'es_activo', 'estado_suscripcion'),
    Index('IDX_cliente_tipo', 'tipo_instalacion'),
)

# ============================================================================
# TABLA: usuario
# ============================================================================
UsuarioTable = Table(
    'usuario',
    metadata,
    Column('usuario_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=False),
    
    # Credenciales
    Column('nombre_usuario', String(100), nullable=False),
    Column('contrasena', String(255), nullable=False),
    
    # Datos personales
    Column('nombre', String(100), nullable=True),
    Column('apellido', String(100), nullable=True),
    Column('correo', String(150), nullable=True),
    Column('dni', String(8), nullable=True),
    Column('telefono', String(20), nullable=True),
    
    # Configuración de autenticación
    Column('proveedor_autenticacion', String(30), nullable=False, server_default='local'),
    Column('referencia_externa_id', String(255), nullable=True),
    Column('referencia_externa_email', String(150), nullable=True),
    
    # Seguridad
    Column('es_activo', Boolean, nullable=False, server_default='1'),
    Column('correo_confirmado', Boolean, nullable=True, server_default='0'),
    Column('requiere_cambio_contrasena', Boolean, nullable=True, server_default='0'),
    Column('intentos_fallidos', Integer, nullable=True, server_default='0'),
    Column('fecha_bloqueo', DateTime, nullable=True),
    Column('fecha_ultimo_cambio_contrasena', DateTime, nullable=True),
    Column('ultimo_ip', String(45), nullable=True),
    
    # Sincronización
    Column('sincronizado_desde', String(30), nullable=True),
    Column('referencia_sincronizacion_id', UNIQUEIDENTIFIER, nullable=True),
    Column('fecha_ultima_sincronizacion', DateTime, nullable=True),
    Column('hash_datos_sincronizado', String(64), nullable=True),
    
    # Auditoría
    Column('fecha_creacion', DateTime, nullable=False, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    Column('fecha_ultimo_acceso', DateTime, nullable=True),
    
    # Eliminación lógica
    Column('es_eliminado', Boolean, nullable=True, server_default='0'),
    Column('fecha_eliminacion', DateTime, nullable=True),
    Column('usuario_eliminacion_id', UNIQUEIDENTIFIER, nullable=True),
    
    # Constraints
    UniqueConstraint('cliente_id', 'nombre_usuario', name='UQ_usuario_cliente_nombre'),
    
    # Índices
    Index('IDX_usuario_cliente', 'cliente_id', 'es_activo'),
    Index('IDX_usuario_correo', 'correo'),
    Index('IDX_usuario_dni', 'dni'),
    Index('IDX_usuario_referencia_externa', 'referencia_externa_id'),
    Index('IDX_usuario_sincronizacion', 'sincronizado_desde', 'fecha_ultima_sincronizacion'),
)

# ============================================================================
# TABLA: rol
# ============================================================================
RolTable = Table(
    'rol',
    metadata,
    Column('rol_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=True),
    
    # Identificación
    Column('codigo_rol', String(30), nullable=True),
    Column('nombre', String(50), nullable=False),
    Column('descripcion', String(255), nullable=True),
    
    # Configuración
    Column('es_rol_sistema', Boolean, nullable=True, server_default='0'),
    Column('nivel_acceso', Integer, nullable=True, server_default='1'),
    
    # Control
    Column('es_activo', Boolean, nullable=False, server_default='1'),
    Column('fecha_creacion', DateTime, nullable=False, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    
    # Constraints
    UniqueConstraint('cliente_id', 'nombre', name='UQ_rol_cliente_nombre'),
    
    # Índices
    Index('IDX_rol_cliente', 'cliente_id', 'es_activo'),
    Index('IDX_rol_codigo', 'codigo_rol'),
)

# ============================================================================
# TABLA: usuario_rol
# ============================================================================
UsuarioRolTable = Table(
    'usuario_rol',
    metadata,
    Column('usuario_rol_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('usuario_id', UNIQUEIDENTIFIER, ForeignKey('usuario.usuario_id', ondelete='CASCADE'), nullable=False),
    Column('rol_id', UNIQUEIDENTIFIER, ForeignKey('rol.rol_id', ondelete='CASCADE'), nullable=False),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='NO ACTION'), nullable=False),
    
    # Control
    Column('fecha_asignacion', DateTime, nullable=False, server_default=func.getdate()),
    Column('fecha_expiracion', DateTime, nullable=True),
    Column('es_activo', Boolean, nullable=False, server_default='1'),
    
    # Auditoría
    Column('asignado_por_usuario_id', UNIQUEIDENTIFIER, nullable=True),
    
    # Constraints
    UniqueConstraint('usuario_id', 'rol_id', name='UQ_usuario_rol'),
    
    # Índices
    Index('IDX_usuario_rol_usuario', 'usuario_id', 'es_activo'),
    Index('IDX_usuario_rol_rol', 'rol_id', 'es_activo'),
    Index('IDX_usuario_rol_cliente', 'cliente_id'),
)

# ============================================================================
# TABLAS DE MÓDULOS Y MENÚS
# ============================================================================
# Las tablas de módulos y menús han sido movidas a tables_modulos.py
# Importar desde allí:
#   from app.infrastructure.database.tables_modulos import (
#       ModuloTable, ClienteModuloTable, ModuloSeccionTable,
#       ModuloMenuTable, ModuloRolPlantillaTable
#   )

# ============================================================================
# TABLA: rol_menu_permiso
# ============================================================================
RolMenuPermisoTable = Table(
    'rol_menu_permiso',
    metadata,
    Column('permiso_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='NO ACTION'), nullable=False),
    Column('rol_id', UNIQUEIDENTIFIER, ForeignKey('rol.rol_id', ondelete='CASCADE'), nullable=False),
    Column('menu_id', UNIQUEIDENTIFIER, ForeignKey('modulo_menu.menu_id', ondelete='CASCADE'), nullable=False),
    
    # Permisos granulares
    Column('puede_ver', Boolean, nullable=False, server_default='1'),
    Column('puede_crear', Boolean, nullable=True, server_default='0'),
    Column('puede_editar', Boolean, nullable=True, server_default='0'),
    Column('puede_eliminar', Boolean, nullable=True, server_default='0'),
    Column('puede_exportar', Boolean, nullable=True, server_default='0'),
    Column('puede_imprimir', Boolean, nullable=True, server_default='0'),
    Column('puede_aprobar', Boolean, nullable=True, server_default='0'),
    
    # Permisos adicionales extensibles
    Column('permisos_extra', Text, nullable=True),
    
    Column('fecha_creacion', DateTime, nullable=False, server_default=func.getdate()),
    
    # Constraints
    # ✅ CORRECCIÓN: Incluir cliente_id en el constraint único según estructura_bd.sql
    UniqueConstraint('cliente_id', 'rol_id', 'menu_id', name='UQ_rol_menu'),
    
    # Índices
    Index('IDX_permiso_rol', 'rol_id', 'puede_ver'),
    Index('IDX_permiso_menu', 'menu_id'),
    Index('IDX_permiso_cliente', 'cliente_id'),
)

# ============================================================================
# TABLA: refresh_tokens
# ============================================================================
RefreshTokensTable = Table(
    'refresh_tokens',
    metadata,
    Column('token_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=False),
    Column('usuario_id', UNIQUEIDENTIFIER, ForeignKey('usuario.usuario_id', ondelete='CASCADE'), nullable=False),
    
    # Token
    Column('token_hash', String(255), nullable=False, unique=True),
    
    # Expiración y revocación
    Column('expires_at', DateTime, nullable=False),
    Column('is_revoked', Boolean, nullable=False, server_default='0'),
    Column('revoked_at', DateTime, nullable=True),
    Column('revoked_reason', String(100), nullable=True),
    
    # Información de la sesión
    Column('client_type', String(10), nullable=False, server_default='web'),
    Column('device_name', String(100), nullable=True),
    Column('device_id', String(100), nullable=True),
    Column('ip_address', String(45), nullable=True),
    Column('user_agent', String(500), nullable=True),
    
    # Control de uso
    Column('created_at', DateTime, nullable=False, server_default=func.getdate()),
    Column('last_used_at', DateTime, nullable=True),
    Column('uso_count', Integer, nullable=True, server_default='0'),
    
    # Índices
    Index('IDX_refresh_token_usuario_cliente', 'usuario_id', 'cliente_id'),
    Index('IDX_refresh_token_active', 'usuario_id', 'is_revoked', 'expires_at'),
    Index('IDX_refresh_token_cleanup', 'expires_at', 'is_revoked'),
    Index('IDX_refresh_token_device', 'device_id'),
)

# ============================================================================
# TABLA: cliente_modulo (ACTUALIZADA)
# ============================================================================
# La tabla cliente_modulo ha sido actualizada y movida a tables_modulos.py
# Importar desde allí: ClienteModuloTable

# ============================================================================
# TABLA: cliente_conexion
# ============================================================================
ClienteConexionTable = Table(
    'cliente_conexion',
    metadata,
    Column('conexion_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=False),
    
    # Información de conexión
    Column('servidor', String(255), nullable=False),
    Column('puerto', Integer, nullable=True, server_default='1433'),
    Column('nombre_bd', String(100), nullable=False),
    
    # Credenciales encriptadas
    Column('usuario_encriptado', String(500), nullable=False),
    Column('password_encriptado', String(500), nullable=False),
    Column('connection_string_encriptado', Text, nullable=True),
    
    # Configuración avanzada
    Column('tipo_bd', String(20), nullable=True, server_default='sqlserver'),
    Column('usa_ssl', Boolean, nullable=True, server_default='0'),
    Column('timeout_segundos', Integer, nullable=True, server_default='30'),
    Column('max_pool_size', Integer, nullable=True, server_default='100'),
    
    # Configuración de acceso
    Column('es_solo_lectura', Boolean, nullable=True, server_default='0'),
    Column('es_conexion_principal', Boolean, nullable=True, server_default='0'),
    
    # Estado y monitoreo
    Column('es_activo', Boolean, nullable=True, server_default='1'),
    Column('ultima_conexion_exitosa', DateTime, nullable=True),
    Column('ultimo_error', Text, nullable=True),
    Column('fecha_ultimo_error', DateTime, nullable=True),
    
    # Auditoría
    Column('fecha_creacion', DateTime, nullable=True, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    Column('creado_por_usuario_id', UNIQUEIDENTIFIER, nullable=True),
    
    # Constraints
    UniqueConstraint('cliente_id', 'es_conexion_principal', name='UQ_conexion_principal_cliente'),
    
    # Índices
    Index('IDX_conexion_cliente_', 'cliente_id', 'es_activo'),
    Index('IDX_conexion_principal', 'cliente_id', 'es_conexion_principal'),
)

# ============================================================================
# TABLA: cliente_modulo_activo (OBSOLETA)
# ============================================================================
# Esta tabla ha sido reemplazada por ClienteModuloTable en tables_modulos.py
# La tabla cliente_modulo_activo ahora es cliente_modulo con estructura actualizada

# ============================================================================
# TABLA: cliente_auth_config
# ============================================================================
ClienteAuthConfigTable = Table(
    'cliente_auth_config',
    metadata,
    Column('config_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=False, unique=True),
    
    # Políticas de contraseña
    Column('password_min_length', Integer, nullable=True, server_default='8'),
    Column('password_require_uppercase', Boolean, nullable=True, server_default='1'),
    Column('password_require_lowercase', Boolean, nullable=True, server_default='1'),
    Column('password_require_number', Boolean, nullable=True, server_default='1'),
    Column('password_require_special', Boolean, nullable=True, server_default='0'),
    Column('password_expiry_days', Integer, nullable=True, server_default='90'),
    Column('password_history_count', Integer, nullable=True, server_default='3'),
    
    # Control de acceso
    Column('max_login_attempts', Integer, nullable=True, server_default='5'),
    Column('lockout_duration_minutes', Integer, nullable=True, server_default='30'),
    Column('max_active_sessions', Integer, nullable=True, server_default='3'),
    Column('session_idle_timeout_minutes', Integer, nullable=True, server_default='60'),
    
    # Tokens JWT
    Column('access_token_minutes', Integer, nullable=True, server_default='15'),
    Column('refresh_token_days', Integer, nullable=True, server_default='30'),
    
    # Opciones de login
    Column('allow_remember_me', Boolean, nullable=True, server_default='1'),
    Column('remember_me_days', Integer, nullable=True, server_default='30'),
    Column('require_email_verification', Boolean, nullable=True, server_default='0'),
    Column('allow_password_reset', Boolean, nullable=True, server_default='1'),
    
    # Autenticación de dos factores
    Column('enable_2fa', Boolean, nullable=True, server_default='0'),
    Column('require_2fa_for_admins', Boolean, nullable=True, server_default='0'),
    Column('metodos_2fa_permitidos', String(100), nullable=True, server_default='email,sms'),
    
    # Whitelist/Blacklist de IPs
    Column('ip_whitelist_enabled', Boolean, nullable=True, server_default='0'),
    Column('ip_whitelist', Text, nullable=True),
    Column('ip_blacklist', Text, nullable=True),
    
    # Horarios de acceso
    Column('horario_acceso_enabled', Boolean, nullable=True, server_default='0'),
    Column('horario_acceso_config', Text, nullable=True),
    
    Column('fecha_creacion', DateTime, nullable=False, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
)

# ============================================================================
# TABLA: federacion_identidad
# ============================================================================
FederacionIdentidadTable = Table(
    'federacion_identidad',
    metadata,
    Column('federacion_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=False),
    
    # Identificación
    Column('nombre_configuracion', String(100), nullable=False),
    Column('proveedor', String(30), nullable=False),
    
    # Configuración OAuth 2.0 / OpenID Connect
    Column('client_id', String(255), nullable=True),
    Column('client_secret_encrypted', String(500), nullable=True),
    Column('authority_url', String(500), nullable=True),
    Column('token_endpoint', String(500), nullable=True),
    Column('authorization_endpoint', String(500), nullable=True),
    Column('userinfo_endpoint', String(500), nullable=True),
    Column('redirect_uri', String(500), nullable=True),
    Column('scope', String(200), nullable=True, server_default='openid profile email'),
    
    # Configuración SAML 2.0
    Column('entity_id', String(500), nullable=True),
    Column('sso_url', String(500), nullable=True),
    Column('slo_url', String(500), nullable=True),
    Column('certificate_x509', Text, nullable=True),
    
    # Mapeo de atributos
    Column('attribute_mapping', Text, nullable=True),
    
    # Configuración de comportamiento
    Column('es_activo', Boolean, nullable=False, server_default='1'),
    Column('es_metodo_principal', Boolean, nullable=True, server_default='0'),
    Column('auto_provision_users', Boolean, nullable=True, server_default='1'),
    Column('sync_user_data', Boolean, nullable=True, server_default='1'),
    
    # Auditoría
    Column('fecha_creacion', DateTime, nullable=False, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    Column('ultimo_login_sso', DateTime, nullable=True),
    
    # Índices
    Index('IDX_federacion_cliente', 'cliente_id', 'es_activo'),
    Index('IDX_federacion_proveedor', 'proveedor'),
)

# ============================================================================
# TABLA: log_sincronizacion_usuario
# ============================================================================
LogSincronizacionUsuarioTable = Table(
    'log_sincronizacion_usuario',
    metadata,
    Column('log_id', UNIQUEIDENTIFIER, primary_key=True),
    
    # Contexto de la sincronización
    Column('cliente_origen_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='NO ACTION'), nullable=True),
    Column('cliente_destino_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='NO ACTION'), nullable=True),
    Column('usuario_id', UNIQUEIDENTIFIER, ForeignKey('usuario.usuario_id', ondelete='CASCADE'), nullable=False),
    
    # Detalles de la operación
    Column('tipo_sincronizacion', String(20), nullable=False),
    Column('direccion', String(10), nullable=False),
    Column('operacion', String(20), nullable=False),
    
    # Resultado
    Column('estado', String(20), nullable=False),
    Column('mensaje_error', Text, nullable=True),
    
    # Datos de la sincronización
    Column('campos_sincronizados', Text, nullable=True),
    Column('cambios_detectados', Text, nullable=True),
    Column('hash_antes', String(64), nullable=True),
    Column('hash_despues', String(64), nullable=True),
    
    # Auditoría
    Column('fecha_sincronizacion', DateTime, nullable=False, server_default=func.getdate()),
    Column('usuario_ejecutor_id', UNIQUEIDENTIFIER, nullable=True),
    Column('duracion_ms', Integer, nullable=True),
    
    # Índices
    Index('IDX_log_sync_usuario', 'usuario_id', 'fecha_sincronizacion'),
    Index('IDX_log_sync_origen', 'cliente_origen_id', 'estado'),
    Index('IDX_log_sync_destino', 'cliente_destino_id', 'estado'),
    Index('IDX_log_sync_fecha', 'fecha_sincronizacion'),
)

# ============================================================================
# TABLA: auth_audit_log
# ============================================================================
AuthAuditLogTable = Table(
    'auth_audit_log',
    metadata,
    Column('log_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=False),
    Column('usuario_id', UNIQUEIDENTIFIER, ForeignKey('usuario.usuario_id', ondelete='SET NULL'), nullable=True),
    
    # Evento
    Column('evento', String(50), nullable=False),
    Column('nombre_usuario_intento', String(100), nullable=True),
    
    # Detalles
    Column('descripcion', String(500), nullable=True),
    Column('exito', Boolean, nullable=False),
    Column('codigo_error', String(50), nullable=True),
    
    # Contexto técnico
    Column('ip_address', String(45), nullable=True),
    Column('user_agent', String(500), nullable=True),
    Column('device_info', String(200), nullable=True),
    Column('geolocation', String(100), nullable=True),
    
    # Metadata adicional
    Column('metadata_json', Text, nullable=True),
    Column('fecha_evento', DateTime, nullable=False, server_default=func.getdate()),
    
    # Índices
    Index('IDX_audit_cliente_fecha', 'cliente_id', 'fecha_evento'),
    Index('IDX_audit_usuario_fecha', 'usuario_id', 'fecha_evento'),
    Index('IDX_audit_evento', 'evento', 'fecha_evento'),
    Index('IDX_audit_exito', 'exito', 'fecha_evento'),
    Index('IDX_audit_ip', 'ip_address', 'fecha_evento'),
)

# ============================================================================
# EXPORTAR TODAS LAS TABLAS
# ============================================================================
__all__ = [
    'metadata',
    'ClienteTable',
    'UsuarioTable',
    'RolTable',
    'UsuarioRolTable',
    'RolMenuPermisoTable',
    'RefreshTokensTable',
    'ClienteConexionTable',
    'ClienteAuthConfigTable',
    'FederacionIdentidadTable',
    'LogSincronizacionUsuarioTable',
    'AuthAuditLogTable',
    # Tablas de módulos y menús están en tables_modulos.py
    # Importar desde allí: ModuloTable, ClienteModuloTable, ModuloSeccionTable,
    #                      ModuloMenuTable, ModuloRolPlantillaTable
]

