# app/modules/inv/presentation/schemas.py
"""
Schemas Pydantic para el módulo INV (Inventarios).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
✅ Campos esenciales incluidos desde el inicio.
"""
from typing import Optional, Any, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.shared.validators import normalize_upper, normalize_lower, normalize_strip


# ----- Mixins de normalización (solo Create / Update) -----

class _CategoriaWriteMixin:
    @field_validator(
        "codigo",
        "ruta_jerarquica",
        "cuenta_contable_inventario",
        "cuenta_contable_costo_venta",
        "metodo_costeo_defecto",
        mode="before",
    )
    @classmethod
    def _upper_categoria(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("nombre", "descripcion", mode="before")
    @classmethod
    def _strip_categoria(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _UnidadMedidaWriteMixin:
    @field_validator("codigo", "tipo_unidad", mode="before")
    @classmethod
    def _upper_unidad_medida(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("nombre", "simbolo", mode="before")
    @classmethod
    def _strip_unidad_medida(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _ProductoWriteMixin:
    @field_validator(
        "codigo_sku",
        "codigo_barra",
        "codigo_interno",
        "codigo_fabricante",
        "codigo_sunat",
        "tipo_producto",
        "subtipo_producto",
        "tipo_afectacion_igv",
        "metodo_costeo",
        "estado",
        mode="before",
    )
    @classmethod
    def _upper_producto(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("imagen_principal_url", "ficha_tecnica_url", mode="before")
    @classmethod
    def _lower_producto(cls, v: Optional[str]) -> Optional[str]:
        return normalize_lower(v)

    @field_validator(
        "nombre",
        "nombre_corto",
        "descripcion",
        "descripcion_corta",
        "marca",
        "modelo",
        "linea_producto",
        "color",
        "talla",
        "observaciones",
        "especificaciones_tecnicas",
        "atributos_personalizados",
        "imagenes_adicionales",
        mode="before",
    )
    @classmethod
    def _strip_producto(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _AlmacenWriteMixin:
    @field_validator("codigo", "tipo_almacen", mode="before")
    @classmethod
    def _upper_almacen(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator(
        "nombre",
        "descripcion",
        "direccion",
        "responsable_nombre",
        mode="before",
    )
    @classmethod
    def _strip_almacen(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _TipoMovimientoWriteMixin:
    @field_validator(
        "codigo",
        "clase_movimiento",
        "cuenta_contable_debito",
        "cuenta_contable_credito",
        "tipo_documento_referencia",
        mode="before",
    )
    @classmethod
    def _upper_tipo_movimiento(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("nombre", "descripcion", mode="before")
    @classmethod
    def _strip_tipo_movimiento(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _MovimientoWriteMixin:
    @field_validator(
        "numero_movimiento",
        "modulo_origen",
        "documento_referencia_tipo",
        "documento_referencia_numero",
        "tercero_tipo",
        "moneda",
        "estado",
        mode="before",
    )
    @classmethod
    def _upper_movimiento(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator(
        "tercero_nombre",
        "observaciones",
        "motivo_anulacion",
        mode="before",
    )
    @classmethod
    def _strip_movimiento(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _MovimientoDetalleWriteMixin:
    @field_validator(
        "lote",
        "numero_serie",
        "ubicacion_almacen",
        "moneda",
        mode="before",
    )
    @classmethod
    def _upper_movimiento_detalle(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("observaciones", mode="before")
    @classmethod
    def _strip_movimiento_detalle(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _StockWriteMixin:
    @field_validator("ubicacion_almacen", mode="before")
    @classmethod
    def _upper_stock(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)


class _InventarioFisicoWriteMixin:
    @field_validator(
        "numero_inventario",
        "tipo_inventario",
        "ubicacion_almacen",
        "estado",
        mode="before",
    )
    @classmethod
    def _upper_inventario_fisico(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator(
        "descripcion",
        "supervisor_nombre",
        "observaciones",
        mode="before",
    )
    @classmethod
    def _strip_inventario_fisico(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _InventarioFisicoDetalleWriteMixin:
    @field_validator("lote", "ubicacion_almacen", "estado_conteo", mode="before")
    @classmethod
    def _upper_inventario_fisico_detalle(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator(
        "contador_nombre",
        "observaciones",
        "motivo_diferencia",
        mode="before",
    )
    @classmethod
    def _strip_inventario_fisico_detalle(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


# ============================================================================
# CATEGORÍA DE PRODUCTO
# ============================================================================
class CategoriaCreate(_CategoriaWriteMixin, BaseModel):
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


class CategoriaUpdate(_CategoriaWriteMixin, BaseModel):
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
class UnidadMedidaCreate(_UnidadMedidaWriteMixin, BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=50)
    simbolo: Optional[str] = Field(None, max_length=10)
    tipo_unidad: str = Field(..., max_length=20)  # 'cantidad', 'peso', 'volumen', etc.
    es_unidad_base: Optional[bool] = False
    factor_conversion_base: Optional[Decimal] = None
    decimales_permitidos: Optional[int] = 2
    es_activo: Optional[bool] = True


class UnidadMedidaUpdate(_UnidadMedidaWriteMixin, BaseModel):
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
class ProductoCreate(_ProductoWriteMixin, BaseModel):
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
    moneda_costo: UUID
    precio_base_venta: Optional[Decimal] = None
    moneda_venta: UUID
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


class ProductoUpdate(_ProductoWriteMixin, BaseModel):
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
    moneda_costo: Optional[UUID] = None
    precio_base_venta: Optional[Decimal] = None
    moneda_venta: Optional[UUID] = None
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
    moneda_costo: UUID
    precio_base_venta: Optional[Decimal] = None
    moneda_venta: UUID
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
class AlmacenCreate(_AlmacenWriteMixin, BaseModel):
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


class AlmacenUpdate(_AlmacenWriteMixin, BaseModel):
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
class StockCreate(_StockWriteMixin, BaseModel):
    empresa_id: UUID
    producto_id: UUID
    almacen_id: UUID
    cantidad_actual: Optional[Decimal] = Field(0, ge=0)
    cantidad_reservada: Optional[Decimal] = Field(0, ge=0)
    cantidad_transito: Optional[Decimal] = Field(0, ge=0)
    costo_promedio: Optional[Decimal] = Field(0, ge=0)
    moneda_id: UUID
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_reorden: Optional[Decimal] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    fecha_ultimo_movimiento: Optional[datetime] = None
    fecha_ultima_compra: Optional[datetime] = None
    fecha_ultima_venta: Optional[datetime] = None


class StockUpdate(_StockWriteMixin, BaseModel):
    cantidad_actual: Optional[Decimal] = None
    cantidad_reservada: Optional[Decimal] = None
    cantidad_transito: Optional[Decimal] = None
    costo_promedio: Optional[Decimal] = None
    moneda_id: Optional[UUID] = None
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
    moneda_id: UUID
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
# KARDEX (consulta)
# ============================================================================
class KardexLineaRead(BaseModel):
    movimiento_id: UUID
    movimiento_detalle_id: UUID
    empresa_id: UUID
    fecha_movimiento: datetime
    tipo_movimiento_id: UUID
    producto_id: UUID
    almacen_origen_id: Optional[UUID] = None
    almacen_destino_id: Optional[UUID] = None
    cantidad_base: Decimal
    costo_unitario: Optional[Decimal] = None
    moneda: Optional[str] = None
    lote: Optional[str] = None
    numero_serie: Optional[str] = None
    observaciones: Optional[str] = None


# ============================================================================
# TIPO DE MOVIMIENTO
# ============================================================================
class TipoMovimientoCreate(_TipoMovimientoWriteMixin, BaseModel):
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


class TipoMovimientoUpdate(_TipoMovimientoWriteMixin, BaseModel):
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
class MovimientoCreate(_MovimientoWriteMixin, BaseModel):
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
    # Alineado a BD: inv_movimiento.moneda_id (FK cat_moneda.moneda_id)
    moneda_id: Optional[UUID] = Field(
        None,
        description="ID de moneda (cat_moneda.moneda_id). Preferido.",
    )
    # Compatibilidad legacy: antes se enviaba 'PEN', 'USD', etc.
    moneda: Optional[str] = Field(
        "PEN",
        description="(Legacy) Código de moneda. Usar moneda_id.",
        max_length=10,
    )
    estado: Optional[str] = Field("borrador", max_length=20)
    requiere_autorizacion: Optional[bool] = False
    autorizado_por_usuario_id: Optional[UUID] = None
    fecha_autorizacion: Optional[datetime] = None
    observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = Field(None, max_length=500)
    centro_costo_id: Optional[UUID] = None


class MovimientoUpdate(_MovimientoWriteMixin, BaseModel):
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
    moneda_id: Optional[UUID] = Field(
        None,
        description="ID de moneda (cat_moneda.moneda_id). Preferido.",
    )
    moneda: Optional[str] = Field(
        None,
        description="(Legacy) Código de moneda. Usar moneda_id.",
        max_length=10,
    )
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
    moneda_id: Optional[UUID] = None
    # Nota: algunos queries pueden retornar código de moneda (legacy/consulta).
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
class InventarioFisicoCreate(_InventarioFisicoWriteMixin, BaseModel):
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


class InventarioFisicoUpdate(_InventarioFisicoWriteMixin, BaseModel):
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


# ============================================================================
# MOVIMIENTO DETALLE (solo lectura/escritura básica)
# ============================================================================
class MovimientoDetalleBase(BaseModel):
    empresa_id: UUID
    movimiento_id: UUID
    producto_id: UUID
    cantidad: Decimal
    unidad_medida_id: UUID
    cantidad_base: Decimal
    costo_unitario: Optional[Decimal] = None
    # Alineado a BD: inv_movimiento_detalle.moneda_id (FK cat_moneda.moneda_id)
    moneda_id: Optional[UUID] = Field(
        None,
        description="ID de moneda (cat_moneda.moneda_id). Preferido.",
    )
    moneda: Optional[str] = Field(
        "PEN",
        description="(Legacy) Código de moneda. Usar moneda_id.",
        max_length=10,
    )
    lote: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[date] = None
    numero_serie: Optional[str] = Field(None, max_length=100)
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = Field(None, max_length=500)


class MovimientoDetalleCreate(_MovimientoDetalleWriteMixin, MovimientoDetalleBase):
    pass


class MovimientoDetalleUpdate(_MovimientoDetalleWriteMixin, BaseModel):
    cantidad: Optional[Decimal] = None
    unidad_medida_id: Optional[UUID] = None
    cantidad_base: Optional[Decimal] = None
    costo_unitario: Optional[Decimal] = None
    moneda_id: Optional[UUID] = Field(
        None,
        description="ID de moneda (cat_moneda.moneda_id). Preferido.",
    )
    moneda: Optional[str] = Field(
        None,
        description="(Legacy) Código de moneda. Usar moneda_id.",
        max_length=10,
    )
    lote: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[date] = None
    numero_serie: Optional[str] = Field(None, max_length=100)
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = Field(None, max_length=500)


class MovimientoDetalleRead(BaseModel):
    movimiento_detalle_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    movimiento_id: UUID
    producto_id: UUID
    cantidad: Decimal
    unidad_medida_id: UUID
    cantidad_base: Decimal
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None          # AS (cantidad * costo_unitario) PERSISTED
    moneda_id: Optional[UUID] = None
    moneda: Optional[str] = None
    lote: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    numero_serie: Optional[str] = None
    ubicacion_almacen: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# INVENTARIO FÍSICO DETALLE
# ============================================================================
class InventarioFisicoDetalleBase(BaseModel):
    empresa_id: UUID
    inventario_fisico_id: UUID
    producto_id: UUID
    cantidad_sistema: Decimal
    cantidad_contada: Optional[Decimal] = None
    lote: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[date] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    costo_unitario: Optional[Decimal] = None
    estado_conteo: Optional[str] = Field("pendiente", max_length=20)
    contador_usuario_id: Optional[UUID] = None
    contador_nombre: Optional[str] = Field(None, max_length=150)
    fecha_conteo: Optional[datetime] = None
    observaciones: Optional[str] = Field(None, max_length=500)
    motivo_diferencia: Optional[str] = Field(None, max_length=500)


class InventarioFisicoDetalleCreate(
    _InventarioFisicoDetalleWriteMixin, InventarioFisicoDetalleBase
):
    pass


class InventarioFisicoDetalleUpdate(_InventarioFisicoDetalleWriteMixin, BaseModel):
    cantidad_sistema: Optional[Decimal] = None
    cantidad_contada: Optional[Decimal] = None
    lote: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[date] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    costo_unitario: Optional[Decimal] = None
    estado_conteo: Optional[str] = Field(None, max_length=20)
    contador_usuario_id: Optional[UUID] = None
    contador_nombre: Optional[str] = Field(None, max_length=150)
    fecha_conteo: Optional[datetime] = None
    observaciones: Optional[str] = Field(None, max_length=500)
    motivo_diferencia: Optional[str] = Field(None, max_length=500)


class InventarioFisicoDetalleRead(BaseModel):
    inventario_fisico_detalle_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    inventario_fisico_id: UUID
    producto_id: UUID
    cantidad_sistema: Decimal
    cantidad_contada: Optional[Decimal] = None
    diferencia: Optional[Decimal] = None           # AS (cantidad_contada - cantidad_sistema) PERSISTED
    lote: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    ubicacion_almacen: Optional[str] = None
    costo_unitario: Optional[Decimal] = None
    valor_diferencia: Optional[Decimal] = None     # AS ((cantidad_contada - cantidad_sistema) * costo_unitario) PERSISTED
    estado_conteo: Optional[str] = None
    contador_usuario_id: Optional[UUID] = None
    contador_nombre: Optional[str] = None
    fecha_conteo: Optional[datetime] = None
    observaciones: Optional[str] = None
    motivo_diferencia: Optional[str] = None
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS CABECERA + DETALLE EMBEBIDO — MOVIMIENTO
# ============================================================================

class MovimientoDetalleCreateEmbebido(_MovimientoDetalleWriteMixin, BaseModel):
    """Línea de movimiento para crear embebida en la cabecera.
    No incluye movimiento_id ni empresa_id: se heredan de la cabecera."""
    producto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    unidad_medida_id: UUID
    cantidad_base: Decimal = Field(..., gt=0)
    costo_unitario: Optional[Decimal] = Field(None, ge=0)
    moneda_id: Optional[UUID] = Field(
        None,
        description="ID de moneda (cat_moneda.moneda_id). Preferido.",
    )
    moneda: Optional[str] = Field(
        "PEN",
        description="(Legacy) Código de moneda. Usar moneda_id.",
        max_length=10,
    )
    lote: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[date] = None
    numero_serie: Optional[str] = Field(None, max_length=100)
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = Field(None, max_length=500)


class MovimientoConDetalleCreate(MovimientoCreate):
    """Movimiento completo: cabecera + líneas obligatorias (mínimo 1)."""
    detalles: List[MovimientoDetalleCreateEmbebido] = Field(
        ..., min_length=1, description="Líneas del movimiento. Mínimo 1."
    )


class MovimientoConDetalleUpdate(MovimientoUpdate):
    """Actualización de movimiento (solo en borrador) + reemplazo opcional de líneas.
    Si 'detalles' se provee, reemplaza todas las líneas existentes."""
    detalles: Optional[List[MovimientoDetalleCreateEmbebido]] = Field(
        None, description="Si se provee, reemplaza todas las líneas existentes."
    )


class MovimientoConDetalleRead(MovimientoRead):
    """Movimiento con sus líneas embebidas en la respuesta."""
    detalles: List[MovimientoDetalleRead] = Field(default_factory=list)


# ============================================================================
# SCHEMAS CABECERA + DETALLE EMBEBIDO — INVENTARIO FÍSICO
# ============================================================================

class InventarioFisicoDetalleCreateEmbebido(_InventarioFisicoDetalleWriteMixin, BaseModel):
    """Línea de inventario físico para crear embebida en la cabecera.
    No incluye inventario_fisico_id ni empresa_id: se heredan de la cabecera."""
    producto_id: UUID
    cantidad_sistema: Decimal = Field(..., ge=0)
    cantidad_contada: Optional[Decimal] = Field(None, ge=0)
    lote: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[date] = None
    ubicacion_almacen: Optional[str] = Field(None, max_length=50)
    costo_unitario: Optional[Decimal] = Field(None, ge=0)
    estado_conteo: Optional[str] = Field("pendiente", max_length=20)
    contador_usuario_id: Optional[UUID] = None
    contador_nombre: Optional[str] = Field(None, max_length=150)
    fecha_conteo: Optional[datetime] = None
    observaciones: Optional[str] = Field(None, max_length=500)
    motivo_diferencia: Optional[str] = Field(None, max_length=500)


class InventarioFisicoConDetalleCreate(InventarioFisicoCreate):
    """Inventario físico completo: cabecera + líneas opcionales al crear
    (se pueden agregar durante el conteo)."""
    detalles: List[InventarioFisicoDetalleCreateEmbebido] = Field(
        default_factory=list,
        description="Líneas de conteo. Se pueden añadir al crear o en PUT posterior.",
    )


class InventarioFisicoConDetalleUpdate(InventarioFisicoUpdate):
    """Actualización de inventario físico + reemplazo opcional de líneas.
    Si 'detalles' se provee, reemplaza todas las líneas existentes."""
    detalles: Optional[List[InventarioFisicoDetalleCreateEmbebido]] = Field(
        None, description="Si se provee, reemplaza todas las líneas existentes."
    )


class InventarioFisicoConDetalleRead(InventarioFisicoRead):
    """Inventario físico con sus líneas de conteo embebidas en la respuesta."""
    detalles: List[InventarioFisicoDetalleRead] = Field(default_factory=list)


# ----- Respuestas paginadas ERP (P0) -----

from app.shared.pagination.schemas import ErpPaginatedResponse


class PaginatedMovimientoResponse(ErpPaginatedResponse[MovimientoRead]):
    """Listado paginado de movimientos."""


class PaginatedKardexResponse(ErpPaginatedResponse[KardexLineaRead]):
    """Listado paginado de kardex."""


class PaginatedInventarioFisicoResponse(ErpPaginatedResponse[InventarioFisicoRead]):
    """Listado paginado de inventarios físicos."""


class PaginatedStockResponse(ErpPaginatedResponse[StockRead]):
    """Listado paginado de stocks."""


class PaginatedProductoResponse(ErpPaginatedResponse[ProductoRead]):
    """Listado paginado de productos."""


class PaginatedCategoriaResponse(ErpPaginatedResponse[CategoriaRead]):
    """Listado paginado de categorías."""


class PaginatedAlmacenResponse(ErpPaginatedResponse[AlmacenRead]):
    """Listado paginado de almacenes."""


class PaginatedUnidadMedidaResponse(ErpPaginatedResponse[UnidadMedidaRead]):
    """Listado paginado de unidades de medida."""


class PaginatedTipoMovimientoResponse(ErpPaginatedResponse[TipoMovimientoRead]):
    """Listado paginado de tipos de movimiento."""
