# app/modules/tenant/application/services/modulo_activo_service.py
"""
Servicio para la gestión de activación de módulos por cliente en arquitectura multi-tenant.
Este servicio implementa la lógica de negocio para operaciones sobre la entidad `cliente_modulo_activo`,
incluyendo la activación, desactivación y configuración de módulos específicos por cliente.

Características clave:
- Gestión del ciclo de vida de activación de módulos por cliente
- Validación de límites y configuraciones específicas
- Soporte para módulos con licencia y límites de uso
- Configuración personalizada por módulo y cliente
- Estadísticas de uso de módulos
- Total coherencia con los patrones de BaseService y manejo de excepciones del sistema
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
from app.infrastructure.database.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.core.application.base_service import BaseService
from app.modules.tenant.presentation.schemas import (
    ModuloActivoCreate,
    ModuloActivoUpdate,
    ModuloActivoRead,
    ModuloActivoConEstadisticas,
)
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ModuloActivoService(BaseService):
    """
    Servicio central para la administración de activación de módulos por cliente.
    """
    
    @staticmethod
    def _deserializar_configuracion_json(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper para deserializar configuracion_json de string a Dict.
        La BD almacena JSON como string, pero el schema espera Dict[str, Any].
        """
        if 'configuracion_json' in row and row['configuracion_json']:
            try:
                if isinstance(row['configuracion_json'], str):
                    row['configuracion_json'] = json.loads(row['configuracion_json'])
                # Si ya es dict, no hacer nada
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error deserializando configuracion_json: {e}. Usando None.")
                row['configuracion_json'] = None
        return row

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
        # Deserializar configuracion_json de string a Dict antes de crear objetos
        modulos_deserializados = [ModuloActivoService._deserializar_configuracion_json(dict(modulo)) for modulo in resultados]
        return [ModuloActivoRead(**modulo) for modulo in modulos_deserializados]

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
        # Deserializar configuracion_json de string a Dict antes de crear objeto
        modulo_deserializado = ModuloActivoService._deserializar_configuracion_json(dict(resultado[0]))
        return ModuloActivoRead(**modulo_deserializado)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_activo_por_cliente_y_modulo(
        cliente_id: int, 
        modulo_id: int
    ) -> Optional[ModuloActivoRead]:
        """
        Obtiene un módulo activo específico por cliente y módulo.
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
        # Deserializar configuracion_json de string a Dict antes de crear objeto
        modulo_deserializado = ModuloActivoService._deserializar_configuracion_json(dict(resultado[0]))
        return ModuloActivoRead(**modulo_deserializado)

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_modulo_activo_unico(
        cliente_id: int, 
        modulo_id: int, 
        modulo_activo_id: Optional[int] = None
    ) -> None:
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
    async def activar_modulo(modulo_data: ModuloActivoCreate) -> ModuloActivoRead:
        """
        Activa un módulo para un cliente específico.
        
        LÓGICA CORREGIDA:
        - Si el registro NO existe: INSERT
        - Si el registro YA existe (activo o inactivo): UPDATE de esta_activo = 1 y otros campos
        """
        logger.info(f"Activando módulo {modulo_data.modulo_id} para cliente {modulo_data.cliente_id}")

        # Validar que el módulo no esté ya activado (solo si está activo)
        await ModuloActivoService._validar_modulo_activo_unico(
            modulo_data.cliente_id, 
            modulo_data.modulo_id
        )

        # Validar que el módulo existe
        from app.modules.tenant.application.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(modulo_data.modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_data.modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar que el cliente existe
        from app.modules.tenant.application.services.cliente_service import ClienteService
        cliente = await ClienteService.obtener_cliente_por_id(modulo_data.cliente_id)
        if not cliente:
            raise NotFoundError(
                detail=f"Cliente con ID {modulo_data.cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )

        # Validar fecha de vencimiento si se proporciona
        if modulo_data.fecha_vencimiento:
            if modulo_data.fecha_vencimiento <= datetime.now():
                raise ValidationError(
                    detail="La fecha de vencimiento debe ser futura.",
                    internal_code="INVALID_EXPIRATION_DATE"
                )

        # ✅ CORRECCIÓN: Verificar si ya existe un registro (activo o inactivo)
        query_existe = """
        SELECT cliente_modulo_activo_id, esta_activo
        FROM cliente_modulo_activo
        WHERE cliente_id = ? AND modulo_id = ?
        """
        existe_raw = execute_query(query_existe, (modulo_data.cliente_id, modulo_data.modulo_id), connection_type=DatabaseConnection.ADMIN)
        
        # Preparar datos
        configuracion_json = json.dumps(modulo_data.configuracion_json) if modulo_data.configuracion_json else None

        if existe_raw:
            # ✅ El registro ya existe: hacer UPDATE
            modulo_activo_id = existe_raw[0]['cliente_modulo_activo_id']
            logger.info(f"[ACTIVAR] Registro existente encontrado (ID: {modulo_activo_id}), actualizando a activo")
            
            query_update = """
            UPDATE cliente_modulo_activo
            SET esta_activo = 1,
                fecha_vencimiento = ?,
                configuracion_json = ?,
                limite_usuarios = ?,
                limite_registros = ?
            WHERE cliente_modulo_activo_id = ?
            """
            
            params_update = [
                modulo_data.fecha_vencimiento,
                configuracion_json,
                modulo_data.limite_usuarios,
                modulo_data.limite_registros,
                modulo_activo_id
            ]
            
            # Ejecutar UPDATE
            resultado_update = execute_update(query_update, tuple(params_update), connection_type=DatabaseConnection.ADMIN)
            
            if resultado_update.get('rows_affected', 0) == 0:
                raise ServiceError(
                    status_code=500,
                    detail="No se pudo activar el módulo para el cliente.",
                    internal_code="MODULE_ACTIVATION_FAILED"
                )
            
            logger.info(f"[ACTIVAR] Módulo reactivado exitosamente (ID: {modulo_activo_id})")
            modulo_activo_id_resultado = modulo_activo_id
        else:
            # ✅ El registro NO existe: hacer INSERT
            logger.info(f"[ACTIVAR] Registro no existe, creando nuevo registro")
            
            fields = [
                'cliente_id', 'modulo_id', 'esta_activo',
                'fecha_vencimiento', 'configuracion_json', 'limite_usuarios', 'limite_registros'
            ]
            
            params = [
                modulo_data.cliente_id,
                modulo_data.modulo_id,
                1,  # esta_activo
                modulo_data.fecha_vencimiento,
                configuracion_json,
                modulo_data.limite_usuarios,
                modulo_data.limite_registros
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

            resultado = execute_insert(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
            if not resultado:
                raise ServiceError(
                    status_code=500,
                    detail="No se pudo activar el módulo para el cliente.",
                    internal_code="MODULE_ACTIVATION_FAILED"
                )
            
            logger.info(f"[ACTIVAR] Módulo activado exitosamente con ID: {resultado['cliente_modulo_activo_id']}")
            modulo_activo_id_resultado = resultado['cliente_modulo_activo_id']
        
        # Obtener el módulo activo completo con información del módulo
        return await ModuloActivoService.obtener_modulo_activo_por_id(modulo_activo_id_resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_modulo_activo(
        modulo_activo_id: int, 
        modulo_data: ModuloActivoUpdate
    ) -> ModuloActivoRead:
        """
        Actualiza la configuración de un módulo activo.
        """
        logger.info(f"Actualizando módulo activo ID: {modulo_activo_id}")

        # Verificar que el módulo activo existe
        modulo_existente = await ModuloActivoService.obtener_modulo_activo_por_id(modulo_activo_id)
        if not modulo_existente:
            raise NotFoundError(
                detail=f"Módulo activo con ID {modulo_activo_id} no encontrado.",
                internal_code="ACTIVE_MODULE_NOT_FOUND"
            )

        # Validar fecha de vencimiento si se proporciona
        if modulo_data.fecha_vencimiento:
            if modulo_data.fecha_vencimiento <= datetime.now():
                raise ValidationError(
                    detail="La fecha de vencimiento debe ser futura.",
                    internal_code="INVALID_EXPIRATION_DATE"
                )

        # Construir query dinámica basada en los campos proporcionados
        update_fields = []
        params = []
        
        for field, value in modulo_data.dict(exclude_unset=True).items():
            if value is not None:
                if field == "configuracion_json":
                    update_fields.append("configuracion_json = ?")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
                
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
                detail="No se pudo actualizar el módulo activo.",
                internal_code="ACTIVE_MODULE_UPDATE_FAILED"
            )

        logger.info(f"Módulo activo ID {modulo_activo_id} actualizado exitosamente.")
        
        # Obtener el módulo activo completo con información del módulo
        return await ModuloActivoService.obtener_modulo_activo_por_id(modulo_activo_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_modulo(modulo_activo_id: int) -> bool:
        """
        Desactiva un módulo para un cliente.
        Implementa desactivación lógica (soft delete).
        """
        logger.info(f"Desactivando módulo activo ID: {modulo_activo_id}")

        # Verificar que el módulo activo existe
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_por_id(modulo_activo_id)
        if not modulo_activo:
            raise NotFoundError(
                detail=f"Módulo activo con ID {modulo_activo_id} no encontrado.",
                internal_code="ACTIVE_MODULE_NOT_FOUND"
            )

        # Validar que no sea un módulo core (opcional, depende de reglas de negocio)
        from app.modules.tenant.application.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(modulo_activo.modulo_id)
        if modulo and modulo.es_modulo_core:
            raise ValidationError(
                detail="No se puede desactivar un módulo core.",
                internal_code="CANNOT_DEACTIVATE_CORE_MODULE"
            )

        # Realizar desactivación lógica
        query = """
        UPDATE cliente_modulo_activo
        SET esta_activo = 0
        WHERE cliente_modulo_activo_id = ?
        """
        
        execute_update(query, (modulo_activo_id,), connection_type=DatabaseConnection.ADMIN)
        logger.info(f"Módulo activo ID {modulo_activo_id} desactivado exitosamente.")
        return True

    @staticmethod
    @BaseService.handle_service_errors
    async def verificar_limites_modulo(
        cliente_id: int, 
        modulo_id: int
    ) -> Dict[str, Any]:
        """
        Verifica los límites de uso de un módulo para un cliente.
        Retorna información sobre el uso actual vs límites configurados.
        
        NOTA: Esta es una implementación base. En producción, se debería
        integrar con sistemas de telemetría reales para obtener datos precisos.
        """
        logger.info(f"Verificando límites para módulo {modulo_id} del cliente {cliente_id}")

        # Obtener configuración del módulo activo
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        
        if not modulo_activo:
            raise NotFoundError(
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}.",
                internal_code="MODULE_NOT_ACTIVE"
            )

        # TODO: Integrar con sistema de telemetría real
        # Por ahora, retornamos datos simulados
        return {
            "modulo_id": modulo_id,
            "cliente_id": cliente_id,
            "limite_usuarios": modulo_activo.limite_usuarios,
            "usuarios_actuales": 0,  # TODO: Obtener de telemetría
            "limite_registros": modulo_activo.limite_registros,
            "registros_actuales": 0,  # TODO: Obtener de telemetría
            "dentro_limites": True,
            "fecha_vencimiento": modulo_activo.fecha_vencimiento,
            "esta_vencido": modulo_activo.fecha_vencimiento < datetime.now() if modulo_activo.fecha_vencimiento else False
        }

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_estadisticas_modulo_activo(
        cliente_id: int, 
        modulo_id: int
    ) -> ModuloActivoConEstadisticas:
        """
        Obtiene estadísticas completas de uso de un módulo para un cliente.
        Incluye información de activación, límites y uso actual.
        
        NOTA: Esta es una implementación base. En producción, se debería
        integrar con sistemas de telemetría reales para obtener datos precisos.
        """
        logger.info(f"Obteniendo estadísticas para módulo {modulo_id} del cliente {cliente_id}")

        # Obtener módulo activo
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        
        if not modulo_activo:
            raise NotFoundError(
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}.",
                internal_code="MODULE_NOT_ACTIVE"
            )

        # Verificar límites
        limites = await ModuloActivoService.verificar_limites_modulo(cliente_id, modulo_id)

        # Construir respuesta con estadísticas
        # TODO: Integrar con sistema de telemetría real
        estadisticas = {
            **modulo_activo.dict(),
            "usuarios_actuales": limites["usuarios_actuales"],
            "registros_actuales": limites["registros_actuales"],
            "dentro_limites": limites["dentro_limites"],
            "esta_vencido": limites["esta_vencido"],
            "dias_restantes": (modulo_activo.fecha_vencimiento - datetime.now()).days if modulo_activo.fecha_vencimiento else None
        }

        return ModuloActivoConEstadisticas(**estadisticas)

