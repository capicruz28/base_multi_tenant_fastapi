# app/services/modulo_activo_service.py
"""
Servicio para la gestión de activación de módulos por cliente en arquitectura multi-tenant.
Este servicio implementa la lógica de negocio para operaciones sobre la entidad `cliente_modulo_activo`,
incluyendo la activación, desactivación y configuración de módulos específicos por cliente.

Características clave:
- Gestión del ciclo de vida de activación de módulos por cliente
- Validación de límites y configuraciones específicas
- Soporte para módulos con licencia y límites de uso
- Configuración personalizada por módulo y cliente
- Total coherencia con los patrones de BaseService y manejo de excepciones del sistema
"""
from typing import List, Optional, Dict, Any
import json
import logging
from app.db.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.services.base_service import BaseService
from app.schemas.modulo_activo import ModuloActivoCreate, ModuloActivoUpdate, ModuloActivoRead
from app.db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ModuloActivoService(BaseService):
    """
    Servicio central para la administración de activación de módulos por cliente.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos_activos_cliente(cliente_id: int) -> List[ModuloActivoRead]:
        """
        Obtiene todos los módulos activos para un cliente específico.
        """
        logger.info(f"Obteniendo módulos activos para cliente ID: {cliente_id}")

        query = """
        SELECT 
            cma.cliente_modulo_activo_id,
            cma.cliente_id,
            cma.modulo_id,
            cma.esta_activo,
            cma.fecha_activacion,
            cma.fecha_vencimiento,
            cma.configuracion_json,
            cma.limite_usuarios,
            cma.limite_registros,
            cm.nombre as modulo_nombre,
            cm.codigo_modulo,
            cm.descripcion as modulo_descripcion
        FROM cliente_modulo_activo cma
        INNER JOIN cliente_modulo cm ON cma.modulo_id = cm.modulo_id
        WHERE cma.cliente_id = ? AND cma.esta_activo = 1
        ORDER BY cm.orden, cm.nombre
        """
        
        resultados = execute_query(query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        return [ModuloActivoRead(**modulo) for modulo in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_activo_por_id(modulo_activo_id: int) -> Optional[ModuloActivoRead]:
        """
        Obtiene un módulo activo específico por su ID.
        """
        query = """
        SELECT 
            cma.cliente_modulo_activo_id,
            cma.cliente_id,
            cma.modulo_id,
            cma.esta_activo,
            cma.fecha_activacion,
            cma.fecha_vencimiento,
            cma.configuracion_json,
            cma.limite_usuarios,
            cma.limite_registros,
            cm.nombre as modulo_nombre,
            cm.codigo_modulo,
            cm.descripcion as modulo_descripcion
        FROM cliente_modulo_activo cma
        INNER JOIN cliente_modulo cm ON cma.modulo_id = cm.modulo_id
        WHERE cma.cliente_modulo_activo_id = ?
        """
        
        resultado = execute_query(query, (modulo_activo_id,), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            return None
        return ModuloActivoRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_modulo_activo_unico(cliente_id: int, modulo_id: int, modulo_activo_id: Optional[int] = None) -> None:
        """
        Valida que un módulo no esté ya activado para el cliente.
        """
        query = """
        SELECT cliente_modulo_activo_id FROM cliente_modulo_activo 
        WHERE cliente_id = ? AND modulo_id = ? AND esta_activo = 1
        """
        params = [cliente_id, modulo_id]
        
        if modulo_activo_id:
            query += " AND cliente_modulo_activo_id != ?"
            params.append(modulo_activo_id)
            
        resultado = execute_query(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if resultado:
            raise ConflictError(
                detail="El módulo ya está activado para este cliente.",
                internal_code="MODULE_ALREADY_ACTIVE"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def activar_modulo_cliente(
        cliente_id: int, 
        modulo_id: int, 
        configuracion: Optional[Dict[str, Any]] = None,
        limite_usuarios: Optional[int] = None,
        limite_registros: Optional[int] = None,
        fecha_vencimiento: Optional[str] = None
    ) -> ModuloActivoRead:
        """
        Activa un módulo para un cliente específico.
        """
        logger.info(f"Activando módulo {modulo_id} para cliente {cliente_id}")

        # Validar que el módulo no esté ya activado
        await ModuloActivoService._validar_modulo_activo_unico(cliente_id, modulo_id)

        # Validar que el módulo existe
        from app.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar que el cliente existe
        from app.services.cliente_service import ClienteService
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )

        # Preparar datos para inserción
        configuracion_json = json.dumps(configuracion) if configuracion else None

        fields = [
            'cliente_id', 'modulo_id', 'esta_activo', 'fecha_activacion',
            'fecha_vencimiento', 'configuracion_json', 'limite_usuarios', 'limite_registros'
        ]
        
        params = [
            cliente_id,
            modulo_id,
            1,  # esta_activo
            'GETDATE()',  # fecha_activacion
            fecha_vencimiento,
            configuracion_json,
            limite_usuarios,
            limite_registros
        ]

        query = f"""
        INSERT INTO cliente_modulo_activo ({', '.join(fields)})
        OUTPUT 
            INSERTED.cliente_modulo_activo_id,
            INSERTED.cliente_id,
            INSERTED.modulo_id,
            INSERTED.esta_activo,
            INSERTED.fecha_activacion,
            INSERTED.fecha_vencimiento,
            INSERTED.configuracion_json,
            INSERTED.limite_usuarios,
            INSERTED.limite_registros
        VALUES ({', '.join(['?'] * len(fields))})
        """

        # Reemplazar GETDATE() para SQL Server
        query = query.replace("'GETDATE()'", "GETDATE()")

        resultado = execute_insert(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo activar el módulo para el cliente.",
                internal_code="MODULE_ACTIVATION_FAILED"
            )

        logger.info(f"Módulo {modulo_id} activado exitosamente para cliente {cliente_id}")
        
        # Obtener el registro completo con información del módulo
        return await ModuloActivoService.obtener_modulo_activo_por_id(resultado['cliente_modulo_activo_id'])

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_modulo_cliente(cliente_id: int, modulo_id: int) -> bool:
        """
        Desactiva un módulo para un cliente específico.
        """
        logger.info(f"Desactivando módulo {modulo_id} para cliente {cliente_id}")

        # Verificar que el módulo está activo para el cliente
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_cliente(cliente_id, modulo_id)
        if not modulo_activo:
            raise NotFoundError(
                detail=f"El módulo {modulo_id} no está activo para el cliente {cliente_id}.",
                internal_code="MODULE_NOT_ACTIVE"
            )

        query = """
        UPDATE cliente_modulo_activo
        SET esta_activo = 0
        WHERE cliente_id = ? AND modulo_id = ? AND esta_activo = 1
        """

        filas_afectadas = execute_update(query, (cliente_id, modulo_id), connection_type=DatabaseConnection.ADMIN)
        
        if filas_afectadas > 0:
            logger.info(f"Módulo {modulo_id} desactivado exitosamente para cliente {cliente_id}")
            return True
        else:
            raise ServiceError(
                status_code=500,
                detail="No se pudo desactivar el módulo.",
                internal_code="MODULE_DEACTIVATION_FAILED"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_config_modulo(
        modulo_activo_id: int, 
        configuracion: Optional[Dict[str, Any]] = None,
        limite_usuarios: Optional[int] = None,
        limite_registros: Optional[int] = None,
        fecha_vencimiento: Optional[str] = None
    ) -> ModuloActivoRead:
        """
        Actualiza la configuración de un módulo activo para un cliente.
        """
        logger.info(f"Actualizando configuración del módulo activo ID: {modulo_activo_id}")

        # Verificar que el módulo activo existe
        modulo_activo_existente = await ModuloActivoService.obtener_modulo_activo_por_id(modulo_activo_id)
        if not modulo_activo_existente:
            raise NotFoundError(
                detail=f"Módulo activo con ID {modulo_activo_id} no encontrado.",
                internal_code="ACTIVE_MODULE_NOT_FOUND"
            )

        # Construir query dinámica
        update_fields = []
        params = []
        
        if configuracion is not None:
            update_fields.append("configuracion_json = ?")
            params.append(json.dumps(configuracion))
            
        if limite_usuarios is not None:
            update_fields.append("limite_usuarios = ?")
            params.append(limite_usuarios)
            
        if limite_registros is not None:
            update_fields.append("limite_registros = ?")
            params.append(limite_registros)
            
        if fecha_vencimiento is not None:
            update_fields.append("fecha_vencimiento = ?")
            params.append(fecha_vencimiento)
                
        if not update_fields:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )
            
        params.append(modulo_activo_id)

        query = f"""
        UPDATE cliente_modulo_activo
        SET {', '.join(update_fields)}
        OUTPUT 
            INSERTED.cliente_modulo_activo_id,
            INSERTED.cliente_id,
            INSERTED.modulo_id,
            INSERTED.esta_activo,
            INSERTED.fecha_activacion,
            INSERTED.fecha_vencimiento,
            INSERTED.configuracion_json,
            INSERTED.limite_usuarios,
            INSERTED.limite_registros
        WHERE cliente_modulo_activo_id = ?
        """

        resultado = execute_update(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar la configuración del módulo.",
                internal_code="MODULE_CONFIG_UPDATE_FAILED"
            )

        logger.info(f"Configuración del módulo activo ID {modulo_activo_id} actualizada exitosamente.")
        
        # Obtener el registro completo actualizado
        return await ModuloActivoService.obtener_modulo_activo_por_id(modulo_activo_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_activo_cliente(cliente_id: int, modulo_id: int) -> Optional[ModuloActivoRead]:
        """
        Obtiene un módulo activo específico para un cliente y módulo.
        """
        query = """
        SELECT 
            cma.cliente_modulo_activo_id,
            cma.cliente_id,
            cma.modulo_id,
            cma.esta_activo,
            cma.fecha_activacion,
            cma.fecha_vencimiento,
            cma.configuracion_json,
            cma.limite_usuarios,
            cma.limite_registros,
            cm.nombre as modulo_nombre,
            cm.codigo_modulo,
            cm.descripcion as modulo_descripcion
        FROM cliente_modulo_activo cma
        INNER JOIN cliente_modulo cm ON cma.modulo_id = cm.modulo_id
        WHERE cma.cliente_id = ? AND cma.modulo_id = ? AND cma.esta_activo = 1
        """
        
        resultado = execute_query(query, (cliente_id, modulo_id), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            return None
        return ModuloActivoRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def verificar_limites_modulo(cliente_id: int, modulo_id: int) -> Dict[str, Any]:
        """
        Verifica los límites de uso de un módulo activo para un cliente.
        """
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_cliente(cliente_id, modulo_id)
        if not modulo_activo:
            return {
                "activo": False,
                "mensaje": "Módulo no activo para este cliente"
            }

        # Aquí iría la lógica para verificar límites reales contra uso actual
        # Por ahora retornamos estado básico
        return {
            "activo": True,
            "limite_usuarios": modulo_activo.limite_usuarios,
            "limite_registros": modulo_activo.limite_registros,
            "fecha_vencimiento": modulo_activo.fecha_vencimiento,
            "dentro_limites": True  # Simulación
        }