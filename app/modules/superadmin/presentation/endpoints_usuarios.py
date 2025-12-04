# app/api/v1/endpoints/superadmin_usuarios.py
"""
Módulo de endpoints exclusivos para Superadmin - Gestión de Usuarios.

Este módulo proporciona endpoints para que el Superadmin pueda ver y gestionar
usuarios de todos los clientes con filtrado opcional por cliente_id.

Características principales:
- NO modifica endpoints existentes en usuarios.py
- Solo accesible por Superadmin (nivel 5)
- Filtrado opcional por cliente_id en todos los endpoints
- Incluye información del cliente en respuestas
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from typing import Optional
from uuid import UUID

# Importar Schemas
from app.modules.superadmin.presentation.schemas import (
    UsuarioSuperadminRead,
    PaginatedUsuarioSuperadminResponse,
    UsuarioActividadResponse,
    UsuarioSesionesResponse
)

# Importar Servicios
from app.modules.superadmin.application.services.superadmin_usuario_service import SuperadminUsuarioService

# Importar Excepciones personalizadas
from app.core.exceptions import CustomException

# Importar Dependencias de Autorización
from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin

# Logging
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedUsuarioSuperadminResponse,
    summary="Listado global de usuarios (Superadmin)",
    description="""
    Recupera una lista paginada de usuarios de todos los clientes.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de consulta:**
    - cliente_id (opcional): Filtrar por cliente específico. Si no se proporciona, muestra usuarios de todos los clientes.
    - page: Número de página a mostrar (comienza en 1)
    - limit: Número máximo de usuarios por página (1-100)
    - search: Término opcional para buscar en nombre, apellido, correo o nombre_usuario
    - es_activo: Filtrar por estado activo/inactivo
    - proveedor_autenticacion: Filtrar por método de autenticación
    - ordenar_por: Campo para ordenar (fecha_creacion, fecha_ultimo_acceso, nombre_usuario)
    - orden: 'asc' o 'desc' (default: 'desc')
    
    **Respuestas:**
    - 200: Lista paginada recuperada exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 422: Parámetros de consulta inválidos
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def list_usuarios_global(
    current_user = Depends(get_current_active_user),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente específico (opcional)"),
    page: int = Query(1, ge=1, description="Número de página a mostrar"),
    limit: int = Query(20, ge=1, le=100, description="Número de usuarios por página"),
    search: Optional[str] = Query(None, min_length=1, max_length=50, 
                                 description="Término de búsqueda opcional"),
    es_activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    proveedor_autenticacion: Optional[str] = Query(None, description="Filtrar por método de autenticación"),
    ordenar_por: str = Query("fecha_creacion", description="Campo para ordenar"),
    orden: str = Query("desc", description="Orden: 'asc' o 'desc'")
):
    """
    Endpoint para obtener una lista paginada de usuarios de todos los clientes (Superadmin).
    """
    logger.info(
        f"Superadmin {current_user.usuario_id} solicitando listado global de usuarios - "
        f"cliente_id: {cliente_id}, page: {page}, limit: {limit}"
    )
    
    try:
        paginated_data = await SuperadminUsuarioService.get_usuarios_globales(
            cliente_id=cliente_id,
            page=page,
            limit=limit,
            search=search,
            es_activo=es_activo,
            proveedor_autenticacion=proveedor_autenticacion,
            ordenar_por=ordenar_por,
            orden=orden
        )
        
        logger.info(
            f"Listado global de usuarios recuperado - "
            f"Total: {paginated_data['total_usuarios']}, "
            f"Página: {paginated_data['pagina_actual']}"
        )
        return paginated_data
        
    except CustomException as ce:
        logger.warning(f"Error de negocio al listar usuarios globales: {ce.detail}")
        raise HTTPException(
            status_code=ce.status_code, 
            detail=ce.detail
        )
    except Exception as e:
        logger.exception("Error inesperado en endpoint GET /superadmin/usuarios/")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la lista de usuarios."
        )


@router.get(
    "/{usuario_id}/",
    response_model=UsuarioSuperadminRead,
    summary="Obtener detalle de usuario (Superadmin)",
    description="""
    Recupera los detalles completos de un usuario específico (Superadmin puede ver usuarios de cualquier cliente).
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - usuario_id: ID numérico del usuario a consultar
    
    **Parámetros de consulta:**
    - cliente_id (opcional): Filtrar por cliente específico. Si se proporciona, consulta directamente en la BD de ese tenant.
    
    **Respuestas:**
    - 200: Usuario encontrado y devuelto
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Usuario no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def read_usuario_superadmin(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    cliente_id: Optional[UUID] = Query(None, description="Filtrar por cliente específico (opcional)"),
    current_user = Depends(get_current_active_user)
):
    """
    Endpoint para obtener los detalles completos de un usuario específico (Superadmin).
    """
    logger.debug(f"Superadmin {current_user.usuario_id} solicitando usuario ID {usuario_id}, cliente_id: {cliente_id}")
    
    try:
        usuario = await SuperadminUsuarioService.obtener_usuario_completo(usuario_id, cliente_id=cliente_id)
        
        if usuario is None:
            logger.warning(f"Usuario con ID {usuario_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {usuario_id} no encontrado."
            )

        logger.debug(f"Usuario ID {usuario_id} encontrado: '{usuario['nombre_usuario']}'")
        return usuario
        
    except HTTPException:
        raise
    except CustomException as ce:
        logger.error(f"Error de negocio obteniendo usuario {usuario_id}: {ce.detail}")
        raise HTTPException(
            status_code=ce.status_code, 
            detail=ce.detail
        )
    except Exception as e:
        logger.exception(f"Error inesperado obteniendo usuario {usuario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al recuperar el usuario solicitado."
        )


@router.get(
    "/{usuario_id}/actividad/",
    response_model=UsuarioActividadResponse,
    summary="Obtener actividad de usuario (Superadmin)",
    description="""
    Recupera la actividad reciente de un usuario específico.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - usuario_id: ID numérico del usuario
    
    **Parámetros de query:**
    - cliente_id (opcional): Filtrar por cliente específico. Si se proporciona, consulta directamente en la BD de ese tenant.
    - limite: Número de eventos a retornar (1-200, default: 50)
    - tipo_evento: Filtrar por tipo de evento (opcional)
    
    **Respuestas:**
    - 200: Actividad recuperada exitosamente
    - 403: Acceso denegado
    - 404: Usuario no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def read_usuario_actividad(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    cliente_id: Optional[UUID] = Query(None, description="Filtrar por cliente específico (opcional)"),
    current_user = Depends(get_current_active_user),
    limite: int = Query(50, ge=1, le=200, description="Número de eventos a retornar"),
    tipo_evento: Optional[str] = Query(None, description="Filtrar por tipo de evento")
):
    """
    Endpoint para obtener la actividad reciente de un usuario.
    """
    logger.debug(f"Superadmin {current_user.usuario_id} solicitando actividad de usuario ID {usuario_id}, cliente_id: {cliente_id}")
    
    try:
        actividad = await SuperadminUsuarioService.obtener_actividad_usuario(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            limite=limite,
            tipo_evento=tipo_evento
        )
        
        logger.debug(f"Actividad del usuario {usuario_id} recuperada - Total eventos: {actividad['total_eventos']}")
        return actividad
        
    except HTTPException:
        raise
    except CustomException as ce:
        logger.error(f"Error de negocio obteniendo actividad de usuario {usuario_id}: {ce.detail}")
        raise HTTPException(
            status_code=ce.status_code, 
            detail=ce.detail
        )
    except Exception as e:
        logger.exception(f"Error inesperado obteniendo actividad de usuario {usuario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la actividad del usuario."
        )


@router.get(
    "/{usuario_id}/sesiones/",
    response_model=UsuarioSesionesResponse,
    summary="Obtener sesiones de usuario (Superadmin)",
    description="""
    Recupera las sesiones activas de un usuario específico.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - usuario_id: ID numérico del usuario
    
    **Parámetros de query:**
    - cliente_id (opcional): Filtrar por cliente específico. Si se proporciona, consulta directamente en la BD de ese tenant.
    - solo_activas: Si solo mostrar sesiones activas (default: true)
    
    **Respuestas:**
    - 200: Sesiones recuperadas exitosamente
    - 403: Acceso denegado
    - 404: Usuario no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def read_usuario_sesiones(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    cliente_id: Optional[UUID] = Query(None, description="Filtrar por cliente específico (opcional)"),
    current_user = Depends(get_current_active_user),
    solo_activas: bool = Query(True, description="Solo mostrar sesiones activas")
):
    """
    Endpoint para obtener las sesiones de un usuario.
    """
    logger.debug(f"Superadmin {current_user.usuario_id} solicitando sesiones de usuario ID {usuario_id}, cliente_id: {cliente_id}")
    
    try:
        sesiones = await SuperadminUsuarioService.obtener_sesiones_usuario(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            solo_activas=solo_activas
        )
        
        logger.debug(
            f"Sesiones del usuario {usuario_id} recuperadas - "
            f"Total: {sesiones['total_sesiones']}, "
            f"Activas: {sesiones['sesiones_activas']}"
        )
        return sesiones
        
    except HTTPException:
        raise
    except CustomException as ce:
        logger.error(f"Error de negocio obteniendo sesiones de usuario {usuario_id}: {ce.detail}")
        raise HTTPException(
            status_code=ce.status_code, 
            detail=ce.detail
        )
    except Exception as e:
        logger.exception(f"Error inesperado obteniendo sesiones de usuario {usuario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener las sesiones del usuario."
        )


@router.get(
    "/clientes/{cliente_id}/usuarios/",
    response_model=PaginatedUsuarioSuperadminResponse,
    summary="Listar usuarios de un cliente específico (Superadmin)",
    description="""
    Recupera una lista paginada de usuarios de un cliente específico.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Parámetros de consulta:**
    - page: Número de página a mostrar
    - limit: Número máximo de usuarios por página
    - search: Término opcional para buscar
    - es_activo: Filtrar por estado activo/inactivo
    
    **Respuestas:**
    - 200: Lista paginada recuperada exitosamente
    - 403: Acceso denegado
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def list_usuarios_por_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="Número de página a mostrar"),
    limit: int = Query(20, ge=1, le=100, description="Número de usuarios por página"),
    search: Optional[str] = Query(None, min_length=1, max_length=50, 
                                 description="Término de búsqueda opcional"),
    es_activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo")
):
    """
    Endpoint para obtener una lista paginada de usuarios de un cliente específico.
    """
    logger.info(
        f"Superadmin {current_user.usuario_id} solicitando usuarios del cliente {cliente_id} - "
        f"page: {page}, limit: {limit}"
    )
    
    try:
        paginated_data = await SuperadminUsuarioService.get_usuarios_globales(
            cliente_id=cliente_id,
            page=page,
            limit=limit,
            search=search,
            es_activo=es_activo
        )
        
        logger.info(
            f"Usuarios del cliente {cliente_id} recuperados - "
            f"Total: {paginated_data['total_usuarios']}, "
            f"Página: {paginated_data['pagina_actual']}"
        )
        return paginated_data
        
    except HTTPException:
        raise
    except CustomException as ce:
        logger.warning(f"Error de negocio al listar usuarios del cliente {cliente_id}: {ce.detail}")
        raise HTTPException(
            status_code=ce.status_code, 
            detail=ce.detail
        )
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint GET /superadmin/usuarios/clientes/{cliente_id}/usuarios/")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la lista de usuarios."
        )


