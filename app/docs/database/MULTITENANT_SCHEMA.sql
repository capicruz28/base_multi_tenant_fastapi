-- ============================================================================
-- TABLA: cliente
-- Propósito: Core del sistema multi-tenant. Cada cliente es una empresa/organización
-- Aislamiento: Por cliente_id + subdominio único
-- Casos de uso:
--   - Múltiples clientes en mismo servidor (cloud)
--   - Cada cliente con BD dedicada (cloud)
--   - Clientes con servidor propio (on-premise)
-- ============================================================================

CREATE TABLE cliente (
cliente_id INT PRIMARY KEY IDENTITY(1,1),
-- ========================================
-- IDENTIFICACIÓN Y BRANDING
-- ========================================
codigo_cliente NVARCHAR(20) NOT NULL UNIQUE,  
-- Código corto único para identificar al cliente
-- Ejemplos: 'CLI001', 'ACME', 'BANCO01'

subdominio NVARCHAR(63) NOT NULL UNIQUE,      
-- Subdominio único para acceso web (RFC 1035: máx 63 chars)
-- Ejemplos: 'acme' → accede en acme.tuapp.com
--           'banco' → accede en banco.tuapp.com
-- IMPORTANTE: Validar en app que solo contenga [a-z0-9-]

razon_social NVARCHAR(200) NOT NULL,          
-- Nombre legal completo de la empresa
-- Ejemplo: 'ACME Corporation S.A.C.'

nombre_comercial NVARCHAR(150) NULL,          
-- Nombre corto para mostrar en UI
-- Ejemplo: 'ACME'

ruc NVARCHAR(11) NULL,                        
-- RUC del cliente (solo informativo/facturación)
-- Perú: 11 dígitos. Ajustar según país
-- NO se usa para autenticación

-- ========================================
-- CONFIGURACIÓN DE INSTALACIÓN
-- ========================================
tipo_instalacion NVARCHAR(20) DEFAULT 'cloud' NOT NULL,
-- Define dónde corre el sistema para este cliente:
--   'cloud'      = Tu servidor centralizado (caso 1 y 2)
--   'onpremise'  = Servidor local del cliente (caso 3)
--   'hybrid'     = Local pero sincroniza con central

servidor_api_local NVARCHAR(255) NULL,       
-- URL del API si el cliente tiene instalación local
-- Ejemplos: 'https://api.cliente.local'
--           'https://planillas.bancoxyz.pe'
-- Solo se llena si tipo_instalacion = 'onpremise' o 'hybrid'

-- ========================================
-- AUTENTICACIÓN
-- ========================================
modo_autenticacion NVARCHAR(20) DEFAULT 'local' NOT NULL,
-- Define cómo se autentican los usuarios:
--   'local'  = Usuario + contraseña en nuestra BD
--   'sso'    = Solo federación de identidad (Azure AD, Google, etc)
--   'hybrid' = Ambos métodos habilitados

-- ========================================
-- PERSONALIZACIÓN VISUAL (BRANDING)
-- ========================================
logo_url NVARCHAR(500) NULL,                  
-- URL pública del logo del cliente
-- Ejemplo: 'https://cdn.tuapp.com/logos/acme.png'

favicon_url NVARCHAR(500) NULL,               
-- URL del favicon personalizado

color_primario NVARCHAR(7) DEFAULT '#1976D2', 
-- Color principal en formato HEX: #RRGGBB
-- Se aplica en botones, headers, etc.

color_secundario NVARCHAR(7) DEFAULT '#424242',
-- Color secundario para acentos

tema_personalizado NVARCHAR(MAX) NULL,        
-- JSON con configuración avanzada de tema
-- Ejemplo: {"font": "Roboto", "borderRadius": "8px"}

-- ========================================
-- ESTADO Y SUSCRIPCIÓN
-- ========================================
plan_suscripcion NVARCHAR(30) DEFAULT 'trial',
-- Plan contratado: 'trial', 'basico', 'profesional', 'enterprise'

estado_suscripcion NVARCHAR(20) DEFAULT 'activo',
-- Estado actual: 'trial', 'activo', 'suspendido', 'cancelado', 'moroso'

fecha_inicio_suscripcion DATE NULL,
-- Fecha de inicio de la suscripción pagada

fecha_fin_trial DATE NULL,
-- Fecha de fin del periodo de prueba
-- Si es NULL y plan='trial', entonces trial ilimitado

-- ========================================
-- CONTACTO PRINCIPAL
-- ========================================
contacto_nombre NVARCHAR(100) NULL,
-- Nombre del contacto administrativo del cliente

contacto_email NVARCHAR(100) NOT NULL,        
-- Email del administrador principal (REQUERIDO)
-- Se usa para notificaciones importantes

contacto_telefono NVARCHAR(20) NULL,
-- Teléfono de contacto

-- ========================================
-- CONTROL DE ESTADO
-- ========================================
es_activo BIT DEFAULT 1 NOT NULL,
-- Si está inactivo, bloquea acceso a todos los usuarios del cliente

es_demo BIT DEFAULT 0,                        
-- Marca clientes de demostración (datos de prueba)

-- ========================================
-- AUDITORÍA
-- ========================================
fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,

fecha_actualizacion DATETIME NULL,
-- Se actualiza cada vez que cambia algún campo

fecha_ultimo_acceso DATETIME NULL,            
-- Última vez que algún usuario del cliente accedió al sistema
-- Se actualiza en cada login exitoso

-- ========================================
-- SINCRONIZACIÓN (Para instalaciones locales)
-- ========================================
api_key_sincronizacion NVARCHAR(255) NULL,    
-- API Key única para que el cliente se autentique con servidor central
-- Solo se usa si tipo_instalacion = 'onpremise' o 'hybrid'
-- Debe ser un token seguro generado aleatoriamente

sincronizacion_habilitada BIT DEFAULT 0,
-- Si permite sincronización bidireccional con servidor central

ultima_sincronizacion DATETIME NULL,
-- Última vez que se sincronizó (cualquier entidad)

-- ========================================
-- METADATOS EXTENSIBLES
-- ========================================
metadata_json NVARCHAR(MAX) NULL              
-- JSON para configuraciones custom sin alterar schema
-- Ejemplo: {"fiscal_year_start": "04-01", "timezone": "America/Lima"}
);

-- Índices optimizados para queries frecuentes
CREATE UNIQUE INDEX UQ_cliente_subdominio ON cliente(subdominio) WHERE es_activo = 1;
CREATE INDEX IDX_cliente_codigo ON cliente(codigo_cliente);
CREATE INDEX IDX_cliente_estado ON cliente(es_activo, estado_suscripcion);
CREATE INDEX IDX_cliente_tipo ON cliente(tipo_instalacion);

-- ============================================================================
-- TABLA: usuario
-- Propósito: Usuarios del sistema, segmentados por cliente
-- Autenticación: nombre_usuario + contraseña (nombre_usuario es flexible)
-- Multi-tenant: Cada usuario pertenece a UN solo cliente
-- ============================================================================
CREATE TABLE usuario (
usuario_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NOT NULL,                      
-- FK al cliente al que pertenece este usuario
-- CRÍTICO: Todas las queries DEBEN filtrar por cliente_id

-- ========================================
-- CREDENCIALES (Autenticación local)
-- ========================================
nombre_usuario NVARCHAR(100) NOT NULL,        
-- Campo FLEXIBLE: puede contener:
--   - Username tradicional: 'carlos.perez'
--   - DNI: '42799662'
--   - Email: 'carlos@empresa.com'
--   - Código empleado: 'EMP001'
-- El cliente decide qué formato usar
-- Se valida único POR CLIENTE (no globalmente)

contrasena NVARCHAR(255) NOT NULL,            
-- Hash bcrypt de la contraseña
-- NUNCA guardar en texto plano
-- Si usa SSO exclusivo, puede ser hash dummy

-- ========================================
-- DATOS PERSONALES
-- ========================================
nombre NVARCHAR(100) NULL,
apellido NVARCHAR(100) NULL,

correo NVARCHAR(150) NULL,                    
-- Email real del usuario (puede diferir de nombre_usuario)
-- Se usa para notificaciones, recuperación de contraseña

dni NVARCHAR(8) NULL,                         
-- DNI solo para registro/información (NO para login)
-- Ajustar longitud según país

telefono NVARCHAR(20) NULL,

-- ========================================
-- CONFIGURACIÓN DE AUTENTICACIÓN
-- ========================================
proveedor_autenticacion NVARCHAR(30) DEFAULT 'local' NOT NULL,
-- Define cómo se autentica este usuario específico:
--   'local'     = Usuario/password en nuestra BD
--   'azure_ad'  = Azure Active Directory
--   'google'    = Google Workspace
--   'okta'      = Okta
--   'oidc'      = OpenID Connect genérico
--   'saml'      = SAML 2.0

referencia_externa_id NVARCHAR(255) NULL,     
-- ID del usuario en el proveedor externo
-- Ejemplos: 
--   Azure AD: 'f8e7d6c5-b4a3-2918-7f6e-5d4c3b2a1098' (ObjectId)
--   Google: '123456789012345678901' (Google User ID)

referencia_externa_email NVARCHAR(150) NULL,  
-- Email en el proveedor externo (puede diferir del correo local)

-- ========================================
-- SEGURIDAD
-- ========================================
es_activo BIT DEFAULT 1 NOT NULL,
-- Si está inactivo, no puede hacer login

correo_confirmado BIT DEFAULT 0,
-- Si ha verificado su email

requiere_cambio_contrasena BIT DEFAULT 0,     
-- Forzar cambio de password en próximo login
-- Útil para passwords temporales o después de reset

intentos_fallidos INT DEFAULT 0,
-- Contador de intentos de login fallidos consecutivos
-- Se resetea a 0 en login exitoso

fecha_bloqueo DATETIME NULL,                  
-- Si no es NULL, la cuenta está bloqueada temporalmente
-- Se desbloquea automáticamente después de N minutos

fecha_ultimo_cambio_contrasena DATETIME NULL,
-- Para validar expiración de contraseñas

ultimo_ip NVARCHAR(45) NULL,                  
-- Última IP desde donde accedió (IPv4 o IPv6)

-- ========================================
-- SINCRONIZACIÓN (Para multi-instalación)
-- ========================================
sincronizado_desde NVARCHAR(30) NULL,         
-- Indica el origen del usuario:
--   NULL         = Creado localmente
--   'central'    = Sincronizado desde servidor central
--   'local'      = Enviado a servidor central desde aquí
--   'cliente_XXX'= Sincronizado desde otro cliente

referencia_sincronizacion_id INT NULL,        
-- ID del usuario en el sistema origen

fecha_ultima_sincronizacion DATETIME NULL,
-- Última vez que se sincronizó este usuario

hash_datos_sincronizado NVARCHAR(64) NULL,    
-- SHA-256 de datos clave para detectar cambios
-- Se calcula automáticamente por trigger

-- ========================================
-- AUDITORÍA
-- ========================================
fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,

fecha_actualizacion DATETIME NULL,
-- Se actualiza cada vez que cambia algún campo

fecha_ultimo_acceso DATETIME NULL,
-- Última vez que hizo login exitoso

-- ========================================
-- ELIMINACIÓN LÓGICA (Soft Delete)
-- ========================================
es_eliminado BIT DEFAULT 0,
-- No se eliminan registros físicamente por auditoría

fecha_eliminacion DATETIME NULL,

usuario_eliminacion_id INT NULL,              
-- Quién eliminó este usuario (para auditoría)

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_usuario_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE,

-- UNIQUE: nombre_usuario único POR CLIENTE (no globalmente)
CONSTRAINT UQ_usuario_cliente_nombre UNIQUE (cliente_id, nombre_usuario)
);
-- Índices optimizados
CREATE INDEX IDX_usuario_cliente ON usuario(cliente_id, es_activo) WHERE es_eliminado = 0;
CREATE INDEX IDX_usuario_correo ON usuario(correo) WHERE correo IS NOT NULL;
CREATE INDEX IDX_usuario_dni ON usuario(dni) WHERE dni IS NOT NULL;
CREATE INDEX IDX_usuario_referencia_externa ON usuario(referencia_externa_id) WHERE referencia_externa_id IS NOT NULL;
CREATE INDEX IDX_usuario_sincronizacion ON usuario(sincronizado_desde, fecha_ultima_sincronizacion);

-- ============================================================================
-- TABLA: rol
-- Propósito: Roles para agrupar permisos
-- Estrategia: Soporta roles globales (sistema) y roles por cliente
-- ============================================================================
CREATE TABLE rol (
rol_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NULL,                          
-- NULL = Rol global del sistema (ej: SUPER_ADMIN)
-- Con valor = Rol específico de un cliente

-- ========================================
-- IDENTIFICACIÓN
-- ========================================
codigo_rol NVARCHAR(30) NULL,                 
-- Código único para referencia en código
-- Ejemplos: 'ADMIN', 'USER', 'SUPERVISOR', 'GERENTE'
-- Solo los roles del sistema tienen código

nombre NVARCHAR(50) NOT NULL,
-- Nombre descriptivo del rol
-- Ejemplo: 'Administrador', 'Usuario Estándar'

descripcion NVARCHAR(255) NULL,
-- Descripción detallada de qué puede hacer este rol

-- ========================================
-- CONFIGURACIÓN
-- ========================================
es_rol_sistema BIT DEFAULT 0,                 
-- True = Creado por el sistema, no editable por usuarios
-- False = Creado por cliente, puede editarse

nivel_acceso INT DEFAULT 1,                   
-- Nivel jerárquico del rol (1=básico, 5=máximo)
-- Útil para validaciones: un nivel 2 no puede modificar nivel 3

-- ========================================
-- CONTROL
-- ========================================
es_activo BIT DEFAULT 1 NOT NULL,

fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
fecha_actualizacion DATETIME NULL,

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_rol_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE,

-- UNIQUE: nombre único por cliente (o globalmente si cliente_id es NULL)
CONSTRAINT UQ_rol_cliente_nombre UNIQUE (cliente_id, nombre)
);
-- Índices
CREATE INDEX IDX_rol_cliente ON rol(cliente_id, es_activo);
CREATE INDEX IDX_rol_codigo ON rol(codigo_rol)
WHERE codigo_rol IS NOT NULL;

-- ============================================================================
-- TABLA: usuario_rol
-- Propósito: Relación N:N entre usuarios y roles
-- Un usuario puede tener múltiples roles
-- ============================================================================
CREATE TABLE usuario_rol (
usuario_rol_id INT PRIMARY KEY IDENTITY(1,1),
usuario_id INT NOT NULL,
rol_id INT NOT NULL,
cliente_id INT NOT NULL,                      
-- Desnormalizado para queries rápidas

-- ========================================
-- CONTROL
-- ========================================
fecha_asignacion DATETIME DEFAULT GETDATE() NOT NULL,

fecha_expiracion DATETIME NULL,               
-- Para roles temporales (ej: supervisor por 3 meses)
-- NULL = permanente

es_activo BIT DEFAULT 1 NOT NULL,

-- ========================================
-- AUDITORÍA
-- ========================================
asignado_por_usuario_id INT NULL,             
-- Quién asignó este rol

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_usuario_rol_usuario FOREIGN KEY (usuario_id) 
    REFERENCES usuario(usuario_id) ON DELETE CASCADE,
CONSTRAINT FK_usuario_rol_rol FOREIGN KEY (rol_id) 
    REFERENCES rol(rol_id) ON DELETE CASCADE,
CONSTRAINT FK_usuario_rol_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION,

-- Un usuario no puede tener el mismo rol dos veces
CONSTRAINT UQ_usuario_rol UNIQUE (usuario_id, rol_id)
);
-- Índices
CREATE INDEX IDX_usuario_rol_usuario ON usuario_rol(usuario_id, es_activo);
CREATE INDEX IDX_usuario_rol_rol ON usuario_rol(rol_id, es_activo);
CREATE INDEX IDX_usuario_rol_cliente ON usuario_rol(cliente_id);

-- ============================================================================
-- TABLA: area_menu
-- Propósito: Agrupación lógica de menús (ej: "Planillas", "RRHH", "Reportes")
-- Estrategia: Áreas globales del sistema + áreas custom por cliente
-- ============================================================================
CREATE TABLE area_menu (
area_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NULL,                          
-- NULL = Área global del sistema
-- Con valor = Área específica del cliente

nombre NVARCHAR(100) NOT NULL,
descripcion NVARCHAR(255) NULL,

icono NVARCHAR(50) NULL,                      
-- Nombre del icono (depende de librería UI usada)
-- Ejemplos: 'dashboard', 'people', 'receipt', 'bar_chart'

orden INT DEFAULT 0,                          
-- Para ordenar áreas en el menú (menor = primero)

es_area_sistema BIT DEFAULT 0,                
-- True = Área del sistema, no editable

es_activo BIT DEFAULT 1 NOT NULL,
fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,

CONSTRAINT FK_area_menu_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE
);
-- Índices
CREATE INDEX IDX_area_menu_cliente ON area_menu(cliente_id, es_activo, orden);

-- ============================================================================
-- TABLA: menu
-- Propósito: Opciones de menú del sistema (rutas, pantallas)
-- Jerarquía: Soporta menús padre-hijo (submenús) mediante padre_menu_id
-- ============================================================================
CREATE TABLE menu (
menu_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NULL,                          
-- NULL = Menú global del sistema
-- Con valor = Menú específico del cliente

area_id INT NULL,                             
-- FK al área de menú (puede ser NULL para menús sueltos)

nombre NVARCHAR(100) NOT NULL,
descripcion NVARCHAR(255) NULL,

icono NVARCHAR(50) NULL,                      
-- Icono del menú

ruta NVARCHAR(255) NULL,                      
-- Path de la ruta en el frontend
-- Ejemplos: '/planillas/empleados', '/reportes/ventas'

-- ========================================
-- JERARQUÍA (para submenús)
-- ========================================
padre_menu_id INT NULL,                       
-- FK recursivo a menu(menu_id)
-- NULL = menú raíz, Con valor = es submenú

orden INT DEFAULT 0,                          
-- Orden dentro del área o dentro del padre

-- ========================================
-- CONFIGURACIÓN
-- ========================================
es_menu_sistema BIT DEFAULT 0,                
-- True = Menú del sistema, no editable

requiere_autenticacion BIT DEFAULT 1,         
-- Si requiere estar logueado para acceder

es_visible BIT DEFAULT 1,                     
-- Si se muestra en el menú (puede estar oculto pero accesible)

es_activo BIT DEFAULT 1 NOT NULL,

fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_menu_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE,
CONSTRAINT FK_menu_area FOREIGN KEY (area_id) 
    REFERENCES area_menu(area_id) ON DELETE SET NULL,
CONSTRAINT FK_menu_padre FOREIGN KEY (padre_menu_id) 
    REFERENCES menu(menu_id) ON DELETE NO ACTION  -- Evitar cascada en jerarquía
);
-- Índices
CREATE INDEX IDX_menu_cliente ON menu(cliente_id, es_activo, orden);
CREATE INDEX IDX_menu_area ON menu(area_id, orden);
CREATE INDEX IDX_menu_padre ON menu(padre_menu_id, orden);
CREATE INDEX IDX_menu_ruta ON menu(ruta) WHERE ruta IS NOT NULL;

-- ============================================================================
-- TABLA: rol_menu_permiso
-- Propósito: Permisos granulares de roles sobre menús
-- Define qué puede hacer cada rol en cada menú
-- ============================================================================
CREATE TABLE rol_menu_permiso (
permiso_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NOT NULL,                      
-- Desnormalizado para queries rápidas

rol_id INT NOT NULL,
menu_id INT NOT NULL,

-- ========================================
-- PERMISOS GRANULARES (Modelo CRUD extendido)
-- ========================================
puede_ver BIT DEFAULT 1 NOT NULL,             
-- Ver el menú y acceder a la pantalla

puede_crear BIT DEFAULT 0,                    
-- Crear nuevos registros en este módulo

puede_editar BIT DEFAULT 0,                   
-- Modificar registros existentes

puede_eliminar BIT DEFAULT 0,                 
-- Eliminar registros

puede_exportar BIT DEFAULT 0,                 
-- Exportar datos (Excel, PDF, CSV, etc.)

puede_imprimir BIT DEFAULT 0,                 
-- Imprimir reportes

-- ========================================
-- PERMISOS ADICIONALES EXTENSIBLES
-- ========================================
permisos_extra NVARCHAR(MAX) NULL,            
-- JSON con permisos custom específicos del módulo
-- Ejemplo: {"aprobar_planilla": true, "cerrar_periodo": false}

fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_permiso_rol FOREIGN KEY (rol_id) 
    REFERENCES rol(rol_id) ON DELETE CASCADE,
CONSTRAINT FK_permiso_menu FOREIGN KEY (menu_id) 
    REFERENCES menu(menu_id) ON DELETE CASCADE,
CONSTRAINT FK_permiso_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION,

-- Un rol no puede tener permisos duplicados sobre el mismo menú
CONSTRAINT UQ_rol_menu UNIQUE (rol_id, menu_id)
);
-- Índices optimizados para consultas de permisos
CREATE INDEX IDX_permiso_rol ON rol_menu_permiso(rol_id, puede_ver);
CREATE INDEX IDX_permiso_menu ON rol_menu_permiso(menu_id);
CREATE INDEX IDX_permiso_cliente ON rol_menu_permiso(cliente_id);

-- ============================================================================
-- TABLA: refresh_token
-- Propósito: Almacenar refresh tokens para autenticación JWT
-- Seguridad: Tokens hasheados (SHA-256), nunca en texto plano
-- Permite: Revocación de tokens, tracking de sesiones
-- ============================================================================
CREATE TABLE refresh_token (
token_id INT IDENTITY(1,1) PRIMARY KEY,
cliente_id INT NOT NULL,
usuario_id INT NOT NULL,

-- ========================================
-- TOKEN (Hasheado por seguridad)
-- ========================================
token_hash VARCHAR(255) NOT NULL UNIQUE,      
-- SHA-256 del refresh token JWT
-- NUNCA guardar el token en texto plano

-- ========================================
-- EXPIRACIÓN Y REVOCACIÓN
-- ========================================
expires_at DATETIME NOT NULL,
-- Fecha/hora de expiración del token

is_revoked BIT DEFAULT 0 NOT NULL,
-- Si fue revocado manualmente (logout, seguridad, admin)

revoked_at DATETIME NULL,
-- Cuándo fue revocado

revoked_reason NVARCHAR(100) NULL,            
-- Motivo de revocación: 'logout', 'security', 'expired', 'admin', 'password_change'

-- ========================================
-- INFORMACIÓN DE LA SESIÓN
-- ========================================
client_type VARCHAR(10) DEFAULT 'web' NOT NULL,
-- Tipo de cliente: 'web', 'mobile', 'desktop'

device_name NVARCHAR(100) NULL,               
-- Nombre del dispositivo (útil para mostrar al usuario)
-- Ejemplos: 'iPhone 13 Pro', 'Chrome en Windows 11', 'Samsung Galaxy S21'

device_id NVARCHAR(100) NULL,                 
-- ID único del dispositivo (para apps móviles)
-- Permite identificar el dispositivo específico

ip_address VARCHAR(45) NULL,                  
-- IP desde donde se creó el token (IPv4 o IPv6)

user_agent VARCHAR(500) NULL,                 
-- User agent del navegador/app

-- ========================================
-- CONTROL DE USO
-- ========================================
created_at DATETIME DEFAULT GETDATE() NOT NULL,

last_used_at DATETIME NULL,                   
-- Última vez que se usó este token para refrescar

uso_count INT DEFAULT 0,                      
-- Cuántas veces se ha usado para refrescar
-- Útil para detectar anomalías

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_refresh_token_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE,
CONSTRAINT FK_refresh_token_usuario FOREIGN KEY (usuario_id) 
    REFERENCES usuario(usuario_id) ON DELETE CASCADE
);
-- Índices optimizados
CREATE INDEX IDX_refresh_token_usuario_cliente ON refresh_token(usuario_id, cliente_id);
CREATE INDEX IDX_refresh_token_active ON refresh_token(usuario_id, is_revoked, expires_at);
CREATE INDEX IDX_refresh_token_cleanup ON refresh_token(expires_at, is_revoked);
CREATE INDEX IDX_refresh_token_device ON refresh_token(device_id) WHERE device_id IS NOT NULL;

-- ============================================================================
-- TABLA: cliente_modulo
-- Propósito: Catálogo de módulos disponibles en el sistema
-- Ejemplos: Planillas, Contabilidad, Producción, Ventas, RRHH
-- ============================================================================
CREATE TABLE cliente_modulo (
modulo_id INT PRIMARY KEY IDENTITY(1,1),
codigo_modulo NVARCHAR(30) NOT NULL UNIQUE,   
-- Código único para referencia en código
-- Ejemplos: 'PLANILLAS', 'CONTABILIDAD', 'PRODUCCION', 'VENTAS'

nombre NVARCHAR(100) NOT NULL,
descripcion NVARCHAR(255) NULL,

icono NVARCHAR(50) NULL,
-- Icono representativo del módulo
-- ========================================
-- CONFIGURACIÓN
-- ========================================
es_modulo_core BIT DEFAULT 0,                 
-- True = Módulo esencial del sistema (siempre disponible)
-- False = Módulo opcional/adicional

requiere_licencia BIT DEFAULT 0,              
-- True = Requiere licencia/pago adicional
-- False = Incluido en plan base

orden INT DEFAULT 0,                          
-- Orden de visualización en UI

es_activo BIT DEFAULT 1,
fecha_creacion DATETIME DEFAULT GETDATE()
);
-- Índices
CREATE INDEX IDX_cliente_modulo_codigo ON cliente_modulo(codigo_modulo);

-- ============================================================================
-- TABLA: cliente_modulo_conexion
-- Propósito: Conexiones de BD específicas por cliente y módulo
-- Permite: Cada cliente puede tener diferentes BDs para cada módulo
-- Caso de uso: Cliente A tiene Planillas en servidor1, Contabilidad en servidor2
-- ============================================================================
CREATE TABLE cliente_modulo_conexion (
conexion_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NOT NULL,
modulo_id INT NOT NULL,

-- ========================================
-- INFORMACIÓN DE CONEXIÓN
-- ========================================
servidor NVARCHAR(255) NOT NULL,              
-- Nombre o IP del servidor de BD
-- Ejemplos: 'CARLOSPC', 'perufashions11', 'sql.azure.com', '192.168.1.100'

puerto INT DEFAULT 1433,                      
-- Puerto de conexión (1433 para SQL Server)

nombre_bd NVARCHAR(100) NOT NULL,             
-- Nombre de la base de datos
-- Ejemplos: 'bdpla_psf_web', 'bdcon2020', 'produccion_2024'

-- ========================================
-- CREDENCIALES (SIEMPRE ENCRIPTADAS)
-- ========================================
usuario_encriptado NVARCHAR(500) NOT NULL,    
-- Usuario de BD encriptado con AES-256
-- NUNCA guardar en texto plano
-- Se encripta/desencripta en la aplicación usando SECRET_KEY

password_encriptado NVARCHAR(500) NOT NULL,   
-- Password de BD encriptado
-- CRÍTICO: Nunca exponer este campo en APIs

connection_string_encriptado NVARCHAR(MAX) NULL,
-- Connection string completo encriptado
-- Se genera automáticamente desde los campos anteriores
-- Formato: "Server=xxx;Database=xxx;User=xxx;Password=xxx;..."

-- ========================================
-- CONFIGURACIÓN AVANZADA
-- ========================================
tipo_bd NVARCHAR(20) DEFAULT 'sqlserver',     
-- Tipo de base de datos: 'sqlserver', 'postgresql', 'mysql', 'oracle'
-- Permite soportar diferentes motores en el futuro

usa_ssl BIT DEFAULT 0,                        
-- Si la conexión usa SSL/TLS

timeout_segundos INT DEFAULT 30,              
-- Timeout de conexión en segundos

max_pool_size INT DEFAULT 100,                
-- Tamaño máximo del connection pool

-- ========================================
-- CONFIGURACIÓN DE ACCESO
-- ========================================
es_solo_lectura BIT DEFAULT 0,                
-- True = Conexión read-only (útil para replicas)

es_conexion_principal BIT DEFAULT 0,          
-- True = Es la conexión principal del módulo
-- Solo puede haber una conexión principal por cliente-módulo

-- ========================================
-- ESTADO Y MONITOREO
-- ========================================
es_activo BIT DEFAULT 1,

ultima_conexion_exitosa DATETIME NULL,        
-- Última vez que se conectó exitosamente
-- Se actualiza automáticamente en cada conexión

ultimo_error NVARCHAR(MAX) NULL,              
-- Último mensaje de error de conexión
-- Para troubleshooting

fecha_ultimo_error DATETIME NULL,

-- ========================================
-- AUDITORÍA
-- ========================================
fecha_creacion DATETIME DEFAULT GETDATE(),
fecha_actualizacion DATETIME NULL,
creado_por_usuario_id INT NULL,               
-- Quién configuró esta conexión

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_conexion_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE,
CONSTRAINT FK_conexion_modulo FOREIGN KEY (modulo_id) 
    REFERENCES cliente_modulo(modulo_id) ON DELETE CASCADE,

-- Solo puede haber una conexión principal por cliente-módulo
CONSTRAINT UQ_conexion_principal UNIQUE (cliente_id, modulo_id, es_conexion_principal)
);
-- Índices optimizados
CREATE INDEX IDX_conexion_cliente_modulo ON cliente_modulo_conexion(cliente_id, modulo_id, es_activo);
CREATE INDEX IDX_conexion_principal ON cliente_modulo_conexion(cliente_id, modulo_id, es_conexion_principal);

-- ============================================================================
-- TABLA: cliente_modulo_activo
-- Propósito: Qué módulos tiene contratado/activo cada cliente
-- Control: Licenciamiento y límites por módulo
-- ============================================================================
CREATE TABLE cliente_modulo_activo (
cliente_modulo_activo_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NOT NULL,
modulo_id INT NOT NULL,

-- ========================================
-- LICENCIAMIENTO
-- ========================================
esta_activo BIT DEFAULT 1,
-- Si el módulo está activo para este cliente

fecha_activacion DATETIME DEFAULT GETDATE(),
-- Cuándo se activó el módulo

fecha_vencimiento DATETIME NULL,              
-- Fecha de vencimiento de la licencia
-- NULL = ilimitado/permanente

-- ========================================
-- CONFIGURACIÓN ESPECÍFICA DEL MÓDULO
-- ========================================
configuracion_json NVARCHAR(MAX) NULL,        
-- JSON con configuraciones custom del módulo para este cliente
-- Ejemplo: {"periodo_fiscal": "01-04", "moneda_base": "PEN"}

-- ========================================
-- LÍMITES (si aplica)
-- ========================================
limite_usuarios INT NULL,                     
-- Máximo de usuarios que pueden usar este módulo
-- NULL = ilimitado

limite_registros INT NULL,                    
-- Límite de registros (ej: empleados en Planillas)
-- NULL = ilimitado

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_modulo_activo_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE,
CONSTRAINT FK_modulo_activo_modulo FOREIGN KEY (modulo_id) 
    REFERENCES cliente_modulo(modulo_id) ON DELETE CASCADE,

-- Un cliente no puede tener el mismo módulo activado dos veces
CONSTRAINT UQ_cliente_modulo UNIQUE (cliente_id, modulo_id)
);
-- Índices
CREATE INDEX IDX_modulo_activo_cliente ON cliente_modulo_activo(cliente_id, esta_activo);

-- ============================================================================
-- TABLA: cliente_auth_config
-- Propósito: Configuración de políticas de autenticación por cliente
-- Permite: Cada cliente define sus propias reglas de seguridad
-- ============================================================================
CREATE TABLE cliente_auth_config (
config_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NOT NULL UNIQUE,
-- Un cliente = una configuración
-- ========================================
-- POLÍTICAS DE CONTRASEÑA
-- ========================================
password_min_length INT DEFAULT 8,
-- Longitud mínima de contraseña

password_require_uppercase BIT DEFAULT 1,
-- Requiere al menos una mayúscula

password_require_lowercase BIT DEFAULT 1,
-- Requiere al menos una minúscula

password_require_number BIT DEFAULT 1,
-- Requiere al menos un número

password_require_special BIT DEFAULT 0,
-- Requiere al menos un carácter especial (!@#$%^&*)

password_expiry_days INT DEFAULT 90,          
-- Días antes de expirar la contraseña (0 = nunca expira)

password_history_count INT DEFAULT 3,         
-- Cuántas contraseñas previas recordar (no permitir reutilizar)

-- ========================================
-- CONTROL DE ACCESO
-- ========================================
max_login_attempts INT DEFAULT 5,
-- Máximo de intentos fallidos antes de bloquear

lockout_duration_minutes INT DEFAULT 30,      
-- Duración del bloqueo en minutos

max_active_sessions INT DEFAULT 3,            
-- Máximo de sesiones simultáneas por usuario (0 = ilimitado)

session_idle_timeout_minutes INT DEFAULT 60,  
-- Minutos de inactividad antes de cerrar sesión (0 = no expira)

-- ========================================
-- TOKENS JWT
-- ========================================
access_token_minutes INT DEFAULT 15,
-- Duración del access token en minutos

refresh_token_days INT DEFAULT 30,
-- Duración del refresh token en días

-- ========================================
-- OPCIONES DE LOGIN
-- ========================================
allow_remember_me BIT DEFAULT 1,
-- Permitir opción "Recordar sesión"

remember_me_days INT DEFAULT 30,              
-- Duración de sesión si marca "recordar" (en días)

require_email_verification BIT DEFAULT 0,
-- Requiere verificar email antes de primer login

allow_password_reset BIT DEFAULT 1,
-- Permitir recuperación de contraseña por email

-- ========================================
-- AUTENTICACIÓN DE DOS FACTORES (2FA)
-- ========================================
enable_2fa BIT DEFAULT 0,
-- Habilitar 2FA para el cliente

require_2fa_for_admins BIT DEFAULT 0,         
-- Forzar 2FA para usuarios con rol admin

metodos_2fa_permitidos NVARCHAR(100) DEFAULT 'email,sms',
-- Métodos permitidos separados por coma: 'email', 'sms', 'totp', 'app'

-- ========================================
-- WHITELIST/BLACKLIST DE IPs (Futuro)
-- ========================================
ip_whitelist_enabled BIT DEFAULT 0,
-- Habilitar whitelist de IPs permitidas

ip_whitelist NVARCHAR(MAX) NULL,              
-- JSON array de IPs permitidas
-- Ejemplo: ["192.168.1.0/24", "10.0.0.1"]

ip_blacklist NVARCHAR(MAX) NULL,              
-- JSON array de IPs bloqueadas

-- ========================================
-- HORARIOS DE ACCESO (Futuro)
-- ========================================
horario_acceso_enabled BIT DEFAULT 0,
-- Habilitar restricción por horarios

horario_acceso_config NVARCHAR(MAX) NULL,     
-- JSON con horarios permitidos
-- Ejemplo: {"lunes": "08:00-18:00", "sabado": "08:00-13:00"}

fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
fecha_actualizacion DATETIME NULL,

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_auth_config_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLA: federacion_identidad
-- Propósito: Configuración de proveedores de identidad externos (SSO)
-- Soporta: Azure AD, Google Workspace, Okta, OIDC genérico, SAML 2.0
-- ============================================================================
CREATE TABLE federacion_identidad (
federacion_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NOT NULL,
-- ========================================
-- IDENTIFICACIÓN
-- ========================================
nombre_configuracion NVARCHAR(100) NOT NULL,  
-- Nombre descriptivo de la configuración
-- Ejemplos: 'Azure AD Empresa', 'Google Workspace', 'Okta Producción'

proveedor NVARCHAR(30) NOT NULL,              
-- Tipo de proveedor: 'azure_ad', 'google', 'okta', 'oidc', 'saml'

-- ========================================
-- CONFIGURACIÓN OAuth 2.0 / OpenID Connect
-- ========================================
client_id NVARCHAR(255) NULL,
-- Client ID del proveedor (Azure AD, Google, etc.)

client_secret_encrypted NVARCHAR(500) NULL,   
-- Client Secret ENCRIPTADO (nunca en texto plano)

authority_url NVARCHAR(500) NULL,             
-- URL del proveedor de autenticación
-- Ejemplo Azure AD: 'https://login.microsoftonline.com/{tenant-id}'
-- Ejemplo Google: 'https://accounts.google.com'

token_endpoint NVARCHAR(500) NULL,
-- Endpoint para obtener tokens

authorization_endpoint NVARCHAR(500) NULL,
-- Endpoint de autorización

userinfo_endpoint NVARCHAR(500) NULL,
-- Endpoint para obtener info del usuario

redirect_uri NVARCHAR(500) NULL,              
-- URL de callback después de autenticación
-- Ejemplo: 'https://acme.tuapp.com/auth/callback'

scope NVARCHAR(200) DEFAULT 'openid profile email',
-- Scopes solicitados al proveedor

-- ========================================
-- CONFIGURACIÓN SAML 2.0
-- ========================================
entity_id NVARCHAR(500) NULL,                 
-- Entity ID del Service Provider (nuestra app)

sso_url NVARCHAR(500) NULL,                   
-- Single Sign-On URL del Identity Provider

slo_url NVARCHAR(500) NULL,                   
-- Single Logout URL

certificate_x509 NVARCHAR(MAX) NULL,          
-- Certificado público X.509 del IdP
-- Para validar firmas SAML

-- ========================================
-- MAPEO DE ATRIBUTOS
-- ========================================
attribute_mapping NVARCHAR(MAX) NULL,         
-- JSON con mapeo de atributos externos → campos locales
-- Ejemplo: {
--   "email": "mail",
--   "nombre": "givenName",
--   "apellido": "surname",
--   "dni": "employeeId"
-- }

-- ========================================
-- CONFIGURACIÓN DE COMPORTAMIENTO
-- ========================================
es_activo BIT DEFAULT 1 NOT NULL,

es_metodo_principal BIT DEFAULT 0,            
-- Si es el método de login por defecto (mostrar botón principal)

auto_provision_users BIT DEFAULT 1,           
-- Crear usuarios automáticamente en primer login SSO
-- Si false, el usuario debe existir previamente

sync_user_data BIT DEFAULT 1,                 
-- Sincronizar datos del usuario en cada login SSO
-- Actualiza nombre, email, etc. desde el proveedor

-- ========================================
-- AUDITORÍA
-- ========================================
fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
fecha_actualizacion DATETIME NULL,
ultimo_login_sso DATETIME NULL,               
-- Última vez que alguien se autenticó con este proveedor

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_federacion_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE
);
-- Índices
CREATE INDEX IDX_federacion_cliente ON federacion_identidad(cliente_id, es_activo);
CREATE INDEX IDX_federacion_proveedor ON federacion_identidad(proveedor);

-- ============================================================================
-- TABLA: log_sincronizacion_usuario
-- Propósito: Auditoría de sincronización de usuarios entre instalaciones
-- Caso de uso: Cliente con instalación local sincroniza con servidor central
-- ============================================================================
CREATE TABLE log_sincronizacion_usuario (
log_id INT PRIMARY KEY IDENTITY(1,1),
-- ========================================
-- CONTEXTO DE LA SINCRONIZACIÓN
-- ========================================
cliente_origen_id INT NULL,                   
-- De dónde viene la sincronización

cliente_destino_id INT NULL,                  
-- Hacia dónde va la sincronización

usuario_id INT NOT NULL,                      
-- Usuario que se sincronizó

-- ========================================
-- DETALLES DE LA OPERACIÓN
-- ========================================
tipo_sincronizacion NVARCHAR(20) NOT NULL,    
-- Tipo: 'manual', 'push_auto', 'pull_auto', 'scheduled'

direccion NVARCHAR(10) NOT NULL,              
-- Dirección: 'push', 'pull', 'bidireccional'

operacion NVARCHAR(20) NOT NULL,              
-- Operación realizada: 'create', 'update', 'delete'

-- ========================================
-- RESULTADO
-- ========================================
estado NVARCHAR(20) NOT NULL,                 
-- Estado: 'exitoso', 'fallido', 'parcial', 'pendiente'

mensaje_error NVARCHAR(MAX) NULL,
-- Mensaje de error si falló

-- ========================================
-- DATOS DE LA SINCRONIZACIÓN
-- ========================================
campos_sincronizados NVARCHAR(MAX) NULL,      
-- JSON array con los campos que se actualizaron
-- Ejemplo: ["nombre", "correo", "es_activo"]

cambios_detectados NVARCHAR(MAX) NULL,        
-- JSON con diff de cambios (antes/después)
-- Ejemplo: {"nombre": {"antes": "Juan", "despues": "Juan Carlos"}}

hash_antes NVARCHAR(64) NULL,                 
-- Hash SHA-256 de datos antes de la sincronización

hash_despues NVARCHAR(64) NULL,               
-- Hash SHA-256 de datos después

-- ========================================
-- AUDITORÍA
-- ========================================
fecha_sincronizacion DATETIME DEFAULT GETDATE() NOT NULL,

usuario_ejecutor_id INT NULL,                 
-- Quién ejecutó la sincronización (NULL = automático)

duracion_ms INT NULL,                         
-- Tiempo que tomó la operación en milisegundos

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_log_sync_usuario FOREIGN KEY (usuario_id) 
    REFERENCES usuario(usuario_id) ON DELETE CASCADE,
CONSTRAINT FK_log_sync_cliente_origen FOREIGN KEY (cliente_origen_id) 
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION,
CONSTRAINT FK_log_sync_cliente_destino FOREIGN KEY (cliente_destino_id) 
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION
);
-- Índices para queries de auditoría
CREATE INDEX IDX_log_sync_usuario ON log_sincronizacion_usuario(usuario_id, fecha_sincronizacion DESC);
CREATE INDEX IDX_log_sync_origen ON log_sincronizacion_usuario(cliente_origen_id, estado);
CREATE INDEX IDX_log_sync_destino ON log_sincronizacion_usuario(cliente_destino_id, estado);
CREATE INDEX IDX_log_sync_fecha ON log_sincronizacion_usuario(fecha_sincronizacion DESC);

-- ============================================================================
-- TABLA: auth_audit_log
-- Propósito: Log completo de eventos de autenticación y seguridad
-- Uso: Auditoría, detección de intrusiones, compliance, troubleshooting
-- ============================================================================
CREATE TABLE auth_audit_log (
log_id INT PRIMARY KEY IDENTITY(1,1),
cliente_id INT NOT NULL,
usuario_id INT NULL,                          
-- NULL si el evento es anónimo o login falló

-- ========================================
-- EVENTO
-- ========================================
evento NVARCHAR(50) NOT NULL,
/* Eventos comunes:
   Login:
   - 'login_success', 'login_failed', 'login_blocked'
   - 'sso_login_success', 'sso_login_failed'
   
   Logout:
   - 'logout', 'logout_forced', 'logout_timeout'
   
   Tokens:
   - 'token_refresh', 'token_revoked', 'token_expired'
   
   Contraseña:
   - 'password_change', 'password_reset_request', 'password_reset_complete'
   
   Cuenta:
   - 'account_locked', 'account_unlocked', 'account_activated', 'account_deactivated'
   
   Seguridad:
   - 'email_verified', '2fa_enabled', '2fa_disabled', '2fa_verified', '2fa_failed'
   - 'suspicious_activity', 'ip_blocked'
*/

nombre_usuario_intento NVARCHAR(100) NULL,    
-- Para logins fallidos, guardar el nombre de usuario intentado

-- ========================================
-- DETALLES
-- ========================================
descripcion NVARCHAR(500) NULL,
-- Descripción detallada del evento

exito BIT NOT NULL,
-- Si el evento fue exitoso o falló

codigo_error NVARCHAR(50) NULL,               
-- Código de error si aplica (ej: 'INVALID_PASSWORD', 'ACCOUNT_LOCKED')

-- ========================================
-- CONTEXTO TÉCNICO
-- ========================================
ip_address VARCHAR(45) NULL,                  
-- IP desde donde se originó el evento

user_agent VARCHAR(500) NULL,                 
-- User agent del navegador/app

device_info NVARCHAR(200) NULL,
-- Información del dispositivo

geolocation NVARCHAR(100) NULL,               
-- País, ciudad si se implementa geolocalización
-- Ejemplo: 'Lima, Peru'

-- ========================================
-- METADATA ADICIONAL
-- ========================================
metadata_json NVARCHAR(MAX) NULL,             
-- JSON con datos adicionales del evento
-- Ejemplo: {"session_duration": 3600, "pages_visited": 15}

fecha_evento DATETIME DEFAULT GETDATE() NOT NULL,

-- ========================================
-- CONSTRAINTS
-- ========================================
CONSTRAINT FK_audit_cliente FOREIGN KEY (cliente_id) 
    REFERENCES cliente(cliente_id) ON DELETE CASCADE,
CONSTRAINT FK_audit_usuario FOREIGN KEY (usuario_id) 
    REFERENCES usuario(usuario_id) ON DELETE SET NULL
);
-- Índices optimizados para queries de auditoría y reporting
CREATE INDEX IDX_audit_cliente_fecha ON auth_audit_log(cliente_id, fecha_evento DESC);
CREATE INDEX IDX_audit_usuario_fecha ON auth_audit_log(usuario_id, fecha_evento DESC)
WHERE usuario_id IS NOT NULL;
CREATE INDEX IDX_audit_evento ON auth_audit_log(evento, fecha_evento DESC);
CREATE INDEX IDX_audit_exito ON auth_audit_log(exito, fecha_evento DESC);
CREATE INDEX IDX_audit_ip ON auth_audit_log(ip_address, fecha_evento DESC)
WHERE ip_address IS NOT NULL;