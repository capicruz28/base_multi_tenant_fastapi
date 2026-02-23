# app/infrastructure/database/tables_erp/tables_org.py
"""
Tablas SQLAlchemy Core para el módulo ORG (Organización).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección ORG.
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date,
    ForeignKey, Text, Index, UniqueConstraint, Numeric, MetaData
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

# Metadata ERP (independiente de central para uso en BD dedicada)
metadata_erp = MetaData()

# ============================================================================
# TABLA: org_empresa
# ============================================================================
OrgEmpresaTable = Table(
    "org_empresa",
    metadata_erp,
    Column("empresa_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),  # Sin FK: BD dedicada no tiene cliente
    Column("codigo_empresa", String(20), nullable=False),
    Column("razon_social", String(200), nullable=False),
    Column("nombre_comercial", String(150), nullable=True),
    Column("ruc", String(11), nullable=False),
    Column("tipo_documento_tributario", String(10), nullable=True, server_default="RUC"),
    Column("actividad_economica", String(200), nullable=True),
    Column("codigo_ciiu", String(10), nullable=True),
    Column("rubro", String(50), nullable=True),
    Column("tipo_empresa", String(30), nullable=True),
    Column("direccion_fiscal", String(255), nullable=True),
    Column("pais", String(50), nullable=True, server_default="Perú"),
    Column("departamento", String(50), nullable=True),
    Column("provincia", String(50), nullable=True),
    Column("distrito", String(50), nullable=True),
    Column("codigo_postal", String(10), nullable=True),
    Column("ubigeo", String(6), nullable=True),
    Column("telefono_principal", String(20), nullable=True),
    Column("telefono_secundario", String(20), nullable=True),
    Column("email_principal", String(100), nullable=True),
    Column("email_facturacion", String(100), nullable=True),
    Column("sitio_web", String(255), nullable=True),
    Column("representante_legal_nombre", String(150), nullable=True),
    Column("representante_legal_dni", String(20), nullable=True),
    Column("representante_legal_cargo", String(50), nullable=True),
    Column("moneda_base", String(3), nullable=True, server_default="PEN"),
    Column("zona_horaria", String(50), nullable=True, server_default="America/Lima"),
    Column("idioma_sistema", String(5), nullable=True, server_default="es-PE"),
    Column("formato_fecha", String(20), nullable=True, server_default="dd/MM/yyyy"),
    Column("separador_miles", String(1), nullable=True, server_default=","),
    Column("separador_decimales", String(1), nullable=True, server_default="."),
    Column("decimales_moneda", Integer, nullable=True, server_default="2"),  # SQL Server: string for default
    Column("logo_url", String(500), nullable=True),
    Column("logo_secundario_url", String(500), nullable=True),
    Column("favicon_url", String(500), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_constitucion", Date, nullable=True),
    Column("fecha_inicio_operaciones", Date, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_actualizacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "codigo_empresa", name="UQ_org_empresa_cliente"),
    UniqueConstraint("cliente_id", "ruc", name="UQ_org_empresa_ruc"),
)
Index("IDX_org_empresa_cliente", OrgEmpresaTable.c.cliente_id, OrgEmpresaTable.c.es_activo)
Index("IDX_org_empresa_ruc", OrgEmpresaTable.c.ruc)

# ============================================================================
# TABLA: org_centro_costo
# ============================================================================
OrgCentroCostoTable = Table(
    "org_centro_costo",
    metadata_erp,
    Column("centro_costo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("centro_costo_padre_id", UNIQUEIDENTIFIER, nullable=True),
    Column("nivel", Integer, nullable=True, server_default="1"),
    Column("ruta_jerarquica", String(500), nullable=True),
    Column("tipo_centro_costo", String(30), nullable=False),
    Column("categoria", String(50), nullable=True),
    Column("tiene_presupuesto", Boolean, nullable=True, server_default="0"),
    Column("permite_imputacion_directa", Boolean, nullable=True, server_default="1"),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("responsable_nombre", String(150), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_inicio_vigencia", Date, nullable=True),
    Column("fecha_fin_vigencia", Date, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_cc_codigo"),
)
Index("IDX_cc_empresa", OrgCentroCostoTable.c.empresa_id, OrgCentroCostoTable.c.es_activo)
Index("IDX_cc_padre", OrgCentroCostoTable.c.centro_costo_padre_id)

# ============================================================================
# TABLA: org_sucursal
# ============================================================================
OrgSucursalTable = Table(
    "org_sucursal",
    metadata_erp,
    Column("sucursal_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("tipo_sucursal", String(30), nullable=True, server_default="sede"),
    Column("direccion", String(255), nullable=True),
    Column("referencia", String(255), nullable=True),
    Column("pais", String(50), nullable=True, server_default="Perú"),
    Column("departamento", String(50), nullable=True),
    Column("provincia", String(50), nullable=True),
    Column("distrito", String(50), nullable=True),
    Column("ubigeo", String(6), nullable=True),
    Column("codigo_postal", String(10), nullable=True),
    Column("latitud", Numeric(10, 8), nullable=True),
    Column("longitud", Numeric(11, 8), nullable=True),
    Column("telefono", String(20), nullable=True),
    Column("email", String(100), nullable=True),
    Column("es_casa_matriz", Boolean, nullable=True, server_default="0"),
    Column("es_punto_venta", Boolean, nullable=True, server_default="0"),
    Column("es_almacen", Boolean, nullable=True, server_default="0"),
    Column("es_planta_produccion", Boolean, nullable=True, server_default="0"),
    Column("horario_atencion", Text, nullable=True),
    Column("zona_horaria", String(50), nullable=True),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("responsable_nombre", String(150), nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_apertura", Date, nullable=True),
    Column("fecha_cierre", Date, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_sucursal_codigo"),
)
Index("IDX_sucursal_empresa", OrgSucursalTable.c.empresa_id, OrgSucursalTable.c.es_activo)

# ============================================================================
# TABLA: org_departamento
# ============================================================================
OrgDepartamentoTable = Table(
    "org_departamento",
    metadata_erp,
    Column("departamento_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("departamento_padre_id", UNIQUEIDENTIFIER, nullable=True),
    Column("nivel", Integer, nullable=True, server_default="1"),
    Column("ruta_jerarquica", String(500), nullable=True),
    Column("tipo_departamento", String(30), nullable=True),
    Column("jefe_departamento_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("jefe_nombre", String(150), nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, nullable=True),
    Column("sucursal_id", UNIQUEIDENTIFIER, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_dpto_codigo"),
)
Index("IDX_dpto_empresa", OrgDepartamentoTable.c.empresa_id, OrgDepartamentoTable.c.es_activo)

# ============================================================================
# TABLA: org_cargo
# ============================================================================
OrgCargoTable = Table(
    "org_cargo",
    metadata_erp,
    Column("cargo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("nivel_jerarquico", Integer, nullable=True, server_default="1"),
    Column("categoria", String(30), nullable=True),
    Column("area_funcional", String(50), nullable=True),
    Column("departamento_id", UNIQUEIDENTIFIER, nullable=True),
    Column("cargo_jefe_id", UNIQUEIDENTIFIER, nullable=True),
    Column("rango_salarial_min", Numeric(12, 2), nullable=True),
    Column("rango_salarial_max", Numeric(12, 2), nullable=True),
    Column("moneda_salarial", String(3), nullable=True, server_default="PEN"),
    Column("nivel_educacion_minimo", String(50), nullable=True),
    Column("experiencia_minima_meses", Integer, nullable=True),
    Column("requisitos_especificos", Text, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_cargo_codigo"),
)
Index("IDX_cargo_empresa", OrgCargoTable.c.empresa_id, OrgCargoTable.c.es_activo)

# ============================================================================
# TABLA: org_parametro_sistema
# ============================================================================
OrgParametroSistemaTable = Table(
    "org_parametro_sistema",
    metadata_erp,
    Column("parametro_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, nullable=True),
    Column("modulo_codigo", String(10), nullable=False),
    Column("codigo_parametro", String(50), nullable=False),
    Column("nombre_parametro", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("tipo_dato", String(20), nullable=False),
    Column("valor_texto", Text, nullable=True),
    Column("valor_numerico", Numeric(18, 4), nullable=True),
    Column("valor_booleano", Boolean, nullable=True),
    Column("valor_fecha", Date, nullable=True),
    Column("valor_json", Text, nullable=True),
    Column("valor_defecto", String(500), nullable=True),
    Column("es_editable", Boolean, nullable=True, server_default="1"),
    Column("es_obligatorio", Boolean, nullable=True, server_default="0"),
    Column("opciones_validas", Text, nullable=True),
    Column("expresion_validacion", String(500), nullable=True),
    Column("mensaje_validacion", String(255), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_actualizacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "modulo_codigo", "codigo_parametro", name="UQ_parametro"),
)
Index("IDX_parametro_modulo", OrgParametroSistemaTable.c.modulo_codigo, OrgParametroSistemaTable.c.codigo_parametro)
