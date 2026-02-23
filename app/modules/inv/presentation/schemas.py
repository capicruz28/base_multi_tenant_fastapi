# app/modules/inv/presentation/schemas.py
"""
Schemas Pydantic para el módulo INV (Inventarios).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# CATEGORÍA DE PRODUCTO
# ============================================================================
class CategoriaCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    categoria_padre_id: Optional[UUID] = None
    nivel: Optional[int] = 1
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
    cuenta_contable_inventario: Optional[str] = Field(None, max_length=20)
    cuenta_contable_costo_venta: Optional[str] = Field(None, max_length=20)
    metodo_costeo_defecto: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = True


class CategoriaUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    categoria_padre_id: Optional[UUID] = None
    nivel: Optional[int] = None
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
    cuenta_contable_inventario: Optional[str] = Field(None, max_length=20)
    cuenta_contable_costo_venta: Optional[str] = Field(None, max_length=20)
    metodo_costeo_defecto: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = None


class CategoriaRead(BaseModel):
    categoria_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    categoria_padre_id: Optional[UUID] = None
    nivel: Optional[int] = None
    ruta_jerarquica: Optional[str] = None
    cuenta_contable_inventario: Optional[str] = None
    cuenta_contable_costo_venta: Optional[str] = None
    metodo_costeo_defecto: Optional[str] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# UNIDAD DE MEDIDA
# ============================================================================
class UnidadMedidaCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=50)
    simbolo: Optional[str] = Field(None, max_length=10)
    tipo_unidad: str = Field(..., max_length=20)  # 'cantidad', 'peso', 'volumen', etc.
    es_unidad_base: Optional[bool] = False
    factor_conversion_base: Optional[Decimal] = None
    decimales_permitidos: Optional[int] = 2
    es_activo: Optional[bool] = True


class UnidadMedidaUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=10)
    nombre: Optional[str] = Field(None, max_length=50)
    simbolo: Optional[str] = Field(None, max_length=10)
    tipo_unidad: Optional[str] = Field(None, max_length=20)
    es_unidad_base: Optional[bool] = None
    factor_conversion_base: Optional[Decimal] = None
    decimales_permitidos: Optional[int] = None
    es_activo: Optional[bool] = None


class UnidadMedidaRead(BaseModel):
    unidad_medida_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    simbolo: Optional[str] = None
    tipo_unidad: str
    es_unidad_base: Optional[bool] = None
    factor_conversion_base: Optional[Decimal] = None
    decimales_permitidos: Optional[int] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# PRODUCTO
# ============================================================================
class ProductoCreate(BaseModel):
    empresa_id: UUID
    codigo_sku: str = Field(..., max_length=50)
    codigo_barra: Optional[str] = Field(None, max_length=50)
    codigo_interno: Optional[str] = Field(None, max_length=30)
    codigo_fabricante: Optional[str] = Field(None, max_length=50)
    nombre: str = Field(..., max_length=200)
    nombre_corto: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    descripcion_corta: Optional[str] = Field(None, max_length=500)
    categoria_id: Optional[UUID] = None
    subcategoria_id: Optional[UUID] = None
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    linea_producto: Optional[str] = Field(None, max_length=100)
    tipo_producto: str = Field(..., max_length=30)  # 'bien', 'servicio', 'materia_prima', etc.
    subtipo_producto: Optional[str] = Field(None, max_length=50)
    unidad_medida_base_id: UUID
    unidad_medida_compra_id: Optional[UUID] = None
    unidad_medida_venta_id: Optional[UUID] = None
    factor_conversion_compra: Optional[Decimal] = Field(1, ge=0)
    factor_conversion_venta: Optional[Decimal] = Field(1, ge=0)
    peso_kg: Optional[Decimal] = None
    volumen_m3: Optional[Decimal] = None
    largo_cm: Optional[Decimal] = None
    ancho_cm: Optional[Decimal] = None
    alto_cm: Optional[Decimal] = None
    color: Optional[str] = Field(None, max_length=50)
    talla: Optional[str] = Field(None, max_length=20)
    atributos_personalizados: Optional[str] = None  # JSON
    especificaciones_tecnicas: Optional[str] = None  # JSON o texto
    maneja_inventario: Optional[bool] = True
    maneja_lotes: Optional[bool] = False
    maneja_series: Optional[bool] = False
    maneja_vencimiento: Optional[bool] = False
    dias_vida_util: Optional[int] = None
    requiere_refrigeracion: Optional[bool] = False
    es_perecible: Optional[bool] = False
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_reorden: Optional[Decimal] = None
    es_comprable: Optional[bool] = True
    tiempo_entrega_dias: Optional[int] = None
    cantidad_minima_compra: Optional[Decimal] = None
    multiplo_compra: Optional[Decimal] = None
    es_vendible: Optional[bool] = True
    requiere_autorizacion_venta: Optional[bool] = False
    es_fabricable: Optional[bool] = False
    tiene_lista_materiales: Optional[bool] = False
    metodo_costeo: Optional[str] = Field("promedio", max_length=20)
    costo_estandar: Optional[Decimal] = None
    costo_ultima_compra: Optional[Decimal] = None
    costo_promedio: Optional[Decimal] = None
    moneda_costo: Optional[str] = "PEN"
    precio_base_venta: Optional[Decimal] = None
    moneda_venta: Optional[str] = "PEN"
    afecto_igv: Optional[bool] = True
    porcentaje_igv: Optional[Decimal] = Field(18.00, ge=0, le=100)
    codigo_sunat: Optional[str] = Field(None, max_length=10)
    tipo_afectacion_igv: Optional[str] = Field(None, max_length=2)
    imagen_principal_url: Optional[str] = Field(None, max_length=500)
    imagenes_adicionales: Optional[str] = None  # JSON array
    ficha_tecnica_url: Optional[str] = Field(None, max_length=500)
    proveedor_habitual_id: Optional[UUID] = None
    estado: Optional[str] = Field("activo", max_length=20)
    es_activo: Optional[bool] = True
    observaciones: Optional[str] = None


class ProductoUpdate(BaseModel):
    codigo_sku: Optional[str] = Field(None, max_length=50)
    codigo_barra: Optional[str] = Field(None, max_length=50)
    codigo_interno: Optional[str] = Field(None, max_length=30)
    codigo_fabricante: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, max_length=200)
    nombre_corto: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    descripcion_corta: Optional[str] = Field(None, max_length=500)
    categoria_id: Optional[UUID] = None
    subcategoria_id: Optional[UUID] = None
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    linea_producto: Optional[str] = Field(None, max_length=100)
    tipo_producto: Optional[str] = Field(None, max_length=30)
    subtipo_producto: Optional[str] = Field(None, max_length=50)
    unidad_medida_base_id: Optional[UUID] = None
    unidad_medida_compra_id: Optional[UUID] = None
    unidad_medida_venta_id: Optional[UUID] = None
    factor_conversion_compra: Optional[Decimal] = None
    factor_conversion_venta: Optional[Decimal] = None
    peso_kg: Optional[Decimal] = None
    volumen_m3: Optional[Decimal] = None
    largo_cm: Optional[Decimal] = None
    ancho_cm: Optional[Decimal] = None
    alto_cm: Optional[Decimal] = None
    color: Optional[str] = Field(None, max_length=50)
    talla: Optional[str] = Field(None, max_length=20)
    atributos_personalizados: Optional[str] = None
    especificaciones_tecnicas: Optional[str] = None
    maneja_inventario: Optional[bool] = None
    maneja_lotes: Optional[bool] = None
    maneja_series: Optional[bool] = None
    maneja_vencimiento: Optional[bool] = None
    dias_vida_util: Optional[int] = None
    requiere_refrigeracion: Optional[bool] = None
    es_perecible: Optional[bool] = None
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_reorden: Optional[Decimal] = None
    es_comprable: Optional[bool] = None
    tiempo_entrega_dias: Optional[int] = None
    cantidad_minima_compra: Optional[Decimal] = None
    multiplo_compra: Optional[Decimal] = None
    es_vendible: Optional[bool] = None
    requiere_autorizacion_venta: Optional[bool] = None
    es_fabricable: Optional[bool] = None
    tiene_lista_materiales: Optional[bool] = None
    metodo_costeo: Optional[str] = Field(None, max_length=20)
    costo_estandar: Optional[Decimal] = None
    costo_ultima_compra: Optional[Decimal] = None
    costo_promedio: Optional[Decimal] = None
    moneda_costo: Optional[str] = None
    precio_base_venta: Optional[Decimal] = None
    moneda_venta: Optional[str] = None
    afecto_igv: Optional[bool] = None
    porcentaje_igv: Optional[Decimal] = None
    codigo_sunat: Optional[str] = Field(None, max_length=10)
    tipo_afectacion_igv: Optional[str] = Field(None, max_length=2)
    imagen_principal_url: Optional[str] = Field(None, max_length=500)
    imagenes_adicionales: Optional[str] = None
    ficha_tecnica_url: Optional[str] = Field(None, max_length=500)
    proveedor_habitual_id: Optional[UUID] = None
    estado: Optional[str] = Field(None, max_length=20)
    es_activo: Optional[bool] = None
    observaciones: Optional[str] = None


class ProductoRead(BaseModel):
    producto_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_sku: str
    codigo_barra: Optional[str] = None
    codigo_interno: Optional[str] = None
    codigo_fabricante: Optional[str] = None
    nombre: str
    nombre_corto: Optional[str] = None
    descripcion: Optional[str] = None
    descripcion_corta: Optional[str] = None
    categoria_id: Optional[UUID] = None
    subcategoria_id: Optional[UUID] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    linea_producto: Optional[str] = None
    tipo_producto: str
    subtipo_producto: Optional[str] = None
    unidad_medida_base_id: UUID
    unidad_medida_compra_id: Optional[UUID] = None
    unidad_medida_venta_id: Optional[UUID] = None
    factor_conversion_compra: Optional[Decimal] = None
    factor_conversion_venta: Optional[Decimal] = None
    peso_kg: Optional[Decimal] = None
    volumen_m3: Optional[Decimal] = None
    largo_cm: Optional[Decimal] = None
    ancho_cm: Optional[Decimal] = None
    alto_cm: Optional[Decimal] = None
    color: Optional[str] = None
    talla: Optional[str] = None
    atributos_personalizados: Optional[str] = None
    especificaciones_tecnicas: Optional[str] = None
    maneja_inventario: Optional[bool] = None
    maneja_lotes: Optional[bool] = None
    maneja_series: Optional[bool] = None
    maneja_vencimiento: Optional[bool] = None
    dias_vida_util: Optional[int] = None
    requiere_refrigeracion: Optional[bool] = None
    es_perecible: Optional[bool] = None
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_reorden: Optional[Decimal] = None
    es_comprable: Optional[bool] = None
    tiempo_entrega_dias: Optional[int] = None
    cantidad_minima_compra: Optional[Decimal] = None
    multiplo_compra: Optional[Decimal] = None
    es_vendible: Optional[bool] = None
    requiere_autorizacion_venta: Optional[bool] = None
    es_fabricable: Optional[bool] = None
    tiene_lista_materiales: Optional[bool] = None
    metodo_costeo: Optional[str] = None
    costo_estandar: Optional[Decimal] = None
    costo_ultima_compra: Optional[Decimal] = None
    costo_promedio: Optional[Decimal] = None
    moneda_costo: Optional[str] = None
    precio_base_venta: Optional[Decimal] = None
    moneda_venta: Optional[str] = None
    afecto_igv: Optional[bool] = None
    porcentaje_igv: Optional[Decimal] = None
    codigo_sunat: Optional[str] = None
    tipo_afectacion_igv: Optional[str] = None
    imagen_principal_url: Optional[str] = None
    imagenes_adicionales: Optional[str] = None
    ficha_tecnica_url: Optional[str] = None
    proveedor_habitual_id: Optional[UUID] = None
    estado: Optional[str] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None
    usuario_actualizacion_id: Optional[UUID] = None
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# ALMACÉN
# ============================================================================
class AlmacenCreate(BaseModel):
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_almacen: str = Field(..., max_length=30)
    direccion: Optional[str] = Field(None, max_length=255)
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = Field(None, max_length=150)
    es_almacen_principal: Optional[bool] = False
    permite_ventas: Optional[bool] = False
    permite_compras: Optional[bool] = True
    permite_produccion: Optional[bool] = False
    capacidad_m3: Optional[Decimal] = None
    capacidad_kg: Optional[Decimal] = None
    capacidad_unidades: Optional[int] = None
    centro_costo_id: Optional[UUID] = None
    es_activo: Optional[bool] = True


class AlmacenUpdate(BaseModel):
    sucursal_id: Optional[UUID] = None
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_almacen: Optional[str] = Field(None, max_length=30)
    direccion: Optional[str] = Field(None, max_length=255)
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = Field(None, max_length=150)
    es_almacen_principal: Optional[bool] = None
    permite_ventas: Optional[bool] = None
    permite_compras: Optional[bool] = None
    permite_produccion: Optional[bool] = None
    capacidad_m3: Optional[Decimal] = None
    capacidad_kg: Optional[Decimal] = None
    capacidad_unidades: Optional[int] = None
    centro_costo_id: Optional[UUID] = None
    es_activo: Optional[bool] = None


class AlmacenRead(BaseModel):
    almacen_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_almacen: str
    direccion: Optional[str] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    es_almacen_principal: Optional[bool] = None
    permite_ventas: Optional[bool] = None
    permite_compras: Optional[bool] = None
    permite_produccion: Optional[bool] = None
    capacidad_m3: Optional[Decimal] = None
    capacidad_kg: Optional[Decimal] = None
    capacidad_unidades: Optional[int] = None
    centro_costo_id: Optional[UUID] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# STOCK
# ============================================================================
class StockCreate(BaseModel):
    empresa_id: UUID
    producto_id: UUID
    almacen_id: UUID
    cantidad_actual: Optional[Decimal] = Field(0, ge=0)
    cantidad_reservada: Optional[Decimal] = Field(0, ge=0)
    cantidad_transito: Optional[Decimal] = Field(0, ge=0)
    costo_promedio: Optional[Decimal] = Field(0, ge=0)
    moneda: Optional[str] = "PEN"
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_reorden: Optional[Decimal] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    fecha_ultimo_movimiento: Optional[datetime] = None
    fecha_ultima_compra: Optional[datetime] = None
    fecha_ultima_venta: Optional[datetime] = None


class StockUpdate(BaseModel):
    cantidad_actual: Optional[Decimal] = None
    cantidad_reservada: Optional[Decimal] = None
    cantidad_transito: Optional[Decimal] = None
    costo_promedio: Optional[Decimal] = None
    moneda: Optional[str] = None
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_reorden: Optional[Decimal] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    fecha_ultimo_movimiento: Optional[datetime] = None
    fecha_ultima_compra: Optional[datetime] = None
    fecha_ultima_venta: Optional[datetime] = None


class StockRead(BaseModel):
    stock_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    producto_id: UUID
    almacen_id: UUID
    cantidad_actual: Decimal
    cantidad_reservada: Optional[Decimal] = None
    cantidad_disponible: Optional[Decimal] = None  # Calculado en BD
    cantidad_transito: Optional[Decimal] = None
    costo_promedio: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None  # Calculado en BD
    moneda: Optional[str] = None
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_reorden: Optional[Decimal] = None
    ubicacion_almacen: Optional[str] = None
    fecha_ultimo_movimiento: Optional[datetime] = None
    fecha_ultima_compra: Optional[datetime] = None
    fecha_ultima_venta: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# TIPO DE MOVIMIENTO
# ============================================================================
class TipoMovimientoCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    clase_movimiento: str = Field(..., max_length=20)  # 'entrada', 'salida', 'transferencia', 'ajuste'
    afecta_costo: Optional[bool] = True
    requiere_autorizacion: Optional[bool] = False
    genera_asiento_contable: Optional[bool] = False
    cuenta_contable_debito: Optional[str] = Field(None, max_length=20)
    cuenta_contable_credito: Optional[str] = Field(None, max_length=20)
    requiere_documento_referencia: Optional[bool] = False
    tipo_documento_referencia: Optional[str] = Field(None, max_length=50)
    es_activo: Optional[bool] = True
    es_tipo_sistema: Optional[bool] = False


class TipoMovimientoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    clase_movimiento: Optional[str] = Field(None, max_length=20)
    afecta_costo: Optional[bool] = None
    requiere_autorizacion: Optional[bool] = None
    genera_asiento_contable: Optional[bool] = None
    cuenta_contable_debito: Optional[str] = Field(None, max_length=20)
    cuenta_contable_credito: Optional[str] = Field(None, max_length=20)
    requiere_documento_referencia: Optional[bool] = None
    tipo_documento_referencia: Optional[str] = Field(None, max_length=50)
    es_activo: Optional[bool] = None
    es_tipo_sistema: Optional[bool] = None


class TipoMovimientoRead(BaseModel):
    tipo_movimiento_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    clase_movimiento: str
    afecta_costo: Optional[bool] = None
    requiere_autorizacion: Optional[bool] = None
    genera_asiento_contable: Optional[bool] = None
    cuenta_contable_debito: Optional[str] = None
    cuenta_contable_credito: Optional[str] = None
    requiere_documento_referencia: Optional[bool] = None
    tipo_documento_referencia: Optional[str] = None
    es_activo: bool
    es_tipo_sistema: Optional[bool] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# MOVIMIENTO
# ============================================================================
class MovimientoCreate(BaseModel):
    empresa_id: UUID
    numero_movimiento: str = Field(..., max_length=20)
    tipo_movimiento_id: UUID
    fecha_movimiento: Optional[datetime] = None
    fecha_contable: date
    almacen_origen_id: Optional[UUID] = None
    almacen_destino_id: Optional[UUID] = None
    modulo_origen: Optional[str] = Field(None, max_length=10)
    documento_referencia_tipo: Optional[str] = Field(None, max_length=20)
    documento_referencia_id: Optional[UUID] = None
    documento_referencia_numero: Optional[str] = Field(None, max_length=30)
    tercero_tipo: Optional[str] = Field(None, max_length=20)
    tercero_id: Optional[UUID] = None
    tercero_nombre: Optional[str] = Field(None, max_length=200)
    total_items: Optional[int] = 0
    total_cantidad: Optional[Decimal] = Field(0, ge=0)
    total_costo: Optional[Decimal] = Field(0, ge=0)
    moneda: Optional[str] = "PEN"
    estado: Optional[str] = Field("borrador", max_length=20)
    requiere_autorizacion: Optional[bool] = False
    autorizado_por_usuario_id: Optional[UUID] = None
    fecha_autorizacion: Optional[datetime] = None
    observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    centro_costo_id: Optional[UUID] = None


class MovimientoUpdate(BaseModel):
    numero_movimiento: Optional[str] = Field(None, max_length=20)
    tipo_movimiento_id: Optional[UUID] = None
    fecha_movimiento: Optional[datetime] = None
    fecha_contable: Optional[date] = None
    almacen_origen_id: Optional[UUID] = None
    almacen_destino_id: Optional[UUID] = None
    modulo_origen: Optional[str] = Field(None, max_length=10)
    documento_referencia_tipo: Optional[str] = Field(None, max_length=20)
    documento_referencia_id: Optional[UUID] = None
    documento_referencia_numero: Optional[str] = Field(None, max_length=30)
    tercero_tipo: Optional[str] = Field(None, max_length=20)
    tercero_id: Optional[UUID] = None
    tercero_nombre: Optional[str] = Field(None, max_length=200)
    total_items: Optional[int] = None
    total_cantidad: Optional[Decimal] = None
    total_costo: Optional[Decimal] = None
    moneda: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=20)
    requiere_autorizacion: Optional[bool] = None
    autorizado_por_usuario_id: Optional[UUID] = None
    fecha_autorizacion: Optional[datetime] = None
    observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    centro_costo_id: Optional[UUID] = None


class MovimientoRead(BaseModel):
    movimiento_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_movimiento: str
    tipo_movimiento_id: UUID
    fecha_movimiento: datetime
    fecha_contable: date
    almacen_origen_id: Optional[UUID] = None
    almacen_destino_id: Optional[UUID] = None
    modulo_origen: Optional[str] = None
    documento_referencia_tipo: Optional[str] = None
    documento_referencia_id: Optional[UUID] = None
    documento_referencia_numero: Optional[str] = None
    tercero_tipo: Optional[str] = None
    tercero_id: Optional[UUID] = None
    tercero_nombre: Optional[str] = None
    total_items: Optional[int] = None
    total_cantidad: Optional[Decimal] = None
    total_costo: Optional[Decimal] = None
    moneda: Optional[str] = None
    estado: str
    requiere_autorizacion: Optional[bool] = None
    autorizado_por_usuario_id: Optional[UUID] = None
    fecha_autorizacion: Optional[datetime] = None
    observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = None
    centro_costo_id: Optional[UUID] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    fecha_procesado: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None
    usuario_procesado_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# INVENTARIO FÍSICO
# ============================================================================
class InventarioFisicoCreate(BaseModel):
    empresa_id: UUID
    numero_inventario: str = Field(..., max_length=20)
    fecha_inventario: date
    almacen_id: UUID
    tipo_inventario: str = Field(..., max_length=20)  # 'total', 'ciclico', 'selectivo'
    descripcion: Optional[str] = Field(None, max_length=255)
    categoria_id: Optional[UUID] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    estado: Optional[str] = Field("en_proceso", max_length=20)
    supervisor_usuario_id: Optional[UUID] = None
    supervisor_nombre: Optional[str] = Field(None, max_length=150)
    total_productos_contados: Optional[int] = 0
    total_diferencias: Optional[int] = 0
    valor_diferencias: Optional[Decimal] = Field(0, ge=0)
    movimiento_ajuste_id: Optional[UUID] = None
    observaciones: Optional[str] = None


class InventarioFisicoUpdate(BaseModel):
    numero_inventario: Optional[str] = Field(None, max_length=20)
    fecha_inventario: Optional[date] = None
    almacen_id: Optional[UUID] = None
    tipo_inventario: Optional[str] = Field(None, max_length=20)
    descripcion: Optional[str] = Field(None, max_length=255)
    categoria_id: Optional[UUID] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    estado: Optional[str] = Field(None, max_length=20)
    supervisor_usuario_id: Optional[UUID] = None
    supervisor_nombre: Optional[str] = Field(None, max_length=150)
    total_productos_contados: Optional[int] = None
    total_diferencias: Optional[int] = None
    valor_diferencias: Optional[Decimal] = None
    movimiento_ajuste_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    fecha_finalizacion: Optional[datetime] = None
    fecha_ajuste: Optional[datetime] = None


class InventarioFisicoRead(BaseModel):
    inventario_fisico_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_inventario: str
    fecha_inventario: date
    almacen_id: UUID
    tipo_inventario: str
    descripcion: Optional[str] = None
    categoria_id: Optional[UUID] = None
    ubicacion_almacen: Optional[str] = None
    estado: str
    supervisor_usuario_id: Optional[UUID] = None
    supervisor_nombre: Optional[str] = None
    total_productos_contados: Optional[int] = None
    total_diferencias: Optional[int] = None
    valor_diferencias: Optional[Decimal] = None
    movimiento_ajuste_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_finalizacion: Optional[datetime] = None
    fecha_ajuste: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True
