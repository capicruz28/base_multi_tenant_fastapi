# app/services/menu_service.py
from typing import List, Dict, Optional, Any
from uuid import UUID
import logging

# 🗄️ IMPORTACIONES DE BASE DE DATOS
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import (
    execute_query, execute_insert, execute_update, execute_procedure, execute_procedure_params
)
from app.infrastructure.database.queries import (
    GET_ALL_MENUS_ADMIN, INSERT_MENU, SELECT_MENU_BY_ID, UPDATE_MENU_TEMPLATE,
    DEACTIVATE_MENU, REACTIVATE_MENU, CHECK_MENU_EXISTS, CHECK_AREA_EXISTS,
    GET_MENUS_BY_AREA_FOR_TREE_QUERY, GET_MAX_ORDEN_FOR_SIBLINGS, GET_MAX_ORDEN_FOR_ROOT
)

# 🚨 EXCEPCIONES - Nuevo sistema de manejo de errores
from app.core.exceptions import (
    ValidationError, NotFoundError, ServiceError, DatabaseError
)

# 🏗️ BASE SERVICE - Clase base para manejo consistente de errores
from app.core.application.base_service import BaseService

# 📋 SCHEMAS
from app.modules.menus.presentation.schemas import (
    MenuResponse, MenuItem, MenuCreate, MenuUpdate, MenuReadSingle
)

# 🔧 UTILIDADES
from app.modules.menus.application.services.menu_helper import build_menu_tree

logger = logging.getLogger(__name__)

class MenuService(BaseService):
    """
    Servicio para gestión completa de menús del sistema en arquitectura multi-tenant.
    
    ⚠️ IMPORTANTE: Este servicio maneja operaciones críticas relacionadas con:
    - Estructura jerárquica de menús **por cliente**
    - Menús del sistema (cliente_id IS NULL) vs. menús custom del cliente
    - Permisos y accesos basados en roles
    
    CARACTERÍSTICAS PRINCIPALES:
    - Herencia de BaseService para manejo automático de errores
    - Validaciones de integridad referencial **por cliente**
    - Aislamiento total de datos por cliente_id
    - Soporte para menús del sistema y menús custom
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def get_menu_for_user(usuario_id: UUID) -> MenuResponse:
        """
        Obtiene la estructura de menú filtrada según los roles y permisos del usuario.
        
        🔐 SEGURIDAD: 
        - Filtra menús basado en los roles y permisos del usuario
        - Construye una estructura jerárquica para el frontend
        - Optimizado para rendimiento con stored procedures
        
        Args:
            usuario_id: ID del usuario autenticado
            
        Returns:
            MenuResponse: Estructura de menú permitida para el usuario
            
        Raises:
            ServiceError: Si hay errores al obtener o procesar el menú
        """
        procedure_name = "sp_GetMenuForUser"
        params_dict = {'UsuarioID': usuario_id}

        logger.info(f"Obteniendo menú filtrado para usuario_id: {usuario_id}")
        
        try:
            # 🗄️ EJECUTAR STORED PROCEDURE
            # ✅ FASE 2: Usar await
            resultado_sp = await execute_procedure_params(procedure_name, params_dict)

            if not resultado_sp:
                logger.info(f"No se encontraron menús permitidos para el usuario ID: {usuario_id}.")
                return MenuResponse(menu=[])

            # 🌳 CONSTRUIR ESTRUCTURA JERÁRQUICA
            menu_tree: List[MenuItem] = build_menu_tree(resultado_sp)
            logger.info(f"Árbol de menú construido para usuario {usuario_id} con {len(menu_tree)} items raíz.")

            return MenuResponse(menu=menu_tree)

        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener menú para usuario {usuario_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener menú del usuario",
                internal_code="MENU_USER_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al obtener menú para usuario {usuario_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al procesar el menú del usuario",
                internal_code="MENU_USER_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_todos_menus_estructurados_admin(cliente_id: UUID) -> MenuResponse:
        """
        Obtiene la estructura completa de menús **de un cliente** para administración.
        
        📊 VISIÓN COMPLETA:
        - Incluye todos los menús (activos e inactivos) del cliente
        - Estructura jerárquica completa
        - Ideal para interfaces de administración
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            MenuResponse: Estructura completa de menús del cliente
            
        Raises:
            ServiceError: Si hay errores al obtener la estructura
        """
        logger.info(f"Obteniendo estructura completa de menús para cliente {cliente_id}")
        
        try:
            # ✅ NUEVO: Pasar cliente_id al SP
            params_dict = {'ClienteID': cliente_id}
            resultado_sp = execute_procedure_params("sp_GetAllMenuItemsAdmin", params_dict)
            
            if not resultado_sp:
                logger.warning(f"sp_GetAllMenuItemsAdmin no devolvió resultados para cliente {cliente_id}.")
                return MenuResponse(menu=[])
            
            menu_tree: List[MenuItem] = build_menu_tree(resultado_sp)
            logger.info(f"Estructura de menú para cliente {cliente_id} construida con {len(menu_tree)} items raíz.")
            
            return MenuResponse(menu=menu_tree)

        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener estructura admin para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener estructura de menús",
                internal_code="MENU_ADMIN_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al obtener menús admin para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al procesar estructura de menús",
                internal_code="MENU_ADMIN_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_menu_por_id(menu_id: UUID, cliente_id: Optional[UUID] = None) -> Optional[MenuReadSingle]:
        """
        Obtiene los detalles de un menú específico por su ID con validación multi-tenant.
        
        🔍 DETALLES COMPLETOS:
        - Incluye información del área asociada
        - Valida que el menú exista y pertenezca al cliente (o sea del sistema)
        - Útil para operaciones de edición
        
        🔐 SEGURIDAD MULTI-TENANT:
        - Si se proporciona cliente_id, solo retorna menús del cliente o del sistema
        - Si no se proporciona cliente_id, retorna cualquier menú (uso interno)
        
        Args:
            menu_id: ID del menú a buscar
            cliente_id: ID del cliente para validación multi-tenant (opcional)
            
        Returns:
            Optional[MenuReadSingle]: Detalles del menú o None si no existe o no pertenece al cliente
            
        Raises:
            ServiceError: Si hay errores en la consulta
        """
        logger.debug(f"🔍 Buscando menú con ID: {menu_id}, cliente_id: {cliente_id}")
        
        try:
            # ✅ FILTRAR POR cliente_id SI SE PROPORCIONA
            if cliente_id is not None:
                # ✅ FASE 2: Usar await
                resultado = await execute_query(SELECT_MENU_BY_ID, (menu_id, cliente_id))
            else:
                # Uso interno: obtener cualquier menú sin filtro de cliente
                query_interno = """
                SELECT m.menu_id, m.nombre, m.icono, m.ruta, m.padre_menu_id, m.orden,
                       m.es_activo, m.fecha_creacion, m.area_id, m.cliente_id, a.nombre as area_nombre
                FROM menu m
                LEFT JOIN area_menu a ON m.area_id = a.area_id
                WHERE m.menu_id = ?
                """
                # ✅ FASE 2: Usar await
                resultado = await execute_query(query_interno, (menu_id,))
            
            if not resultado:
                logger.debug(f"Menú con ID {menu_id} no encontrado para cliente {cliente_id}.")
                return None

            menu_data = resultado[0]
            return MenuReadSingle(**menu_data)
            
        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener menú {menu_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener menú",
                internal_code="MENU_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al obtener menú {menu_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener menú",
                internal_code="MENU_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_menu(cliente_id: UUID, menu_data: MenuCreate) -> MenuReadSingle:
        """
        Crea un nuevo menú en el sistema **para un cliente específico** con validaciones completas.
        
        🆕 CREACIÓN SEGURA:
        - Valida existencia del área y menú padre **del mismo cliente**
        - Calcula automáticamente el orden
        - Aplica reglas de negocio para la jerarquía
        
        Args:
            cliente_id: ID del cliente
            menu_data: Datos validados del menú a crear
            
        Returns:
            MenuReadSingle: Menú creado con todos sus datos
            
        Raises:
            ValidationError: Si los datos son inválidos
            ServiceError: Si la creación falla
        """
        logger.info(f"Intentando crear menú para cliente {cliente_id}: {menu_data.nombre}")
        
        try:
            # 🚫 VALIDACIONES PREVIAS
            if menu_data.padre_menu_id:
                # Verificar que el menú padre exista Y pertenezca al mismo cliente
                padre_query = "SELECT cliente_id FROM menu WHERE menu_id = ?"
                # ✅ FASE 2: Usar await
                padre_result = await execute_query(padre_query, (menu_data.padre_menu_id,))
                if not padre_result:
                    raise ValidationError(
                        detail=f"El menú padre con ID {menu_data.padre_menu_id} no existe.",
                        internal_code="MENU_PARENT_NOT_FOUND"
                    )
                padre_cliente_id = padre_result[0]['cliente_id']
                if padre_cliente_id != cliente_id:
                    raise ValidationError(
                        detail=f"El menú padre con ID {menu_data.padre_menu_id} no pertenece al cliente {cliente_id}.",
                        internal_code="MENU_PARENT_WRONG_CLIENT"
                    )
                    
            if not menu_data.area_id:
                raise ValidationError(
                    detail="El ID del área es obligatorio para crear un menú.",
                    internal_code="MENU_AREA_REQUIRED"
                )
            else:
                # Verificar que el área exista Y pertenezca al mismo cliente
                area_query = "SELECT cliente_id FROM area_menu WHERE area_id = ?"
                # ✅ FASE 2: Usar await
                area_result = await execute_query(area_query, (menu_data.area_id,))
                if not area_result:
                    raise ValidationError(
                        detail=f"El área con ID {menu_data.area_id} no existe.",
                        internal_code="MENU_AREA_NOT_FOUND"
                    )
                area_cliente_id = area_result[0]['cliente_id']
                if area_cliente_id != cliente_id:
                    raise ValidationError(
                        detail=f"El área con ID {menu_data.area_id} no pertenece al cliente {cliente_id}.",
                        internal_code="MENU_AREA_WRONG_CLIENT"
                    )

            # 🧮 CALCULAR ORDEN AUTOMÁTICAMENTE
            max_orden_result = None
            if menu_data.padre_menu_id:
                # ✅ FASE 2: Usar await
                max_orden_result = await execute_query(
                    GET_MAX_ORDEN_FOR_SIBLINGS, 
                    (cliente_id, menu_data.area_id, menu_data.padre_menu_id)
                )
            else:
                # ✅ FASE 2: Usar await
                max_orden_result = await execute_query(
                    GET_MAX_ORDEN_FOR_ROOT, 
                    (cliente_id, menu_data.area_id)
                )

            max_orden = 0
            if max_orden_result and max_orden_result[0]['max_orden'] is not None:
                max_orden = max_orden_result[0]['max_orden']

            next_orden = max_orden + 1
            logger.debug(f"Calculado next_orden: {next_orden}")

            # 💾 EJECUTAR INSERCIÓN
            params = (
                cliente_id,
                menu_data.nombre,
                menu_data.icono,
                menu_data.ruta,
                menu_data.padre_menu_id,
                next_orden,
                menu_data.area_id,
                menu_data.es_activo
            )

            # ✅ FASE 2: Usar await
            resultado = await execute_insert(INSERT_MENU, params)
            
            if not resultado or 'menu_id' not in resultado:
                raise ServiceError(
                    status_code=500,
                    detail="La inserción no devolvió el registro creado correctamente.",
                    internal_code="MENU_CREATION_FAILED"
                )

            # 📍 OBTENER NOMBRE DEL ÁREA PARA LA RESPUESTA
            area_nombre = None
            if resultado.get('area_id'):
                # ✅ FASE 2: Usar await
                area_info = await execute_query(
                    "SELECT nombre FROM area_menu WHERE area_id = ?", 
                    (resultado['area_id'],)
                )
                if area_info: 
                    area_nombre = area_info[0]['nombre']

            created_menu = MenuReadSingle(**resultado, area_nombre=area_nombre)
            logger.info(f"Menú '{created_menu.nombre}' creado para cliente {cliente_id} con ID: {created_menu.menu_id}")
            
            return created_menu

        except (ValidationError, ServiceError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al crear menú para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al crear menú",
                internal_code="MENU_CREATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al crear menú para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al crear menú",
                internal_code="MENU_CREATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_menu(menu_id: UUID, menu_data: MenuUpdate, cliente_id: Optional[UUID] = None) -> MenuReadSingle:
        """
        Actualiza un menú existente con validaciones de integridad **por cliente**.
        
        🔄 ACTUALIZACIÓN PARCIAL:
        - Solo actualiza los campos proporcionados
        - Valida relaciones (padre, área) **del mismo cliente**
        - Mantiene la integridad jerárquica
        
        🔐 SEGURIDAD MULTI-TENANT:
        - Si se proporciona cliente_id, valida que el menú pertenezca al cliente
        - Permite actualizar menús del sistema (cliente_id IS NULL) solo si no se proporciona cliente_id
        
        Args:
            menu_id: ID del menú a actualizar
            menu_data: Campos a actualizar (parcial)
            cliente_id: ID del cliente para validación multi-tenant (opcional)
            
        Returns:
            MenuReadSingle: Menú actualizado
            
        Raises:
            NotFoundError: Si el menú no existe
            ValidationError: Si los datos son inválidos o el menú no pertenece al cliente
            ServiceError: Si la actualización falla
        """
        logger.info(f"Intentando actualizar menú ID: {menu_id}, cliente_id: {cliente_id}")

        update_payload = menu_data.model_dump(exclude_unset=True)
        
        if not update_payload:
            raise ValidationError(
                detail="No se proporcionaron datos para actualizar.",
                internal_code="MENU_UPDATE_NO_DATA"
            )

        # 🔍 VERIFICAR EXISTENCIA DEL MENÚ Y VALIDAR CLIENTE_ID
        menu_existente = await MenuService.obtener_menu_por_id(menu_id, cliente_id=cliente_id)
        if not menu_existente:
            raise NotFoundError(
                detail=f"Menú con ID {menu_id} no encontrado para actualizar.",
                internal_code="MENU_NOT_FOUND"
            )
        
        # ✅ OBTENER cliente_id DEL MENÚ (para validaciones posteriores)
        menu_cliente_id = menu_existente.cliente_id
        
        # ✅ VALIDAR QUE EL MENÚ PERTENEZCA AL CLIENTE (si se proporcionó cliente_id)
        if cliente_id is not None:
            if menu_cliente_id is not None and menu_cliente_id != cliente_id:
                raise ValidationError(
                    detail=f"El menú con ID {menu_id} no pertenece al cliente {cliente_id}.",
                    internal_code="MENU_WRONG_CLIENT"
                )
            # Usar el cliente_id proporcionado para las validaciones
            cliente_id_validacion = cliente_id
        else:
            # Si no se proporcionó cliente_id, usar el del menú (para compatibilidad)
            cliente_id_validacion = menu_cliente_id

        try:
            # 🚫 VALIDACIONES DE INTEGRIDAD
            if 'padre_menu_id' in update_payload and update_payload['padre_menu_id'] is not None:
                if menu_id == update_payload['padre_menu_id']:
                    raise ValidationError(
                        detail="Un menú no puede ser su propio padre.",
                        internal_code="MENU_SELF_REFERENCE"
                    )
                    
                padre_query = "SELECT cliente_id FROM menu WHERE menu_id = ?"
                padre_result = execute_query(padre_query, (update_payload['padre_menu_id'],))
                if not padre_result:
                    raise ValidationError(
                        detail=f"El menú padre con ID {update_payload['padre_menu_id']} no existe.",
                        internal_code="MENU_PARENT_NOT_FOUND"
                    )
                padre_cliente_id = padre_result[0]['cliente_id']
                if padre_cliente_id != cliente_id_validacion and padre_cliente_id is not None:
                    raise ValidationError(
                        detail=f"El menú padre con ID {update_payload['padre_menu_id']} no pertenece al cliente {cliente_id_validacion}.",
                        internal_code="MENU_PARENT_WRONG_CLIENT"
                    )
                    
            if 'area_id' in update_payload and update_payload['area_id'] is not None:
                area_query = "SELECT cliente_id FROM area_menu WHERE area_id = ?"
                area_result = execute_query(area_query, (update_payload['area_id'],))
                if not area_result:
                    raise ValidationError(
                        detail=f"El área con ID {update_payload['area_id']} no existe.",
                        internal_code="MENU_AREA_NOT_FOUND"
                    )
                area_cliente_id = area_result[0]['cliente_id']
                if area_cliente_id != cliente_id_validacion and area_cliente_id is not None:
                    raise ValidationError(
                        detail=f"El área con ID {update_payload['area_id']} no pertenece al cliente {cliente_id_validacion}.",
                        internal_code="MENU_AREA_WRONG_CLIENT"
                    )

            # 💾 EJECUTAR ACTUALIZACIÓN
            params = (
                update_payload.get('nombre'),
                update_payload.get('icono'),
                update_payload.get('ruta'),
                update_payload.get('padre_menu_id'),
                update_payload.get('orden'),
                update_payload.get('area_id'),
                update_payload.get('es_activo'),
                cliente_id_validacion,
                menu_id
            )
            
            # ✅ FASE 2: Usar await
            resultado = await execute_update(UPDATE_MENU_TEMPLATE, params)
            
            if not resultado:
                raise ServiceError(
                    status_code=500,
                    detail="La actualización no devolvió el registro actualizado.",
                    internal_code="MENU_UPDATE_FAILED"
                )

            # 📍 OBTENER NOMBRE DEL ÁREA ACTUALIZADO
            area_nombre = None
            if resultado.get('area_id'):
                # ✅ FASE 2: Usar await
                area_info = await execute_query(
                    "SELECT nombre FROM area_menu WHERE area_id = ?", 
                    (resultado['area_id'],)
                )
                if area_info: 
                    area_nombre = area_info[0]['nombre']

            updated_menu = MenuReadSingle(**resultado, area_nombre=area_nombre)
            logger.info(f"Menú ID: {menu_id} del cliente {cliente_id_validacion} actualizado exitosamente.")
            
            return updated_menu

        except (ValidationError, NotFoundError, ServiceError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al actualizar menú {menu_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al actualizar menú",
                internal_code="MENU_UPDATE_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al actualizar menú {menu_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al actualizar menú",
                internal_code="MENU_UPDATE_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_menu(menu_id: UUID) -> Dict[str, Any]:
        """
        Desactiva un menú (borrado lógico).
        
        🚫 DESACTIVACIÓN SEGURA:
        - Verifica que el menú exista y esté activo
        - Realiza desactivación lógica
        - Mantiene integridad referencial
        
        Args:
            menu_id: ID del menú a desactivar
            
        Returns:
            Dict: Resultado de la operación con metadatos
            
        Raises:
            NotFoundError: Si el menú no existe
            ServiceError: Si la desactivación falla
        """
        logger.info(f"Intentando desactivar menú ID: {menu_id}")
        
        try:
            # ✅ FASE 2: Usar await
            resultado = await execute_update(DEACTIVATE_MENU, (menu_id,))
            
            if not resultado:
                # 🔍 VERIFICAR SI EXISTE O YA ESTÁ INACTIVO
                # ✅ FASE 2: Usar await
                menu_existente = await execute_query(CHECK_MENU_EXISTS, (menu_id,))
                if not menu_existente:
                    raise NotFoundError(
                        detail=f"Menú con ID {menu_id} no encontrado para desactivar.",
                        internal_code="MENU_NOT_FOUND"
                    )
                else:
                    raise ValidationError(
                        detail=f"Menú con ID {menu_id} ya estaba inactivo.",
                        internal_code="MENU_ALREADY_INACTIVE"
                    )

            logger.info(f"Menú ID: {menu_id} desactivado exitosamente.")
            return {
                "menu_id": resultado.get('menu_id'), 
                "es_activo": resultado.get('es_activo')
            }

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al desactivar menú {menu_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al desactivar menú",
                internal_code="MENU_DEACTIVATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al desactivar menú {menu_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al desactivar menú",
                internal_code="MENU_DEACTIVATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def reactivar_menu(menu_id: UUID) -> Dict[str, Any]:
        """
        Reactiva un menú previamente desactivado.
        
        🔄 REACTIVACIÓN:
        - Verifica que el menú exista y esté inactivo
        - Realiza reactivación lógica
        - Valida estado previo
        
        Args:
            menu_id: ID del menú a reactivar
            
        Returns:
            Dict: Resultado de la operación con metadatos
            
        Raises:
            NotFoundError: Si el menú no existe
            ServiceError: Si la reactivación falla
        """
        logger.info(f"Intentando reactivar menú ID: {menu_id}")
        
        try:
            # ✅ FASE 2: Usar await
            resultado = await execute_update(REACTIVATE_MENU, (menu_id,))
            
            if not resultado:
                raise NotFoundError(
                    detail=f"Menú con ID {menu_id} no encontrado o ya estaba activo.",
                    internal_code="MENU_NOT_FOUND_OR_ACTIVE"
                )

            logger.info(f"Menú ID: {menu_id} reactivado exitosamente.")
            return {
                "menu_id": resultado.get('menu_id'), 
                "es_activo": resultado.get('es_activo')
            }
            
        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al reactivar menú {menu_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al reactivar menú",
                internal_code="MENU_REACTIVATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al reactivar menú {menu_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al reactivar menú",
                internal_code="MENU_REACTIVATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_arbol_menu_por_area(area_id: UUID, cliente_id: UUID) -> MenuResponse:
        """
        Obtiene la estructura jerárquica de menús para un área específica **de un cliente**.
        
        🌳 ÁRBOL POR ÁREA:
        - Filtra menús por área específica del cliente
        - Construye estructura jerárquica completa
        - Útil para administración por áreas
        
        Args:
            cliente_id: ID del cliente
            area_id: ID del área a filtrar
            
        Returns:
            MenuResponse: Estructura de menú del área especificada
            
        Raises:
            ServiceError: Si hay errores al obtener el árbol
        """
        logger.info(f"Obteniendo árbol de menú para cliente {cliente_id}, area_id: {area_id}")
        
        try:
            params = (area_id, cliente_id)
            # ✅ FASE 2: Usar await
            menu_items_raw_list = await execute_query(GET_MENUS_BY_AREA_FOR_TREE_QUERY, params)

            if not menu_items_raw_list:
                logger.info(f"No se encontraron menús para el cliente {cliente_id}, área ID: {area_id}.")
                return MenuResponse(menu=[])

            menu_tree = build_menu_tree(menu_items_raw_list)
            logger.info(f"Árbol de menú del cliente {cliente_id}, área {area_id} construido con {len(menu_tree)} items raíz.")
            
            return MenuResponse(menu=menu_tree)

        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener árbol de menú para cliente {cliente_id}, área {area_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener menú del área",
                internal_code="MENU_AREA_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al obtener menú del cliente {cliente_id}, área {area_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al procesar el menú del área",
                internal_code="MENU_AREA_RETRIEVAL_UNEXPECTED_ERROR"
            )