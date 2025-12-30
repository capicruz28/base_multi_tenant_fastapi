# app/infrastructure/database/tables_modulos.py
"""
Definiciones de tablas para el sistema de módulos y menús usando SQLAlchemy Core.

✅ REFACTORIZACIÓN: Sistema de Módulos y Menús
- Tablas nuevas para la arquitectura refactorizada
- Reemplaza tablas antiguas: cliente_modulo → modulo, area_menu → modulo_seccion, menu → modulo_menu
- Nueva tabla: modulo_rol_plantilla

USO:
    from app.infrastructure.database.tables_modulos import ModuloTable, ModuloSeccionTable
    from sqlalchemy import select
    
    query = select(ModuloTable).where(ModuloTable.c.es_activo == True)
    result = await execute_query(query)
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Text, Index, UniqueConstraint,
    MetaData, Numeric
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

# Metadata para todas las tablas (compartida con tables.py)
from app.infrastructure.database.tables import metadata

# ============================================================================
# TABLA: modulo
# Propósito: Catálogo maestro de módulos ERP disponibles en el sistema
# Alcance: GLOBAL (no por cliente)
# ============================================================================
ModuloTable = Table(
    'modulo',
    metadata,
    Column('modulo_id', UNIQUEIDENTIFIER, primary_key=True),
    
    # Identificación
    Column('codigo', String(30), nullable=False, unique=True),
    Column('nombre', String(100), nullable=False),
    Column('descripcion', String(500), nullable=True),
    Column('icono', String(50), nullable=True),
    Column('color', String(7), nullable=True, server_default='#1976D2'),
    
    # Clasificación y licenciamiento
    Column('categoria', String(30), nullable=True, server_default='operaciones'),
    Column('es_core', Boolean, nullable=True, server_default='0'),
    Column('requiere_licencia', Boolean, nullable=True, server_default='1'),
    Column('precio_mensual', Numeric(10, 2), nullable=True),
    
    # Dependencias entre módulos
    Column('modulos_requeridos', Text, nullable=True),  # JSON array
    
    # Control y orden
    Column('orden', Integer, nullable=True, server_default='0'),
    Column('es_activo', Boolean, nullable=True, server_default='1'),
    Column('fecha_creacion', DateTime, nullable=True, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    
    # Metadata extensible
    Column('configuracion_defecto', Text, nullable=True),  # JSON
    
    # Índices
    Index('IDX_modulo_codigo', 'codigo'),
    Index('IDX_modulo_activo', 'es_activo', 'orden'),
    Index('IDX_modulo_categoria', 'categoria', 'orden'),
)

# ============================================================================
# TABLA: cliente_modulo
# Propósito: Módulos contratados/activos por cada cliente (tenant)
# Relación: cliente 1:N cliente_modulo, modulo 1:N cliente_modulo
# ============================================================================
ClienteModuloTable = Table(
    'cliente_modulo',
    metadata,
    Column('cliente_modulo_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=False),
    Column('modulo_id', UNIQUEIDENTIFIER, ForeignKey('modulo.modulo_id', ondelete='CASCADE'), nullable=False),
    
    # Estado y licenciamiento
    Column('esta_activo', Boolean, nullable=True, server_default='1'),
    Column('fecha_activacion', DateTime, nullable=True, server_default=func.getdate()),
    Column('fecha_vencimiento', DateTime, nullable=True),
    Column('modo_prueba', Boolean, nullable=True, server_default='0'),
    Column('fecha_fin_prueba', DateTime, nullable=True),
    
    # Configuración específica del cliente
    Column('configuracion_json', Text, nullable=True),  # JSON
    
    # Límites y cuotas
    Column('limite_usuarios', Integer, nullable=True),
    Column('limite_registros', Integer, nullable=True),
    Column('limite_transacciones_mes', Integer, nullable=True),
    
    # Auditoría
    Column('fecha_creacion', DateTime, nullable=True, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    Column('activado_por_usuario_id', UNIQUEIDENTIFIER, nullable=True),
    
    # Constraints
    UniqueConstraint('cliente_id', 'modulo_id', name='UQ_cliente_modulo'),
    
    # Índices
    Index('IDX_cliente_modulo_cliente', 'cliente_id', 'esta_activo'),
    Index('IDX_cliente_modulo_vencimiento', 'fecha_vencimiento'),
)

# ============================================================================
# TABLA: modulo_seccion
# Propósito: Secciones/Áreas dentro de un módulo (reemplaza area_menu)
# Ejemplo: Módulo LOGISTICA tiene secciones: "Rutas", "Vehículos", "Conductores"
# Alcance: GLOBAL (definido por el proveedor SaaS)
# ============================================================================
ModuloSeccionTable = Table(
    'modulo_seccion',
    metadata,
    Column('seccion_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('modulo_id', UNIQUEIDENTIFIER, ForeignKey('modulo.modulo_id', ondelete='CASCADE'), nullable=False),
    
    # Identificación
    Column('codigo', String(30), nullable=False),
    Column('nombre', String(100), nullable=False),
    Column('descripcion', String(255), nullable=True),
    Column('icono', String(50), nullable=True),
    
    # Organización
    Column('orden', Integer, nullable=True, server_default='0'),
    Column('es_seccion_sistema', Boolean, nullable=True, server_default='1'),
    Column('es_activo', Boolean, nullable=True, server_default='1'),
    Column('fecha_creacion', DateTime, nullable=True, server_default=func.getdate()),
    
    # Constraints
    UniqueConstraint('modulo_id', 'codigo', name='UQ_seccion_modulo_codigo'),
    
    # Índices
    Index('IDX_seccion_modulo', 'modulo_id', 'es_activo', 'orden'),
)

# ============================================================================
# TABLA: modulo_menu
# Propósito: Opciones de menú/pantallas de cada módulo (reemplaza tabla menu)
# Jerarquía: Soporta submenús mediante menu_padre_id
# Alcance: GLOBAL + Personalizable por cliente
# ============================================================================
ModuloMenuTable = Table(
    'modulo_menu',
    metadata,
    Column('menu_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('modulo_id', UNIQUEIDENTIFIER, ForeignKey('modulo.modulo_id', ondelete='CASCADE'), nullable=False),
    Column('seccion_id', UNIQUEIDENTIFIER, ForeignKey('modulo_seccion.seccion_id', ondelete='NO ACTION'), nullable=True),
    Column('cliente_id', UNIQUEIDENTIFIER, ForeignKey('cliente.cliente_id', ondelete='CASCADE'), nullable=True),
    
    # Identificación
    Column('codigo', String(50), nullable=True),
    Column('nombre', String(100), nullable=False),
    Column('descripcion', String(255), nullable=True),
    Column('icono', String(50), nullable=True),
    Column('ruta', String(255), nullable=True),
    
    # Jerarquía (Submenús)
    Column('menu_padre_id', UNIQUEIDENTIFIER, ForeignKey('modulo_menu.menu_id', ondelete='NO ACTION'), nullable=True),
    Column('nivel', Integer, nullable=True, server_default='1'),
    
    # Configuración
    Column('tipo_menu', String(20), nullable=True, server_default='pantalla'),
    Column('orden', Integer, nullable=True, server_default='0'),
    Column('requiere_autenticacion', Boolean, nullable=True, server_default='1'),
    Column('es_visible', Boolean, nullable=True, server_default='1'),
    Column('es_menu_sistema', Boolean, nullable=True, server_default='1'),
    Column('es_activo', Boolean, nullable=True, server_default='1'),
    Column('fecha_creacion', DateTime, nullable=True, server_default=func.getdate()),
    Column('fecha_actualizacion', DateTime, nullable=True),
    
    # Metadata
    Column('configuracion_json', Text, nullable=True),  # JSON
    
    # Índices
    Index('IDX_menu_modulo', 'modulo_id', 'es_activo', 'orden'),
    Index('IDX_menu_seccion', 'seccion_id', 'orden'),
    Index('IDX_menu_padre', 'menu_padre_id', 'orden'),
    Index('IDX_menu_cliente', 'cliente_id', 'es_activo'),
    Index('IDX_menu_ruta', 'ruta'),
)

# ============================================================================
# TABLA: modulo_rol_plantilla
# Propósito: Plantillas de roles predefinidos al activar un módulo
# Uso: Crear roles automáticamente cuando cliente activa un módulo
# ============================================================================
ModuloRolPlantillaTable = Table(
    'modulo_rol_plantilla',
    metadata,
    Column('plantilla_id', UNIQUEIDENTIFIER, primary_key=True),
    Column('modulo_id', UNIQUEIDENTIFIER, ForeignKey('modulo.modulo_id', ondelete='CASCADE'), nullable=False),
    
    # Definición del rol
    Column('nombre_rol', String(50), nullable=False),
    Column('descripcion', String(255), nullable=True),
    Column('nivel_acceso', Integer, nullable=True, server_default='1'),
    
    # Permisos por defecto
    Column('permisos_json', Text, nullable=True),  # JSON
    
    # Control
    Column('es_activo', Boolean, nullable=True, server_default='1'),
    Column('orden', Integer, nullable=True, server_default='0'),
    Column('fecha_creacion', DateTime, nullable=True, server_default=func.getdate()),
    
    # Índices
    Index('IDX_plantilla_modulo', 'modulo_id', 'es_activo', 'orden'),
)

# ============================================================================
# EXPORTAR TODAS LAS TABLAS
# ============================================================================
__all__ = [
    'ModuloTable',
    'ClienteModuloTable',
    'ModuloSeccionTable',
    'ModuloMenuTable',
    'ModuloRolPlantillaTable',
]

