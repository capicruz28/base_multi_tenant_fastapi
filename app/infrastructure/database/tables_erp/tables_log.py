# app/infrastructure/database/tables_erp/tables_log.py
"""
Tablas SQLAlchemy Core para el módulo LOG (Logística y Distribución).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección LOG.
✅ Campos esenciales incluidos desde el inicio.
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date, Time,
    ForeignKey, Text, Index, UniqueConstraint, Numeric, MetaData
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

# Usar la misma metadata_erp que tables_org
from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: log_transportista
# ============================================================================
LogTransportistaTable = Table(
    "log_transportista",
    metadata_erp,
    Column("transportista_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_transportista", String(20), nullable=False),
    Column("razon_social", String(200), nullable=False),
    Column("nombre_comercial", String(150), nullable=True),
    Column("tipo_documento", String(10), nullable=True, server_default="RUC"),
    Column("numero_documento", String(20), nullable=False),
    Column("numero_mtc", String(30), nullable=True),
    Column("licencia_tipo", String(50), nullable=True),
    Column("telefono", String(20), nullable=True),
    Column("email", String(100), nullable=True),
    Column("direccion", String(255), nullable=True),
    Column("tarifa_km", Numeric(10, 2), nullable=True),
    Column("tarifa_hora", Numeric(10, 2), nullable=True),
    Column("moneda_tarifa", String(3), nullable=True, server_default="PEN"),
    Column("calificacion", Numeric(3, 2), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_transportista", name="UQ_transp_codigo"),
)
Index("IDX_transp_empresa", LogTransportistaTable.c.empresa_id, LogTransportistaTable.c.es_activo)

# ============================================================================
# TABLA: log_vehiculo
# ============================================================================
LogVehiculoTable = Table(
    "log_vehiculo",
    metadata_erp,
    Column("vehiculo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("placa", String(15), nullable=False),
    Column("marca", String(50), nullable=True),
    Column("modelo", String(50), nullable=True),
    Column("año", Integer, nullable=True),
    Column("color", String(30), nullable=True),
    Column("tipo_vehiculo", String(30), nullable=False),
    Column("categoria_vehiculo", String(20), nullable=True),
    Column("capacidad_kg", Numeric(12, 2), nullable=True),
    Column("capacidad_m3", Numeric(12, 2), nullable=True),
    Column("tipo_propiedad", String(20), nullable=False),
    Column("transportista_id", UNIQUEIDENTIFIER, ForeignKey("log_transportista.transportista_id", ondelete="SET NULL"), nullable=True),
    Column("conductor_nombre", String(150), nullable=True),
    Column("conductor_licencia", String(20), nullable=True),
    Column("conductor_telefono", String(20), nullable=True),
    Column("tarjeta_propiedad", String(30), nullable=True),
    Column("soat_numero", String(30), nullable=True),
    Column("soat_vencimiento", Date, nullable=True),
    Column("revision_tecnica_vencimiento", Date, nullable=True),
    Column("tiene_gps", Boolean, nullable=True, server_default="0"),
    Column("codigo_gps", String(50), nullable=True),
    Column("estado_vehiculo", String(20), nullable=True, server_default="disponible"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "placa", name="UQ_vehiculo_placa"),
)
Index("IDX_vehiculo_empresa", LogVehiculoTable.c.empresa_id, LogVehiculoTable.c.es_activo)
Index("IDX_vehiculo_estado", LogVehiculoTable.c.estado_vehiculo)
Index("IDX_vehiculo_transp", LogVehiculoTable.c.transportista_id)

# ============================================================================
# TABLA: log_ruta
# ============================================================================
LogRutaTable = Table(
    "log_ruta",
    metadata_erp,
    Column("ruta_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_ruta", String(20), nullable=False),
    Column("nombre_ruta", String(100), nullable=False),
    Column("origen_sucursal_id", UNIQUEIDENTIFIER, ForeignKey("org_sucursal.sucursal_id", ondelete="SET NULL"), nullable=True),
    Column("origen_descripcion", String(255), nullable=True),
    Column("destino_descripcion", String(255), nullable=True),
    Column("departamento_origen", String(50), nullable=True),
    Column("departamento_destino", String(50), nullable=True),
    Column("distancia_km", Numeric(10, 2), nullable=True),
    Column("tiempo_estimado_horas", Numeric(5, 2), nullable=True),
    Column("tipo_carretera", String(30), nullable=True),
    Column("costo_estimado", Numeric(12, 2), nullable=True),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("cantidad_peajes", Integer, nullable=True, server_default="0"),
    Column("costo_peajes", Numeric(10, 2), nullable=True, server_default="0"),
    Column("puntos_intermedios", Text, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_ruta", name="UQ_ruta_codigo"),
)
Index("IDX_ruta_empresa", LogRutaTable.c.empresa_id, LogRutaTable.c.es_activo)

# ============================================================================
# TABLA: log_guia_remision
# ============================================================================
LogGuiaRemisionTable = Table(
    "log_guia_remision",
    metadata_erp,
    Column("guia_remision_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("serie", String(4), nullable=False),
    Column("numero", String(10), nullable=False),
    Column("fecha_emision", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_traslado", Date, nullable=False),
    Column("tipo_guia", String(30), nullable=False),
    Column("motivo_traslado", String(30), nullable=False),
    Column("remitente_razon_social", String(200), nullable=False),
    Column("remitente_ruc", String(11), nullable=False),
    Column("remitente_direccion", String(255), nullable=True),
    Column("destinatario_razon_social", String(200), nullable=False),
    Column("destinatario_documento_tipo", String(10), nullable=True),
    Column("destinatario_documento_numero", String(20), nullable=True),
    Column("destinatario_direccion", String(255), nullable=True),
    Column("punto_partida", String(255), nullable=False),
    Column("punto_partida_ubigeo", String(6), nullable=True),
    Column("punto_llegada", String(255), nullable=False),
    Column("punto_llegada_ubigeo", String(6), nullable=True),
    Column("modalidad_transporte", String(20), nullable=False),
    Column("transportista_id", UNIQUEIDENTIFIER, ForeignKey("log_transportista.transportista_id", ondelete="SET NULL"), nullable=True),
    Column("transportista_razon_social", String(200), nullable=True),
    Column("transportista_ruc", String(11), nullable=True),
    Column("vehiculo_id", UNIQUEIDENTIFIER, ForeignKey("log_vehiculo.vehiculo_id", ondelete="SET NULL"), nullable=True),
    Column("vehiculo_placa", String(15), nullable=True),
    Column("conductor_nombre", String(150), nullable=True),
    Column("conductor_documento_tipo", String(10), nullable=True),
    Column("conductor_documento_numero", String(20), nullable=True),
    Column("conductor_licencia", String(20), nullable=True),
    Column("total_bultos", Integer, nullable=True, server_default="0"),
    Column("peso_total_kg", Numeric(12, 2), nullable=True, server_default="0"),
    Column("documento_sustento_tipo", String(20), nullable=True),
    Column("documento_sustento_serie", String(4), nullable=True),
    Column("documento_sustento_numero", String(10), nullable=True),
    Column("movimiento_inventario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("venta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("estado", String(20), nullable=True, server_default="emitida"),
    Column("fecha_entrega", DateTime, nullable=True),
    Column("codigo_hash", String(100), nullable=True),
    Column("codigo_qr", Text, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_anulacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "serie", "numero", name="UQ_guia_numero"),
)
Index("IDX_guia_empresa", LogGuiaRemisionTable.c.empresa_id, LogGuiaRemisionTable.c.fecha_emision.desc())
Index("IDX_guia_estado", LogGuiaRemisionTable.c.estado)

# ============================================================================
# TABLA: log_guia_remision_detalle
# ============================================================================
LogGuiaRemisionDetalleTable = Table(
    "log_guia_remision_detalle",
    metadata_erp,
    Column("guia_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("guia_remision_id", UNIQUEIDENTIFIER, ForeignKey("log_guia_remision.guia_remision_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("peso_kg", Numeric(12, 2), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_guiadet_guia", LogGuiaRemisionDetalleTable.c.guia_remision_id)

# ============================================================================
# TABLA: log_despacho
# ============================================================================
LogDespachoTable = Table(
    "log_despacho",
    metadata_erp,
    Column("despacho_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_despacho", String(20), nullable=False),
    Column("fecha_programada", Date, nullable=False),
    Column("hora_salida_programada", Time, nullable=True),
    Column("ruta_id", UNIQUEIDENTIFIER, ForeignKey("log_ruta.ruta_id", ondelete="SET NULL"), nullable=True),
    Column("origen_sucursal_id", UNIQUEIDENTIFIER, ForeignKey("org_sucursal.sucursal_id", ondelete="SET NULL"), nullable=True),
    Column("vehiculo_id", UNIQUEIDENTIFIER, ForeignKey("log_vehiculo.vehiculo_id", ondelete="SET NULL"), nullable=True),
    Column("conductor_nombre", String(150), nullable=True),
    Column("conductor_telefono", String(20), nullable=True),
    Column("fecha_salida_real", DateTime, nullable=True),
    Column("fecha_retorno", DateTime, nullable=True),
    Column("km_inicial", Numeric(10, 2), nullable=True),
    Column("km_final", Numeric(10, 2), nullable=True),
    Column("total_guias", Integer, nullable=True, server_default="0"),
    Column("total_peso_kg", Numeric(12, 2), nullable=True, server_default="0"),
    Column("total_bultos", Integer, nullable=True, server_default="0"),
    Column("costo_combustible", Numeric(12, 2), nullable=True),
    Column("costo_peajes", Numeric(12, 2), nullable=True),
    Column("otros_gastos", Numeric(12, 2), nullable=True),
    Column("estado", String(20), nullable=True, server_default="planificado"),
    Column("observaciones", Text, nullable=True),
    Column("incidencias", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_despacho", name="UQ_desp_numero"),
)
Index("IDX_desp_empresa", LogDespachoTable.c.empresa_id, LogDespachoTable.c.fecha_programada.desc())
Index("IDX_desp_estado", LogDespachoTable.c.estado)
Index("IDX_desp_vehiculo", LogDespachoTable.c.vehiculo_id, LogDespachoTable.c.fecha_programada)

# ============================================================================
# TABLA: log_despacho_guia
# ============================================================================
LogDespachoGuiaTable = Table(
    "log_despacho_guia",
    metadata_erp,
    Column("despacho_guia_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("despacho_id", UNIQUEIDENTIFIER, ForeignKey("log_despacho.despacho_id", ondelete="CASCADE"), nullable=False),
    Column("guia_remision_id", UNIQUEIDENTIFIER, ForeignKey("log_guia_remision.guia_remision_id"), nullable=False),
    Column("orden_entrega", Integer, nullable=True),
    Column("fecha_entrega", DateTime, nullable=True),
    Column("estado_entrega", String(20), nullable=True, server_default="pendiente"),
    Column("observaciones_entrega", String(500), nullable=True),
    Column("receptor_nombre", String(150), nullable=True),
    Column("receptor_documento", String(20), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "despacho_id", "guia_remision_id", name="UQ_desp_guia"),
)
Index("IDX_despguia_desp", LogDespachoGuiaTable.c.despacho_id, LogDespachoGuiaTable.c.orden_entrega)
Index("IDX_despguia_guia", LogDespachoGuiaTable.c.guia_remision_id)
