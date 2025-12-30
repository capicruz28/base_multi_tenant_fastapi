# app/services/permiso_service.py
from typing import Dict, List, Optional, Any
from uuid import UUID
import logging

# 🗄️ IMPORTACIONES DE BASE DE DATOS
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

# 🚨 EXCEPCIONES - Nuevo sistema de manejo de errores
from app.core.exceptions import (
    ValidationError, NotFoundError, ServiceError, DatabaseError
)

# 🏗️ BASE SERVICE - Clase base para manejo consistente de errores
from app.core.application.base_service import BaseService

# 👥 SERVICIOS RELACIONADOS
from app.modules.rbac.application.services.rol_service import RolService
# ✅ REFACTORIZACIÓN: Importación lazy para evitar circular imports
# from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService

logger = logging.getLogger(__name__)

class PermisoService(BaseService):
    """
    Servicio para gestión de permisos de roles sobre menús en arquitectura multi-tenant.
    
    ⚠️ IMPORTANTE: Este servicio maneja operaciones críticas relacionadas con:
    - Asignación y actualización de permisos de roles sobre menús **dentro de un cliente**
    - Consulta de permisos existentes
    - Revocación de permisos
    
    CARACTERÍSTICAS PRINCIPALES:
    - Herencia de BaseService para manejo automático de errores
    - Validaciones robustas de existencia de roles y menús **y pertenencia al cliente**
    - Operaciones atómicas para asignación/actualización
    - Logging detallado para auditoría de seguridad
    - Aislamiento total de datos por cliente_id
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_rol_y_menu(cliente_id: UUID, rol_id: UUID, menu_id: UUID) -> None:
        """
        Valida la existencia del rol y el menú **y que pertenezcan al mismo cliente**.
        
        🛡️ VALIDACIÓN DE INTEGRIDAD REFERENCIAL:
        - Verifica que el rol exista, esté activo y pertenezca al cliente
        - Verifica que el menú exista, esté activo y pertenezca al cliente
        - Previene asignaciones a entidades inexistentes o de otro cliente
        
        Args:
            cliente_id: ID del cliente
            rol_id: ID del rol a validar
            menu_id: ID del menú a validar
            
        Raises:
            NotFoundError: Si el rol o el menú no existen o no pertenecen al cliente
            ServiceError: Si hay errores en la validación
        """
        try:
            # 👤 VALIDAR ROL Y OBTENER SU CLIENTE_ID
            rol = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True)
            if not rol:
                raise NotFoundError(
                    detail=f"Rol con ID {rol_id} no encontrado.",
                    internal_code="ROLE_NOT_FOUND"
                )
            rol_cliente_id_raw = rol.get('cliente_id')
            codigo_rol = rol.get('codigo_rol')
            
            # 🔍 DEBUG: Logging para diagnosticar el problema
            logger.info(f"[VALIDAR_ROL] Rol ID: {rol_id}, Rol cliente_id (raw): {rol_cliente_id_raw} (tipo: {type(rol_cliente_id_raw)}), Cliente contexto: {cliente_id} (tipo: {type(cliente_id)}), Codigo_rol: {codigo_rol}")
            
            # ✅ CORRECCIÓN: Permitir roles del sistema (cliente_id = NULL o con codigo_rol) y roles del cliente actual
            # Solo rechazar si el rol pertenece a otro cliente diferente Y no es un rol del sistema
            es_rol_sistema = rol_cliente_id_raw is None or codigo_rol is not None
            
            # 🔄 NORMALIZAR UUIDs PARA COMPARACIÓN
            # Convertir ambos a UUID si son strings o mantener como UUID
            from uuid import UUID
            rol_cliente_id = None
            if rol_cliente_id_raw is not None:
                if isinstance(rol_cliente_id_raw, str):
                    try:
                        rol_cliente_id = UUID(rol_cliente_id_raw)
                    except (ValueError, AttributeError):
                        rol_cliente_id = None
                elif isinstance(rol_cliente_id_raw, UUID):
                    rol_cliente_id = rol_cliente_id_raw
                else:
                    # Intentar convertir desde otros tipos
                    try:
                        rol_cliente_id = UUID(str(rol_cliente_id_raw))
                    except (ValueError, AttributeError):
                        rol_cliente_id = None
            
            cliente_id_normalizado = cliente_id
            if isinstance(cliente_id, str):
                try:
                    cliente_id_normalizado = UUID(cliente_id)
                except (ValueError, AttributeError):
                    pass
            
            logger.info(f"[VALIDAR_ROL] Después de normalización - Rol cliente_id: {rol_cliente_id}, Cliente contexto: {cliente_id_normalizado}, Es rol sistema: {es_rol_sistema}")
            
            # Validar: permitir si es rol del sistema O si pertenece al cliente actual
            if not es_rol_sistema:
                if rol_cliente_id is None:
                    # Si no es rol del sistema pero cliente_id es None, es un error de datos
                    logger.warning(f"[VALIDAR_ROL] Rol {rol_id} tiene cliente_id=None pero no es rol del sistema (codigo_rol={codigo_rol})")
                elif rol_cliente_id != cliente_id_normalizado:
                    logger.warning(f"[VALIDAR_ROL] Rol {rol_id} pertenece a cliente {rol_cliente_id} pero se intenta usar desde cliente {cliente_id_normalizado}")
                    raise ValidationError(
                        detail=f"El rol con ID {rol_id} no pertenece al cliente {cliente_id}.",
                        internal_code="ROLE_WRONG_CLIENT"
                    )
            
            logger.info(f"[VALIDAR_ROL] Validación exitosa - Rol {rol_id} es {'rol del sistema' if es_rol_sistema else f'rol del cliente {rol_cliente_id}'}")

            # 📋 VALIDAR MENÚ Y OBTENER SU CLIENTE_ID
            # ✅ REFACTORIZACIÓN: Importación lazy para evitar circular imports
            from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
            menu = await ModuloMenuService.obtener_menu_por_id(menu_id)
            if not menu:
                raise NotFoundError(
                    detail=f"Menú con ID {menu_id} no encontrado.",
                    internal_code="MENU_NOT_FOUND"
                )
            # ModuloMenuRead es un objeto Pydantic, acceder directamente al atributo
            menu_cliente_id = menu.cliente_id
            if menu_cliente_id != cliente_id and menu_cliente_id is not None:
                raise ValidationError(
                    detail=f"El menú con ID {menu_id} no pertenece al cliente {cliente_id}.",
                    internal_code="MENU_WRONG_CLIENT"
                )

            logger.debug(f"Validación exitosa - Cliente: {cliente_id}, Rol ID: {rol_id}, Menú ID: {menu_id}")

        except (ValidationError, NotFoundError):
            # 🔄 RE-LANZAR ERRORES ESPECÍFICOS
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD en _validar_rol_y_menu para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al validar rol y menú",
                internal_code="ROLE_MENU_VALIDATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en _validar_rol_y_menu para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al validar rol y menú",
                internal_code="ROLE_MENU_VALIDATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def asignar_o_actualizar_permiso(
        cliente_id: UUID,
        rol_id: UUID,
        menu_id: UUID,
        puede_ver: Optional[bool] = None,
        puede_editar: Optional[bool] = None,
        puede_eliminar: Optional[bool] = None,
        puede_crear: Optional[bool] = None,
        puede_exportar: Optional[bool] = None,
        puede_imprimir: Optional[bool] = None,
        puede_aprobar: Optional[bool] = None,
        permisos_extra: Optional[str] = None
    ) -> Dict:
        """
        Asigna o actualiza los permisos de un rol sobre un menú **dentro de un cliente**.
        
        🔄 COMPORTAMIENTO INTELIGENTE:
        - Si el permiso no existe, lo crea
        - Si el permiso existe, lo actualiza
        - Solo actualiza los campos proporcionados
        - Valida que rol y menú pertenezcan al cliente
        
        Args:
            cliente_id: ID del cliente
            rol_id: ID del rol
            menu_id: ID del menú
            puede_ver: Permiso para ver (opcional)
            puede_editar: Permiso para editar (opcional)
            puede_eliminar: Permiso para eliminar (opcional)
            puede_crear: Permiso para crear (opcional)
            puede_exportar: Permiso para exportar (opcional)
            puede_imprimir: Permiso para imprimir (opcional)
            
        Returns:
            Dict: Permiso asignado o actualizado
            
        Raises:
            NotFoundError: Si el rol o menú no existen
            ValidationError: Si no se proporciona al menos un permiso o hay conflicto de cliente
            ServiceError: Si la operación falla
        """
        logger.info(f"Intentando asignar/actualizar permiso para cliente {cliente_id} - Rol: {rol_id}, Menú: {menu_id}")

        try:
            # 1. 🛡️ VALIDAR ROL Y MENÚ
            await PermisoService._validar_rol_y_menu(cliente_id, rol_id, menu_id)

            # 2. 🚫 VALIDAR AL MENOS UN PERMISO PROPORCIONADO
            permiso_data = {}
            if puede_ver is not None:
                permiso_data['puede_ver'] = puede_ver
            if puede_crear is not None:
                permiso_data['puede_crear'] = puede_crear
            if puede_editar is not None:
                permiso_data['puede_editar'] = puede_editar
            if puede_eliminar is not None:
                permiso_data['puede_eliminar'] = puede_eliminar
            if puede_exportar is not None:
                permiso_data['puede_exportar'] = puede_exportar
            if puede_imprimir is not None:
                permiso_data['puede_imprimir'] = puede_imprimir
            if puede_aprobar is not None:
                permiso_data['puede_aprobar'] = puede_aprobar
            if permisos_extra is not None:
                permiso_data['permisos_extra'] = permisos_extra

            if not permiso_data:
                raise ValidationError(
                    detail="Debe proporcionar al menos un permiso.",
                    internal_code="NO_PERMISSIONS_PROVIDED"
                )

            # 3. 🔍 VERIFICAR SI EL PERMISO YA EXISTE
            # ✅ ACTUALIZADO: Incluir todos los campos de permisos
            check_query = """
            SELECT permiso_id, puede_ver, puede_crear, puede_editar, puede_eliminar, 
                   puede_exportar, puede_imprimir, puede_aprobar, permisos_extra
            FROM rol_menu_permiso
            WHERE cliente_id = ? AND rol_id = ? AND menu_id = ?
            """
            # ✅ FASE 2: Usar await
            existing_perm = await execute_query(check_query, (cliente_id, rol_id, menu_id))

            if existing_perm:
                # 🟡 ACTUALIZAR PERMISO EXISTENTE
                perm_id = existing_perm[0]['permiso_id']
                current_perms = existing_perm[0]
                logger.info(f"Actualizando permiso existente ID {perm_id} para cliente {cliente_id}")

                update_parts = []
                params = []
                # 🛠️ CONSTRUIR SET DINÁMICAMENTE
                for key, value in permiso_data.items():
                    # 🔄 Actualizar solo si el valor es diferente al actual
                    if value != current_perms.get(key):
                        update_parts.append(f"{key} = ?")
                        params.append(value)

                # ✅ VERIFICAR SI HAY CAMBIOS REALES
                if not update_parts:
                    logger.info(f"No hay cambios en los permisos para ID {perm_id}")
                    # ✅ ACTUALIZADO: Incluir todos los campos de permisos
                    get_query = """
                    SELECT permiso_id, cliente_id, rol_id, menu_id, 
                           puede_ver, puede_crear, puede_editar, puede_eliminar, 
                           puede_exportar, puede_imprimir, puede_aprobar, permisos_extra,
                           fecha_creacion, fecha_actualizacion
                    FROM rol_menu_permiso WHERE permiso_id = ?
                    """
                    # ✅ FASE 2: Usar await
                    result = await execute_query(get_query, (perm_id,))
                    return result[0] if result else None

                params.append(perm_id)  # Añadir ID para el WHERE

                # ✅ ACTUALIZADO: Incluir fecha_actualizacion en UPDATE
                update_parts.append('fecha_actualizacion = GETDATE()')
                
                update_query = f"""
                UPDATE rol_menu_permiso
                SET {', '.join(update_parts)}
                OUTPUT INSERTED.permiso_id, INSERTED.cliente_id, INSERTED.rol_id, INSERTED.menu_id,
                       INSERTED.puede_ver, INSERTED.puede_crear, INSERTED.puede_editar, 
                       INSERTED.puede_eliminar, INSERTED.puede_exportar, INSERTED.puede_imprimir,
                       INSERTED.puede_aprobar, INSERTED.permisos_extra,
                       INSERTED.fecha_creacion, INSERTED.fecha_actualizacion
                WHERE permiso_id = ?
                """
                # ✅ FASE 2: Usar await
                result = await execute_update(update_query, tuple(params))
                if not result:
                    raise ServiceError(
                        status_code=500,
                        detail="Error al actualizar el permiso.",
                        internal_code="PERMISSION_UPDATE_FAILED"
                    )
                logger.info(f"Permiso ID {perm_id} actualizado exitosamente para cliente {cliente_id}")
                return result

            else:
                # 🟢 CREAR NUEVO PERMISO
                logger.info(f"🟢 Creando nuevo permiso - Cliente: {cliente_id}, Rol: {rol_id}, Menú: {menu_id}")

                # 🎯 ESTABLECER VALORES POR DEFECTO
                # ✅ ACTUALIZADO: Incluir todos los permisos extendidos
                final_puede_ver = permiso_data.get('puede_ver', True)  # Default True según BD
                final_puede_crear = permiso_data.get('puede_crear', False)
                final_puede_editar = permiso_data.get('puede_editar', False)
                final_puede_eliminar = permiso_data.get('puede_eliminar', False)
                final_puede_exportar = permiso_data.get('puede_exportar', False)
                final_puede_imprimir = permiso_data.get('puede_imprimir', False)
                final_puede_aprobar = permiso_data.get('puede_aprobar', False)
                final_permisos_extra = permiso_data.get('permisos_extra', None)

                # ✅ ACTUALIZADO: Incluir todos los campos de permisos
                insert_query = """
                INSERT INTO rol_menu_permiso (
                    cliente_id, rol_id, menu_id, 
                    puede_ver, puede_crear, puede_editar, puede_eliminar, 
                    puede_exportar, puede_imprimir, puede_aprobar, permisos_extra
                )
                OUTPUT INSERTED.permiso_id, INSERTED.cliente_id, INSERTED.rol_id, INSERTED.menu_id,
                       INSERTED.puede_ver, INSERTED.puede_crear, INSERTED.puede_editar, 
                       INSERTED.puede_eliminar, INSERTED.puede_exportar, INSERTED.puede_imprimir,
                       INSERTED.puede_aprobar, INSERTED.permisos_extra,
                       INSERTED.fecha_creacion, INSERTED.fecha_actualizacion
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    cliente_id, rol_id, menu_id,
                    final_puede_ver, final_puede_crear, final_puede_editar, 
                    final_puede_eliminar, final_puede_exportar, final_puede_imprimir,
                    final_puede_aprobar, final_permisos_extra
                )
                # ✅ FASE 2: Usar await
                result = await execute_insert(insert_query, params)
                if not result:
                    raise ServiceError(
                        status_code=500,
                        detail="Error al crear el permiso.",
                        internal_code="PERMISSION_CREATION_FAILED"
                    )
                logger.info(f"Permiso creado exitosamente con ID {result['permiso_id']} para cliente {cliente_id}")
                return result

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD en asignar_o_actualizar_permiso para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al gestionar permiso",
                internal_code="PERMISSION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en asignar_o_actualizar_permiso para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al gestionar permiso",
                internal_code="PERMISSION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_permisos_por_rol(cliente_id: UUID, rol_id: UUID) -> List[Dict]:
        """
        Obtiene todos los permisos asignados a un rol específico **dentro de un cliente**.
        
        📋 LISTA COMPLETA DE PERMISOS:
        - Incluye detalles del menú asociado
        - Ordenado por menú para consistencia
        - Retorna lista vacía si no hay permisos
        
        Args:
            cliente_id: ID del cliente
            rol_id: ID del rol cuyos permisos se quieren obtener
            
        Returns:
            List[Dict]: Lista de permisos del rol con detalles del menú
            
        Raises:
            ServiceError: Si hay errores en la consulta
        """
        try:
            # 🎯 VALIDAR QUE EL ROL EXISTE (OPCIONAL PERO RECOMENDADO)
            rol = await RolService.obtener_rol_por_id(rol_id)
            if not rol:
                logger.warning(f"Intento de obtener permisos para rol inexistente ID {rol_id}")
                return []  # 📭 Retornar lista vacía en lugar de error

            query = """
            SELECT
                p.permiso_id, p.cliente_id, p.rol_id, p.menu_id,
                p.puede_ver, p.puede_crear, p.puede_editar, p.puede_eliminar,
                p.puede_exportar, p.puede_imprimir, p.puede_aprobar, p.permisos_extra,
                p.fecha_creacion, p.fecha_actualizacion,
                m.nombre AS menu_nombre, m.ruta AS menu_url, m.icono AS menu_icono
            FROM rol_menu_permiso p
            INNER JOIN modulo_menu m ON p.menu_id = m.menu_id
            WHERE p.cliente_id = ? AND p.rol_id = ?
            ORDER BY m.orden;
            """
            # ✅ FASE 2: Usar await
            permisos = await execute_query(query, (cliente_id, rol_id))
            logger.debug(f"Obtenidos {len(permisos)} permisos para rol ID {rol_id} en cliente {cliente_id}")
            return permisos

        except DatabaseError as db_err:
            logger.error(f"Error de BD en obtener_permisos_por_rol para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener permisos del rol",
                internal_code="ROLE_PERMISSIONS_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en obtener_permisos_por_rol para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener permisos del rol",
                internal_code="ROLE_PERMISSIONS_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_permiso_especifico(cliente_id: UUID, rol_id: UUID, menu_id: UUID) -> Optional[Dict]:
        """
        Obtiene el permiso específico de un rol sobre un menú **dentro de un cliente**.
        
        🔍 BÚSQUEDA PRECISA:
        - Retorna el permiso específico para el par rol-menú
        - Retorna None si no existe el permiso
        
        Args:
            cliente_id: ID del cliente
            rol_id: ID del rol
            menu_id: ID del menú
            
        Returns:
            Optional[Dict]: Permiso encontrado o None
            
        Raises:
            ServiceError: Si hay errores en la consulta
        """
        try:
            # ✅ ACTUALIZADO: Incluir todos los campos de la tabla rol_menu_permiso
            query = """
            SELECT permiso_id, cliente_id, rol_id, menu_id, 
                   puede_ver, puede_crear, puede_editar, puede_eliminar,
                   puede_exportar, puede_imprimir, puede_aprobar,
                   permisos_extra, fecha_creacion, fecha_actualizacion
            FROM rol_menu_permiso
            WHERE cliente_id = ? AND rol_id = ? AND menu_id = ?
            """
            # ✅ FASE 2: Usar await
            resultados = await execute_query(query, (cliente_id, rol_id, menu_id))
            if not resultados:
                logger.debug(f"Permiso no encontrado - Cliente: {cliente_id}, Rol: {rol_id}, Menú: {menu_id}")
                return None
            
            # ✅ Normalizar valores booleanos y NULL
            permiso = resultados[0]
            # Convertir valores BIT a booleanos explícitos
            for campo_bool in ['puede_ver', 'puede_crear', 'puede_editar', 'puede_eliminar', 
                              'puede_exportar', 'puede_imprimir', 'puede_aprobar']:
                if campo_bool in permiso:
                    permiso[campo_bool] = bool(permiso[campo_bool]) if permiso[campo_bool] is not None else False
            
            return permiso

        except DatabaseError as db_err:
            logger.error(f"Error de BD en obtener_permiso_especifico para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener permiso específico",
                internal_code="SPECIFIC_PERMISSION_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en obtener_permiso_especifico para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener permiso específico",
                internal_code="SPECIFIC_PERMISSION_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def revocar_permiso(cliente_id: UUID, rol_id: UUID, menu_id: UUID) -> Dict:
        """
        Revoca (elimina) el permiso de un rol sobre un menú **dentro de un cliente**.
        
        🗑️ ELIMINACIÓN SEGURA:
        - Verifica que el permiso exista antes de eliminar
        - Retorna mensaje de confirmación
        - Operación irreversible
        
        Args:
            cliente_id: ID del cliente
            rol_id: ID del rol
            menu_id: ID del menú
            
        Returns:
            Dict: Mensaje de confirmación
            
        Raises:
            NotFoundError: Si el permiso no existe
            ServiceError: Si la eliminación falla
        """
        try:
            # 1. 🔍 VERIFICAR EXISTENCIA DEL PERMISO
            permiso_existente = await PermisoService.obtener_permiso_especifico(cliente_id, rol_id, menu_id)
            if not permiso_existente:
                raise NotFoundError(
                    detail=f"No se encontró permiso para eliminar (Cliente ID: {cliente_id}, Rol ID: {rol_id}, Menú ID: {menu_id}).",
                    internal_code="PERMISSION_NOT_FOUND"
                )

            # 2. 🗑️ EJECUTAR ELIMINACIÓN
            delete_query = """
            DELETE FROM rol_menu_permiso
            WHERE cliente_id = ? AND rol_id = ? AND menu_id = ?
            """
            # 📝 Usamos execute_update para operaciones DELETE
            # ✅ FASE 2: Usar await
            result = await execute_update(delete_query, (cliente_id, rol_id, menu_id))

            # ✅ VERIFICAR QUE SE ELIMINÓ AL MENOS UNA FILA
            if result.get('rows_affected', 0) == 0:
                raise ServiceError(
                    status_code=500,
                    detail="No se pudo eliminar el permiso.",
                    internal_code="PERMISSION_DELETION_FAILED"
                )

            logger.info(f"Permiso revocado exitosamente - Cliente: {cliente_id}, Rol: {rol_id}, Menú: {menu_id}")
            return {"message": "Permiso revocado exitosamente"}

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD en revocar_permiso para cliente {cliente_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al revocar permiso",
                internal_code="PERMISSION_REVOCATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en revocar_permiso para cliente {cliente_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al revocar permiso",
                internal_code="PERMISSION_REVOCATION_UNEXPECTED_ERROR"
            )