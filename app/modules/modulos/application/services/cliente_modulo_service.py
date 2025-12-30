# app/modules/modulos/application/services/cliente_modulo_service.py
"""
Servicio para la gestión de activación de módulos por cliente.

Este servicio implementa la lógica de negocio para operaciones sobre la entidad `cliente_modulo`,
incluyendo la activación, desactivación y configuración de módulos específicos por cliente.

⚠️ CRÍTICO: Al activar un módulo, aplica automáticamente las plantillas de roles.

Características clave:
- Gestión del ciclo de vida de activación de módulos por cliente
- Validación de dependencias entre módulos
- Aplicación automática de plantillas de roles al activar
- Validación de límites y configuraciones específicas
- Soporte para módulos con licencia y límites de uso
- Configuración personalizada por módulo y cliente
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json
from sqlalchemy import select, update, delete, and_, func as sql_func
from uuid import UUID

from app.infrastructure.database.tables_modulos import ClienteModuloTable, ModuloTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.core.application.base_service import BaseService
from app.modules.modulos.presentation.schemas import (
    ClienteModuloCreate, ClienteModuloUpdate, ClienteModuloRead
)
from app.modules.modulos.application.helpers.rol_plantilla_applier import aplicar_plantillas_roles
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)


class ClienteModuloService(BaseService):
    """
    Servicio central para la administración de activación de módulos por cliente.
    """
    
    @staticmethod
    def _deserializar_configuracion_json(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper para deserializar configuracion_json de string a Dict.
        """
        if 'configuracion_json' in row and row['configuracion_json']:
            try:
                if isinstance(row['configuracion_json'], str):
                    row['configuracion_json'] = json.loads(row['configuracion_json'])
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error deserializando configuracion_json: {e}. Usando None.")
                row['configuracion_json'] = None
        return row

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos_activos_cliente(cliente_id: UUID) -> List[ClienteModuloRead]:
        """
        Obtiene todos los módulos activos para un cliente específico.
        """
        logger.info(f"Obteniendo módulos activos para cliente ID: {cliente_id}")

        query = select(
            ClienteModuloTable,
            ModuloTable.c.nombre.label('modulo_nombre'),
            ModuloTable.c.codigo.label('modulo_codigo')
        ).select_from(
            ClienteModuloTable.join(ModuloTable, ClienteModuloTable.c.modulo_id == ModuloTable.c.modulo_id)
        ).where(
            and_(
                ClienteModuloTable.c.cliente_id == cliente_id,
                ClienteModuloTable.c.esta_activo == True
            )
        ).order_by(ModuloTable.c.orden, ModuloTable.c.nombre)
        
        resultados = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        
        # Deserializar configuracion_json y construir objetos
        modulos_deserializados = [
            ClienteModuloService._deserializar_configuracion_json(dict(modulo)) 
            for modulo in resultados
        ]
        
        # Construir objetos ClienteModuloRead con información del módulo
        modulos_list = []
        for modulo_data in modulos_deserializados:
            # Separar campos de ClienteModuloTable y ModuloTable
            cliente_modulo_data = {
                'cliente_modulo_id': modulo_data['cliente_modulo_id'],
                'cliente_id': modulo_data['cliente_id'],
                'modulo_id': modulo_data['modulo_id'],
                'esta_activo': modulo_data['esta_activo'],
                'fecha_activacion': modulo_data['fecha_activacion'],
                'fecha_vencimiento': modulo_data.get('fecha_vencimiento'),
                'modo_prueba': modulo_data.get('modo_prueba', False),
                'fecha_fin_prueba': modulo_data.get('fecha_fin_prueba'),
                'configuracion_json': modulo_data.get('configuracion_json'),
                'limite_usuarios': modulo_data.get('limite_usuarios'),
                'limite_registros': modulo_data.get('limite_registros'),
                'limite_transacciones_mes': modulo_data.get('limite_transacciones_mes'),
                'fecha_creacion': modulo_data['fecha_creacion'],
                'fecha_actualizacion': modulo_data.get('fecha_actualizacion'),
                'activado_por_usuario_id': modulo_data.get('activado_por_usuario_id'),
                'modulo_nombre': modulo_data.get('modulo_nombre'),
                'modulo_codigo': modulo_data.get('modulo_codigo')
            }
            modulos_list.append(ClienteModuloRead(**cliente_modulo_data))
        
        return modulos_list

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_activo_por_id(cliente_modulo_id: UUID) -> Optional[ClienteModuloRead]:
        """
        Obtiene un módulo activo específico por su ID.
        """
        query = select(
            ClienteModuloTable,
            ModuloTable.c.nombre.label('modulo_nombre'),
            ModuloTable.c.codigo.label('modulo_codigo')
        ).select_from(
            ClienteModuloTable.join(ModuloTable, ClienteModuloTable.c.modulo_id == ModuloTable.c.modulo_id)
        ).where(ClienteModuloTable.c.cliente_modulo_id == cliente_modulo_id)
        
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            return None
        
        modulo_deserializado = ClienteModuloService._deserializar_configuracion_json(dict(resultado[0]))
        cliente_modulo_data = {
            'cliente_modulo_id': modulo_deserializado['cliente_modulo_id'],
            'cliente_id': modulo_deserializado['cliente_id'],
            'modulo_id': modulo_deserializado['modulo_id'],
            'esta_activo': modulo_deserializado['esta_activo'],
            'fecha_activacion': modulo_deserializado['fecha_activacion'],
            'fecha_vencimiento': modulo_deserializado.get('fecha_vencimiento'),
            'modo_prueba': modulo_deserializado.get('modo_prueba', False),
            'fecha_fin_prueba': modulo_deserializado.get('fecha_fin_prueba'),
            'configuracion_json': modulo_deserializado.get('configuracion_json'),
            'limite_usuarios': modulo_deserializado.get('limite_usuarios'),
            'limite_registros': modulo_deserializado.get('limite_registros'),
            'limite_transacciones_mes': modulo_deserializado.get('limite_transacciones_mes'),
            'fecha_creacion': modulo_deserializado['fecha_creacion'],
            'fecha_actualizacion': modulo_deserializado.get('fecha_actualizacion'),
            'activado_por_usuario_id': modulo_deserializado.get('activado_por_usuario_id'),
            'modulo_nombre': modulo_deserializado.get('modulo_nombre'),
            'modulo_codigo': modulo_deserializado.get('modulo_codigo')
        }
        return ClienteModuloRead(**cliente_modulo_data)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_activo_por_cliente_y_modulo(
        cliente_id: UUID, 
        modulo_id: UUID
    ) -> Optional[ClienteModuloRead]:
        """
        Obtiene un módulo activo específico por cliente y módulo.
        """
        query = select(
            ClienteModuloTable,
            ModuloTable.c.nombre.label('modulo_nombre'),
            ModuloTable.c.codigo.label('modulo_codigo')
        ).select_from(
            ClienteModuloTable.join(ModuloTable, ClienteModuloTable.c.modulo_id == ModuloTable.c.modulo_id)
        ).where(
            and_(
                ClienteModuloTable.c.cliente_id == cliente_id,
                ClienteModuloTable.c.modulo_id == modulo_id,
                ClienteModuloTable.c.esta_activo == True
            )
        )
        
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            return None
        
        modulo_deserializado = ClienteModuloService._deserializar_configuracion_json(dict(resultado[0]))
        cliente_modulo_data = {
            'cliente_modulo_id': modulo_deserializado['cliente_modulo_id'],
            'cliente_id': modulo_deserializado['cliente_id'],
            'modulo_id': modulo_deserializado['modulo_id'],
            'esta_activo': modulo_deserializado['esta_activo'],
            'fecha_activacion': modulo_deserializado['fecha_activacion'],
            'fecha_vencimiento': modulo_deserializado.get('fecha_vencimiento'),
            'modo_prueba': modulo_deserializado.get('modo_prueba', False),
            'fecha_fin_prueba': modulo_deserializado.get('fecha_fin_prueba'),
            'configuracion_json': modulo_deserializado.get('configuracion_json'),
            'limite_usuarios': modulo_deserializado.get('limite_usuarios'),
            'limite_registros': modulo_deserializado.get('limite_registros'),
            'limite_transacciones_mes': modulo_deserializado.get('limite_transacciones_mes'),
            'fecha_creacion': modulo_deserializado['fecha_creacion'],
            'fecha_actualizacion': modulo_deserializado.get('fecha_actualizacion'),
            'activado_por_usuario_id': modulo_deserializado.get('activado_por_usuario_id'),
            'modulo_nombre': modulo_deserializado.get('modulo_nombre'),
            'modulo_codigo': modulo_deserializado.get('modulo_codigo')
        }
        return ClienteModuloRead(**cliente_modulo_data)

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_modulo_activo_unico(
        cliente_id: UUID, 
        modulo_id: UUID, 
        cliente_modulo_id: Optional[UUID] = None
    ) -> None:
        """
        Valida que un módulo no esté ya activado para el cliente.
        """
        query = select(ClienteModuloTable.c.cliente_modulo_id).where(
            and_(
                ClienteModuloTable.c.cliente_id == cliente_id,
                ClienteModuloTable.c.modulo_id == modulo_id,
                ClienteModuloTable.c.esta_activo == True
            )
        )
        
        if cliente_modulo_id:
            query = query.where(ClienteModuloTable.c.cliente_modulo_id != cliente_modulo_id)
            
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if resultado:
            raise ConflictError(
                detail="El módulo ya está activado para este cliente.",
                internal_code="MODULE_ALREADY_ACTIVE"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def activar_modulo_cliente(modulo_data: ClienteModuloCreate) -> ClienteModuloRead:
        """
        Activa un módulo para un cliente específico.
        
        ⚠️ CRÍTICO: Aplica automáticamente las plantillas de roles del módulo.
        
        Lógica:
        1. Validar que el módulo existe y está activo
        2. Validar dependencias (módulos requeridos ya activos)
        3. Validar que no esté ya activado
        4. Insertar o actualizar registro en cliente_modulo
        5. **APLICAR PLANTILLAS DE ROLES AUTOMÁTICAMENTE**
        """
        logger.info(f"Activando módulo {modulo_data.modulo_id} para cliente {modulo_data.cliente_id}")

        # Validar que el módulo existe y está activo
        from app.modules.modulos.application.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(modulo_data.modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_data.modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )
        
        if not modulo.es_activo:
            raise ValidationError(
                detail=f"El módulo {modulo.nombre} no está activo en el catálogo.",
                internal_code="MODULE_NOT_ACTIVE"
            )

        # Validar dependencias (módulos requeridos)
        if modulo.modulos_requeridos:
            await ClienteModuloService._validar_dependencias_activas(
                modulo_data.cliente_id,
                modulo.modulos_requeridos
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

        # Validar que no esté ya activado
        await ClienteModuloService._validar_modulo_activo_unico(
            modulo_data.cliente_id, 
            modulo_data.modulo_id
        )

        # Verificar si ya existe un registro (activo o inactivo)
        query_existe = select(ClienteModuloTable.c.cliente_modulo_id, ClienteModuloTable.c.esta_activo).where(
            and_(
                ClienteModuloTable.c.cliente_id == modulo_data.cliente_id,
                ClienteModuloTable.c.modulo_id == modulo_data.modulo_id
            )
        )
        existe_raw = await execute_query(
            query_existe,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        
        # Preparar datos
        configuracion_json_str = json.dumps(modulo_data.configuracion_json) if modulo_data.configuracion_json else None

        if existe_raw:
            # El registro ya existe: hacer UPDATE
            cliente_modulo_id = existe_raw[0]['cliente_modulo_id']
            logger.info(f"[ACTIVAR] Registro existente encontrado (ID: {cliente_modulo_id}), actualizando a activo")
            
            stmt = (
                update(ClienteModuloTable)
                .where(ClienteModuloTable.c.cliente_modulo_id == cliente_modulo_id)
                .values(
                    esta_activo=True,
                    fecha_vencimiento=modulo_data.fecha_vencimiento,
                    modo_prueba=modulo_data.modo_prueba,
                    fecha_fin_prueba=modulo_data.fecha_fin_prueba,
                    configuracion_json=configuracion_json_str,
                    limite_usuarios=modulo_data.limite_usuarios,
                    limite_registros=modulo_data.limite_registros,
                    limite_transacciones_mes=modulo_data.limite_transacciones_mes,
                    fecha_actualizacion=sql_func.getdate(),
                    activado_por_usuario_id=modulo_data.activado_por_usuario_id
                )
                .returning(ClienteModuloTable)
            )
            
            resultado_update = await execute_update(
                stmt,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )
            
            if not resultado_update:
                raise ServiceError(
                    status_code=500,
                    detail="No se pudo activar el módulo para el cliente.",
                    internal_code="MODULE_ACTIVATION_FAILED"
                )
            
            logger.info(f"[ACTIVAR] Módulo reactivado exitosamente (ID: {cliente_modulo_id})")
            cliente_modulo_id_resultado = cliente_modulo_id
        else:
            # El registro NO existe: hacer INSERT
            logger.info(f"[ACTIVAR] Registro no existe, creando nuevo registro")
            
            insert_data = {
                'cliente_id': modulo_data.cliente_id,
                'modulo_id': modulo_data.modulo_id,
                'esta_activo': True,
                'fecha_vencimiento': modulo_data.fecha_vencimiento,
                'modo_prueba': modulo_data.modo_prueba,
                'fecha_fin_prueba': modulo_data.fecha_fin_prueba,
                'configuracion_json': configuracion_json_str,
                'limite_usuarios': modulo_data.limite_usuarios,
                'limite_registros': modulo_data.limite_registros,
                'limite_transacciones_mes': modulo_data.limite_transacciones_mes,
                'activado_por_usuario_id': modulo_data.activado_por_usuario_id
            }

            from sqlalchemy import insert
            stmt = insert(ClienteModuloTable).values(**insert_data).returning(ClienteModuloTable)
            
            resultado = await execute_insert(
                stmt,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )
            if not resultado:
                raise ServiceError(
                    status_code=500,
                    detail="No se pudo activar el módulo para el cliente.",
                    internal_code="MODULE_ACTIVATION_FAILED"
                )
            
            logger.info(f"[ACTIVAR] Módulo activado exitosamente con ID: {resultado['cliente_modulo_id']}")
            cliente_modulo_id_resultado = resultado['cliente_modulo_id']
        
        # ⚠️ CRÍTICO: Aplicar plantillas de roles automáticamente
        try:
            roles_creados = await aplicar_plantillas_roles(
                cliente_id=modulo_data.cliente_id,
                modulo_id=modulo_data.modulo_id,
                activado_por_usuario_id=modulo_data.activado_por_usuario_id
            )
            logger.info(f"[ACTIVAR] Plantillas aplicadas: {len(roles_creados)} roles creados automáticamente")
        except Exception as e:
            logger.error(f"[ACTIVAR] Error aplicando plantillas de roles: {str(e)}", exc_info=True)
            # No fallar la activación si las plantillas fallan, pero registrar el error
            # En producción, podrías querer hacer rollback o notificar al admin
        
        # Obtener el módulo activo completo con información del módulo
        return await ClienteModuloService.obtener_modulo_activo_por_id(cliente_modulo_id_resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_dependencias_activas(cliente_id: UUID, modulos_requeridos_json: str) -> None:
        """
        Valida que todos los módulos requeridos estén activos para el cliente.
        """
        try:
            modulos_requeridos = json.loads(modulos_requeridos_json)
            if not isinstance(modulos_requeridos, list):
                raise ValidationError(
                    detail="modulos_requeridos debe ser un array JSON",
                    internal_code="INVALID_MODULOS_REQUERIDOS_FORMAT"
                )
            
            from app.modules.modulos.application.services.modulo_service import ModuloService
            modulos_activos = await ClienteModuloService.obtener_modulos_activos_cliente(cliente_id)
            modulos_activos_codigos = {m.modulo_codigo for m in modulos_activos if m.modulo_codigo}
            
            modulos_faltantes = []
            for codigo_modulo in modulos_requeridos:
                if codigo_modulo not in modulos_activos_codigos:
                    modulo = await ModuloService.obtener_modulo_por_codigo(codigo_modulo)
                    modulos_faltantes.append(codigo_modulo if not modulo else modulo.nombre)
            
            if modulos_faltantes:
                raise ValidationError(
                    detail=f"Faltan módulos requeridos activos: {', '.join(modulos_faltantes)}",
                    internal_code="MODULES_REQUIRED_NOT_ACTIVE"
                )
        except json.JSONDecodeError:
            raise ValidationError(
                detail="modulos_requeridos debe ser un JSON válido",
                internal_code="INVALID_MODULOS_REQUERIDOS_JSON"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_modulo_cliente(cliente_id: UUID, modulo_id: UUID) -> bool:
        """
        Desactiva un módulo para un cliente.
        Implementa desactivación lógica (soft delete).
        """
        logger.info(f"Desactivando módulo {modulo_id} para cliente {cliente_id}")

        # Obtener el módulo activo
        modulo_activo = await ClienteModuloService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        if not modulo_activo:
            raise NotFoundError(
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}.",
                internal_code="MODULE_NOT_ACTIVE"
            )

        # Validar que no sea un módulo core (opcional, depende de reglas de negocio)
        from app.modules.modulos.application.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if modulo and modulo.es_core:
            raise ValidationError(
                detail="No se puede desactivar un módulo core.",
                internal_code="CANNOT_DEACTIVATE_CORE_MODULE"
            )

        # Realizar desactivación lógica
        stmt = (
            update(ClienteModuloTable)
            .where(ClienteModuloTable.c.cliente_modulo_id == modulo_activo.cliente_modulo_id)
            .values(esta_activo=False, fecha_actualizacion=sql_func.getdate())
        )
        
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        logger.info(f"Módulo {modulo_id} desactivado para cliente {cliente_id} exitosamente.")
        return True

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_configuracion(
        cliente_id: UUID,
        modulo_id: UUID,
        configuracion: Dict[str, Any]
    ) -> ClienteModuloRead:
        """
        Actualiza la configuración personalizada de un módulo activo.
        """
        modulo_activo = await ClienteModuloService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        if not modulo_activo:
            raise NotFoundError(
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}.",
                internal_code="MODULE_NOT_ACTIVE"
            )
        
        configuracion_json_str = json.dumps(configuracion) if configuracion else None
        
        stmt = (
            update(ClienteModuloTable)
            .where(ClienteModuloTable.c.cliente_modulo_id == modulo_activo.cliente_modulo_id)
            .values(
                configuracion_json=configuracion_json_str,
                fecha_actualizacion=sql_func.getdate()
            )
            .returning(ClienteModuloTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar la configuración.",
                internal_code="CONFIG_UPDATE_FAILED"
            )
        
        return await ClienteModuloService.obtener_modulo_activo_por_id(modulo_activo.cliente_modulo_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_limites(
        cliente_id: UUID,
        modulo_id: UUID,
        limite_usuarios: Optional[int] = None,
        limite_registros: Optional[int] = None,
        limite_transacciones_mes: Optional[int] = None
    ) -> ClienteModuloRead:
        """
        Actualiza los límites de uso de un módulo activo.
        """
        modulo_activo = await ClienteModuloService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        if not modulo_activo:
            raise NotFoundError(
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}.",
                internal_code="MODULE_NOT_ACTIVE"
            )
        
        update_dict = {}
        if limite_usuarios is not None:
            update_dict['limite_usuarios'] = limite_usuarios
        if limite_registros is not None:
            update_dict['limite_registros'] = limite_registros
        if limite_transacciones_mes is not None:
            update_dict['limite_transacciones_mes'] = limite_transacciones_mes
        
        if not update_dict:
            raise ValidationError(
                detail="Debe proporcionar al menos un límite para actualizar.",
                internal_code="NO_LIMITS_PROVIDED"
            )
        
        update_dict['fecha_actualizacion'] = sql_func.getdate()
        
        stmt = (
            update(ClienteModuloTable)
            .where(ClienteModuloTable.c.cliente_modulo_id == modulo_activo.cliente_modulo_id)
            .values(**update_dict)
            .returning(ClienteModuloTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudieron actualizar los límites.",
                internal_code="LIMITS_UPDATE_FAILED"
            )
        
        return await ClienteModuloService.obtener_modulo_activo_por_id(modulo_activo.cliente_modulo_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def extender_vencimiento(cliente_id: UUID, modulo_id: UUID, dias: int) -> ClienteModuloRead:
        """
        Extiende el vencimiento de un módulo activo agregando días.
        """
        modulo_activo = await ClienteModuloService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        if not modulo_activo:
            raise NotFoundError(
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}.",
                internal_code="MODULE_NOT_ACTIVE"
            )
        
        if dias <= 0:
            raise ValidationError(
                detail="Los días a extender deben ser positivos.",
                internal_code="INVALID_DAYS"
            )
        
        nueva_fecha = None
        if modulo_activo.fecha_vencimiento:
            nueva_fecha = modulo_activo.fecha_vencimiento + timedelta(days=dias)
        else:
            nueva_fecha = datetime.now() + timedelta(days=dias)
        
        stmt = (
            update(ClienteModuloTable)
            .where(ClienteModuloTable.c.cliente_modulo_id == modulo_activo.cliente_modulo_id)
            .values(
                fecha_vencimiento=nueva_fecha,
                fecha_actualizacion=sql_func.getdate()
            )
            .returning(ClienteModuloTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo extender el vencimiento.",
                internal_code="VENCMIENTO_EXTENSION_FAILED"
            )
        
        return await ClienteModuloService.obtener_modulo_activo_por_id(modulo_activo.cliente_modulo_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def validar_licencia(cliente_id: UUID, modulo_id: UUID) -> Dict[str, Any]:
        """
        Valida la licencia de un módulo (está activo + no vencido).
        """
        modulo_activo = await ClienteModuloService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        if not modulo_activo:
            return {
                "valido": False,
                "razon": "Módulo no activado para el cliente"
            }
        
        if not modulo_activo.esta_activo:
            return {
                "valido": False,
                "razon": "Módulo desactivado"
            }
        
        if modulo_activo.fecha_vencimiento:
            if modulo_activo.fecha_vencimiento < datetime.now():
                return {
                    "valido": False,
                    "razon": "Licencia vencida",
                    "fecha_vencimiento": modulo_activo.fecha_vencimiento.isoformat()
                }
        
        return {
            "valido": True,
            "fecha_vencimiento": modulo_activo.fecha_vencimiento.isoformat() if modulo_activo.fecha_vencimiento else None,
            "modo_prueba": modulo_activo.modo_prueba
        }

