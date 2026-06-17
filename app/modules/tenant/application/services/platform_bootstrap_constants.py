"""
Constantes de bootstrap plataforma (fuente de verdad runtime).

Desacoplado de D010 — equivalencia semántica bloques A–E validados manualmente.
"""
from __future__ import annotations

DEFAULT_RAZON_SOCIAL = "Sistema ERP Multi-Tenant"
DEFAULT_NOMBRE_COMERCIAL = "Plataforma Admin"
DEFAULT_CONTACTO_NOMBRE = "Administrador Plataforma"
DEFAULT_CONTACT_EMAIL_FALLBACK = "admin@platform.com"

TIPO_INSTALACION_SHARED = "shared"
MODO_AUTENTICACION_LOCAL = "local"
PLAN_SUSCRIPCION_ENTERPRISE = "enterprise"
ESTADO_SUSCRIPCION_ACTIVO = "activo"

COLOR_PRIMARIO = "#3B82F6"
COLOR_SECUNDARIO = "#0A1628"

ADMIN_PLATFORM_CODIGO_ROL = "ADMIN_PLATFORM"
ADMIN_PLATFORM_NOMBRE = "Administrador"
ADMIN_PLATFORM_DESCRIPCION = "Rol de administrador con acceso completo a la plataforma"
ADMIN_PLATFORM_NIVEL_ACCESO = 5

SUPERADMIN_NOMBRE = "Administrador"
SUPERADMIN_APELLIDO = "Sistema"
PROVEEDOR_AUTENTICACION_LOCAL = "local"

MIN_RP_COUNT_READY = 5
