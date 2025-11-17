# app/services/usuario_service.py
from datetime import datetime
import math
from typing import Dict, List, Optional, Any
import logging

# 🗄️ IMPORTACIONES DE BASE DE DATOS
from app.db.queries import (
    execute_query, execute_insert, execute_update, execute_auth_query,
    SELECT_USUARIOS_PAGINATED, COUNT_USUARIOS_PAGINATED
)

# 📋 SCHEMAS
from app.schemas.usuario import UsuarioReadWithRoles, PaginatedUsuarioResponse
from app.schemas.rol import RolRead

# 🔐 SEGURIDAD
from app.core.security import get_password_hash

# 🚨 EXCEPCIONES - Nuevo sistema de manejo de errores
from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, ServiceError, DatabaseError
)

# 🏗️ BASE SERVICE - Clase base para manejo consistente de errores
from app.services.base_service import BaseService

# 👥 SERVICIOS RELACIONADOS
from app.services.rol_service import RolService

logger = logging.getLogger(__name__)

class UsuarioService(BaseService):
    """
    Servicio para gestión completa de usuarios del sistema en arquitectura multi-tenant.
    
    ⚠️ IMPORTANTE: Este servicio maneja operaciones críticas relacionadas con:
    - Creación, actualización y eliminación de usuarios **por cliente**
    - Gestión de roles y permisos de usuarios
    - Autenticación y gestión de sesiones
    
    CARACTERÍSTICAS PRINCIPALES:
    - Herencia de BaseService para manejo automático de errores
    - Validaciones robustas de seguridad e integridad de datos **por cliente**
    - Manejo seguro de contraseñas con hash bcrypt
    - Logging detallado para auditoría de seguridad
    - Aislamiento total de datos por cliente_id
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_usuario_completo_por_id(cliente_id: int, usuario_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario completo por su ID incluyendo todos sus datos y roles activos.
        
        🔍 BÚSQUEDA COMPLETA:
        - Obtiene todos los datos básicos del usuario
        - Incluye información de roles asignados y activos
        - Retorna estructura unificada para el endpoint /me extendido
        
        Args:
            cliente_id: ID del cliente al que pertenece el usuario
            usuario_id: ID del usuario a buscar
            
        Returns:
            Optional[Dict[str, Any]]: Diccionario con datos completos del usuario y sus roles,
                                    o None si no existe
                                    
        Raises:
            ServiceError: Si hay errores en la consulta de base de datos
        """
        logger.info(f"Obteniendo usuario completo ID {usuario_id} para cliente {cliente_id}")
        
        try:
            # 🔍 CONSULTA UNIFICADA PARA USUARIO Y SUS ROLES
            query = """
            SELECT 
                -- 📋 DATOS BÁSICOS DEL USUARIO
                u.usuario_id,
                u.cliente_id,
                u.nombre_usuario,
                u.correo,
                u.nombre,
                u.apellido,
                u.dni,
                u.telefono,
                u.proveedor_autenticacion,
                u.es_activo,
                u.correo_confirmado,
                u.fecha_creacion,
                u.fecha_ultimo_acceso,
                u.fecha_actualizacion,
                
                -- 🎭 DATOS DE ROLES ASIGNADOS (si existen)
                r.rol_id,
                r.nombre as nombre_rol,
                r.descripcion as descripcion_rol,
                r.es_activo as rol_activo,
                ur.fecha_asignacion,
                ur.es_activo as asignacion_activa
                
            FROM dbo.usuario u
            -- 🔄 LEFT JOIN para incluir usuarios sin roles asignados
            LEFT JOIN dbo.usuario_rol ur ON u.usuario_id = ur.usuario_id 
                AND u.cliente_id = ur.cliente_id 
                AND ur.es_activo = 1
            LEFT JOIN dbo.rol r ON ur.rol_id = r.rol_id 
                AND r.es_activo = 1
            WHERE 
                u.usuario_id = ? 
                AND u.cliente_id = ? 
                AND u.es_eliminado = 0
            ORDER BY 
                u.usuario_id, 
                r.nombre
            """
            
            params = (usuario_id, cliente_id)
            resultados = execute_query(query, params)
            
            if not resultados:
                logger.warning(f"Usuario ID {usuario_id} no encontrado en cliente {cliente_id} o está eliminado")
                return None
            
            logger.debug(f"Encontradas {len(resultados)} filas para usuario ID {usuario_id}")
            
            # 🎯 ESTRUCTURA BASE DEL USUARIO (primera fila contiene datos del usuario)
            usuario_base = resultados[0]
            usuario_completo = {
                # 📋 DATOS PRINCIPALES
                "usuario_id": usuario_base['usuario_id'],
                "cliente_id": usuario_base['cliente_id'],
                "nombre_usuario": usuario_base['nombre_usuario'],
                "correo": usuario_base['correo'],
                "nombre": usuario_base.get('nombre'),
                "apellido": usuario_base.get('apellido'),
                "dni": usuario_base.get('dni'),
                "telefono": usuario_base.get('telefono'),
                "proveedor_autenticacion": usuario_base.get('proveedor_autenticacion', 'local'),
                
                # 🔐 ESTADOS Y FLAGS
                "es_activo": bool(usuario_base['es_activo']),
                "correo_confirmado": bool(usuario_base['correo_confirmado']),
                
                # 📅 DATOS TEMPORALES
                "fecha_creacion": usuario_base['fecha_creacion'],
                "fecha_ultimo_acceso": usuario_base.get('fecha_ultimo_acceso'),
                "fecha_actualizacion": usuario_base.get('fecha_actualizacion'),
                
                # 🎭 ROLES ASIGNADOS (se procesarán a continuación)
                "roles": []
            }
            
            # 🔄 PROCESAR ROLES ASIGNADOS
            roles_procesados = set()  # Para evitar duplicados
            
            for fila in resultados:
                rol_id = fila.get('rol_id')
                
                # ✅ SOLO AGREGAR ROLES VÁLIDOS Y ACTIVOS
                if (rol_id is not None and 
                    fila.get('asignacion_activa') and 
                    fila.get('rol_activo') and
                    rol_id not in roles_procesados):
                    
                    rol_info = {
                        "rol_id": rol_id,
                        "nombre": fila['nombre_rol'],
                        "descripcion": fila.get('descripcion_rol'),
                        "es_activo": True,
                        "fecha_asignacion": fila.get('fecha_asignacion'),
                        "fecha_creacion": None  # No disponible en esta consulta
                    }
                    
                    usuario_completo["roles"].append(rol_info)
                    roles_procesados.add(rol_id)
            
            logger.info(f"Usuario completo obtenido exitosamente: ID {usuario_id} con {len(usuario_completo['roles'])} roles activos")
            return usuario_completo
            
        except DatabaseError as db_err:
            logger.error(f"Error de BD en obtener_usuario_completo_por_id: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener información completa del usuario",
                internal_code="USER_COMPLETE_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en obtener_usuario_completo_por_id: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener información completa del usuario",
                internal_code="USER_COMPLETE_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def get_user_role_names(cliente_id: int, user_id: int) -> List[str]:
        """
        Obtiene solo los NOMBRES de roles activos para un usuario dentro de un cliente.
        
        🎯 OPTIMIZACIÓN: Diseñado específicamente para el endpoint de login
        donde solo se necesitan los nombres de roles, no toda la información.
        
        Args:
            cliente_id: ID del cliente al que pertenece el usuario
            user_id: ID del usuario cuyos roles se quieren obtener
            
        Returns:
            List[str]: Lista de nombres de roles activos del usuario
            
        Raises:
            ServiceError: Si hay errores en la consulta
        """
        role_names = []
        try:
            query = """
            SELECT r.nombre
            FROM dbo.rol r
            INNER JOIN dbo.usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = ? AND ur.cliente_id = ? AND ur.es_activo = 1 AND r.es_activo = 1;
            """
            
            results = execute_query(query, (user_id, cliente_id))
            
            if results:
                role_names = [row['nombre'] for row in results if 'nombre' in row]
                logger.debug(f"Roles obtenidos para usuario ID {user_id} (cliente {cliente_id}): {role_names}")
            else:
                logger.debug(f"No se encontraron roles activos para usuario ID {user_id} (cliente {cliente_id})")

        except DatabaseError as db_err:
            logger.error(f"Error de BD en get_user_role_names: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener nombres de roles",
                internal_code="ROLE_NAMES_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en get_user_role_names: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener nombres de roles",
                internal_code="ROLE_NAMES_RETRIEVAL_UNEXPECTED_ERROR"
            )

        return role_names

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_usuario_por_id(cliente_id: int, usuario_id: int) -> Optional[Dict]:
        """
        Obtiene un usuario por su ID dentro de un cliente (excluyendo eliminados).
        
        🔍 BÚSQUEDA SEGURA:
        - Solo retorna usuarios del cliente especificado y no eliminados
        - Incluye todos los datos básicos del usuario
        - Retorna None si no existe
        
        Args:
            cliente_id: ID del cliente
            usuario_id: ID del usuario a buscar
            
        Returns:
            Optional[Dict]: Datos del usuario o None si no existe
            
        Raises:
            ServiceError: Si hay errores en la consulta
        """
        try:
            query = """
            SELECT
                usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido,
                dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
                fecha_creacion, fecha_ultimo_acceso, fecha_actualizacion
            FROM dbo.usuario
            WHERE usuario_id = ? AND cliente_id = ? AND es_eliminado = 0
            """
            
            resultados = execute_query(query, (usuario_id, cliente_id))
            
            if not resultados:
                logger.debug(f"Usuario con ID {usuario_id} no encontrado en cliente {cliente_id} o está eliminado")
                return None

            return resultados[0]

        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener usuario {usuario_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener usuario",
                internal_code="USER_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al obtener usuario {usuario_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener usuario",
                internal_code="USER_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def verificar_usuario_existente(cliente_id: int, nombre_usuario: str, correo: str) -> bool:
        """
        Verifica si ya existe un usuario con el mismo nombre o correo **dentro del cliente**.
        
        🛡️ PREVENCIÓN DE DUPLICADOS:
        - Busca solo dentro del cliente especificado
        - Comparación insensible a mayúsculas/minúsculas
        - Identifica exactamente qué campo causa conflicto
        
        Args:
            cliente_id: ID del cliente
            nombre_usuario: Nombre de usuario a verificar
            correo: Correo electrónico a verificar
            
        Returns:
            bool: False si no existe conflicto (éxito)
            
        Raises:
            ConflictError: Si ya existe un usuario con ese nombre o correo en el cliente
        """
        try:
            query = """
            SELECT nombre_usuario, correo
            FROM dbo.usuario
            WHERE cliente_id = ? AND (LOWER(nombre_usuario) = LOWER(?) OR LOWER(correo) = LOWER(?))
            """
            
            params = (cliente_id, nombre_usuario.lower(), correo.lower())
            resultados = execute_query(query, params)

            if resultados:
                nombre_usuario_coincide = any(
                    r['nombre_usuario'].lower() == nombre_usuario.lower() 
                    for r in resultados
                )
                correo_coincide = any(
                    r['correo'].lower() == correo.lower() 
                    for r in resultados
                )

                if nombre_usuario_coincide:
                    raise ConflictError(
                        detail="El nombre de usuario ya está en uso en este cliente.",
                        internal_code="USERNAME_CONFLICT"
                    )
                if correo_coincide:
                    raise ConflictError(
                        detail="El correo electrónico ya está registrado en este cliente.",
                        internal_code="EMAIL_CONFLICT"
                    )

            return False
            
        except ConflictError:
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD en verificar_usuario_existente: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al verificar usuario existente",
                internal_code="USER_VERIFICATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en verificar_usuario_existente: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al verificar usuario existente",
                internal_code="USER_VERIFICATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_usuario(cliente_id: int, usuario_data: Dict) -> Dict:
        """
        Crea un nuevo usuario en el sistema **para un cliente específico**.
        
        🆕 CREACIÓN SEGURA:
        - Valida duplicados dentro del cliente
        - Aplica hash seguro a la contraseña
        - Establece valores por defecto seguros
        
        Args:
            cliente_id: ID del cliente
            usuario_data: Datos del usuario a crear (incluye contraseña en texto plano)
            
        Returns:
            Dict: Usuario creado (sin contraseña)
            
        Raises:
            ConflictError: Si el nombre de usuario o correo ya existen en el cliente
            ServiceError: Si la creación falla
        """
        logger.info(f"Intentando crear usuario para cliente {cliente_id}: {usuario_data.get('nombre_usuario')}")
        
        try:
            # 🚫 VALIDAR DUPLICADOS EN EL CLIENTE
            await UsuarioService.verificar_usuario_existente(
                cliente_id,
                usuario_data['nombre_usuario'],
                usuario_data['correo']
            )

            # 🔐 APLICAR HASH SEGURO A CONTRASEÑA
            hashed_password = get_password_hash(usuario_data['contrasena'])

            # 💾 EJECUTAR INSERCIÓN
            insert_query = """
            INSERT INTO dbo.usuario (
                cliente_id, nombre_usuario, correo, contrasena, nombre, apellido,
                dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado, es_eliminado
            )
            OUTPUT
                INSERTED.usuario_id, INSERTED.cliente_id, INSERTED.nombre_usuario, INSERTED.correo,
                INSERTED.nombre, INSERTED.apellido, INSERTED.dni, INSERTED.telefono,
                INSERTED.proveedor_autenticacion, INSERTED.es_activo, INSERTED.correo_confirmado,
                INSERTED.fecha_creacion
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0)
            """
            
            params = (
                cliente_id,
                usuario_data['nombre_usuario'],
                usuario_data['correo'],
                hashed_password,
                usuario_data.get('nombre'),
                usuario_data.get('apellido'),
                usuario_data.get('dni'),
                usuario_data.get('telefono'),
                usuario_data.get('proveedor_autenticacion', 'local')
            )
            
            result = execute_insert(insert_query, params)

            if not result:
                raise ServiceError(
                    status_code=500,
                    detail="No se pudo crear el usuario en la base de datos",
                    internal_code="USER_CREATION_FAILED"
                )

            logger.info(f"Usuario creado exitosamente con ID: {result.get('usuario_id')} para cliente {cliente_id}")
            return result

        except (ValidationError, ConflictError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al crear usuario: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al crear usuario",
                internal_code="USER_CREATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al crear usuario: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al crear usuario",
                internal_code="USER_CREATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_usuario(cliente_id: int, usuario_id: int, usuario_data: Dict) -> Dict:
        """
        Actualiza un usuario existente **dentro de un cliente** con validaciones de integridad.
        
        🔄 ACTUALIZACIÓN PARCIAL:
        - Solo actualiza campos proporcionados
        - Valida duplicados dentro del cliente si se cambian campos únicos
        - Actualiza automáticamente la fecha de modificación
        
        Args:
            cliente_id: ID del cliente
            usuario_id: ID del usuario a actualizar
            usuario_data: Campos a actualizar (parcial)
            
        Returns:
            Dict: Usuario actualizado
            
        Raises:
            NotFoundError: Si el usuario no existe en el cliente
            ConflictError: Si los nuevos datos causan conflictos dentro del cliente
            ServiceError: Si la actualización falla
        """
        logger.info(f"Intentando actualizar usuario ID: {usuario_id} en cliente {cliente_id}")

        try:
            # 🔍 VERIFICAR EXISTENCIA DEL USUARIO EN EL CLIENTE
            usuario_existente = await UsuarioService.obtener_usuario_por_id(cliente_id, usuario_id)
            if not usuario_existente:
                raise NotFoundError(
                    detail="Usuario no encontrado en este cliente",
                    internal_code="USER_NOT_FOUND"
                )

            # 🚫 VALIDAR DUPLICADOS EN EL CLIENTE SI SE CAMBIAN CAMPOS ÚNICOS
            check_duplicates = False
            if 'nombre_usuario' in usuario_data and usuario_data['nombre_usuario'] != usuario_existente.get('nombre_usuario'):
                check_duplicates = True
            if 'correo' in usuario_data and usuario_data['correo'] != usuario_existente.get('correo'):
                check_duplicates = True

            if check_duplicates:
                verify_query = """
                SELECT usuario_id, nombre_usuario, correo
                FROM dbo.usuario
                WHERE cliente_id = ? AND (nombre_usuario = ? OR correo = ?)
                AND usuario_id != ? AND es_eliminado = 0
                """
                check_nombre_usuario = usuario_data.get('nombre_usuario', usuario_existente.get('nombre_usuario'))
                check_correo = usuario_data.get('correo', usuario_existente.get('correo'))
                params_verify = (cliente_id, check_nombre_usuario, check_correo, usuario_id)
                duplicados = execute_query(verify_query, params_verify)

                if duplicados:
                    if any(d['nombre_usuario'] == check_nombre_usuario for d in duplicados):
                         raise ConflictError(
                             detail=f"El nombre de usuario '{check_nombre_usuario}' ya está en uso en este cliente.",
                             internal_code="USERNAME_CONFLICT"
                         )
                    if any(d['correo'] == check_correo for d in duplicados):
                         raise ConflictError(
                             detail=f"El correo '{check_correo}' ya está en uso en este cliente.",
                             internal_code="EMAIL_CONFLICT"
                         )

            # 🛠️ CONSTRUIR ACTUALIZACIÓN DINÁMICA
            update_parts = []
            params_update = []
            campos_permitidos = {
                'nombre_usuario', 'correo', 'nombre', 'apellido', 'dni', 'telefono',
                'proveedor_autenticacion', 'es_activo'
            }

            campos_actualizados = False
            for field in campos_permitidos:
                if field in usuario_data and usuario_data[field] is not None:
                    update_parts.append(f"{field} = ?")
                    params_update.append(usuario_data[field])
                    campos_actualizados = True

            if not campos_actualizados:
                logger.info(f"No hay campos válidos para actualizar para usuario ID {usuario_id}")
                raise ValidationError(
                    detail="No hay campos válidos para actualizar",
                    internal_code="NO_UPDATE_DATA"
                )

            update_parts.append("fecha_actualizacion = GETDATE()")
            params_update.append(cliente_id)
            params_update.append(usuario_id)

            # 💾 EJECUTAR ACTUALIZACIÓN
            update_query = f"""
            UPDATE dbo.usuario
            SET {', '.join(update_parts)}
            OUTPUT
                INSERTED.usuario_id, INSERTED.cliente_id, INSERTED.nombre_usuario, INSERTED.correo,
                INSERTED.nombre, INSERTED.apellido, INSERTED.dni, INSERTED.telefono,
                INSERTED.proveedor_autenticacion, INSERTED.es_activo, INSERTED.correo_confirmado,
                INSERTED.fecha_creacion, INSERTED.fecha_actualizacion
            WHERE cliente_id = ? AND usuario_id = ? AND es_eliminado = 0
            """
            
            result = execute_update(update_query, tuple(params_update))

            if not result:
                logger.warning(f"No se pudo actualizar el usuario ID {usuario_id}")
                raise ServiceError(
                    status_code=404,
                    detail="Error al actualizar el usuario, no encontrado o no se pudo modificar",
                    internal_code="USER_UPDATE_FAILED"
                )

            logger.info(f"Usuario ID {usuario_id} actualizado exitosamente en cliente {cliente_id}")
            return result

        except (ValidationError, NotFoundError, ConflictError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al actualizar usuario {usuario_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al actualizar usuario",
                internal_code="USER_UPDATE_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al actualizar usuario {usuario_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al actualizar usuario",
                internal_code="USER_UPDATE_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def eliminar_usuario(cliente_id: int, usuario_id: int) -> Dict:
        """
        Realiza un borrado lógico del usuario y desactiva sus roles.
        
        🗑️ ELIMINACIÓN SEGURA:
        - Borrado lógico (no físico)
        - Desactiva automáticamente al usuario
        - Desactiva todas sus asignaciones de roles
        
        Args:
            cliente_id: ID del cliente
            usuario_id: ID del usuario a eliminar
            
        Returns:
            Dict: Resultado de la eliminación con metadatos
            
        Raises:
            NotFoundError: Si el usuario no existe en el cliente
            ServiceError: Si la eliminación falla
        """
        logger.info(f"Intentando eliminar usuario ID: {usuario_id} en cliente {cliente_id}")

        try:
            # 🔍 VERIFICAR EXISTENCIA Y ESTADO
            check_query = "SELECT es_eliminado FROM dbo.usuario WHERE cliente_id = ? AND usuario_id = ?"
            user_status = execute_query(check_query, (cliente_id, usuario_id))

            if not user_status:
                 raise NotFoundError(
                     detail="Usuario no encontrado en este cliente",
                     internal_code="USER_NOT_FOUND"
                 )
                 
            if user_status[0]['es_eliminado']:
                 logger.info(f"Usuario ID {usuario_id} ya estaba eliminado en cliente {cliente_id}")
                 return {
                     "message": "Usuario ya estaba eliminado", 
                     "usuario_id": usuario_id
                 }

            # 💾 EJECUTAR BORRADO LÓGICO
            update_query = """
            UPDATE dbo.usuario
            SET es_eliminado = 1, es_activo = 0, fecha_actualizacion = GETDATE()
            OUTPUT INSERTED.usuario_id, INSERTED.nombre_usuario, INSERTED.es_eliminado
            WHERE cliente_id = ? AND usuario_id = ? AND es_eliminado = 0
            """
            
            result = execute_update(update_query, (cliente_id, usuario_id))

            if not result:
                logger.warning(f"No se pudo eliminar lógicamente el usuario ID {usuario_id} en cliente {cliente_id}")
                raise ServiceError(
                    status_code=409,
                    detail="Conflicto al eliminar el usuario, posible concurrencia",
                    internal_code="USER_DELETION_CONFLICT"
                )

            # 🔄 DESACTIVAR ROLES ASOCIADOS
            try:
                deactivate_roles_query = """
                UPDATE dbo.usuario_rol SET es_activo = 0
                WHERE usuario_id = ? AND cliente_id = ?
                """
                execute_update(deactivate_roles_query, (usuario_id, cliente_id))
                logger.info(f"Roles desactivados para usuario eliminado ID {usuario_id} en cliente {cliente_id}")
            except Exception as role_error:
                 logger.error(f"Error desactivando roles para usuario {usuario_id}: {role_error}")
                 # 🟡 NO FALLAR LA ELIMINACIÓN PRINCIPAL POR ESTO

            logger.info(f"Usuario ID {usuario_id} eliminado lógicamente exitosamente en cliente {cliente_id}")
            return {
                "message": "Usuario eliminado lógicamente exitosamente",
                "usuario_id": result['usuario_id'],
                "es_eliminado": result['es_eliminado']
            }

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al eliminar usuario {usuario_id}: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al eliminar usuario",
                internal_code="USER_DELETION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al eliminar usuario {usuario_id}: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al eliminar usuario",
                internal_code="USER_DELETION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def asignar_rol_a_usuario(cliente_id: int, usuario_id: int, rol_id: int) -> Dict:
        """
        Asigna un rol a un usuario con validaciones completas.
        
        🔄 COMPORTAMIENTO INTELIGENTE:
        - Si la asignación existe e está inactiva: la reactiva
        - Si la asignación existe y está activa: retorna la existente
        - Si no existe: crea una nueva asignación
        
        Args:
            cliente_id: ID del cliente
            usuario_id: ID del usuario
            rol_id: ID del rol a asignar
            
        Returns:
            Dict: Asignación usuario-rol creada o reactivada
            
        Raises:
            NotFoundError: Si el usuario o rol no existen en el cliente
            ValidationError: Si el rol no está activo
            ServiceError: Si la asignación falla
        """
        logger.info(f"Intentando asignar rol {rol_id} a usuario {usuario_id} en cliente {cliente_id}")

        try:
            # 👤 VALIDAR QUE EL USUARIO EXISTE EN EL CLIENTE
            usuario = await UsuarioService.obtener_usuario_por_id(cliente_id, usuario_id)
            if not usuario:
                raise NotFoundError(
                    detail=f"Usuario con ID {usuario_id} no encontrado en cliente {cliente_id}.",
                    internal_code="USER_NOT_FOUND"
                )

            # 🎭 VALIDAR QUE EL ROL EXISTE Y ESTÁ ACTIVO
            rol = await RolService.obtener_rol_por_id(rol_id)
            if not rol:
                raise NotFoundError(
                    detail=f"Rol con ID {rol_id} no encontrado.",
                    internal_code="ROLE_NOT_FOUND"
                )
            if not rol['es_activo']:
                raise ValidationError(
                    detail=f"Rol con ID {rol_id} no está activo.",
                    internal_code="ROLE_INACTIVE"
                )

            # 🔍 VERIFICAR ASIGNACIÓN EXISTENTE
            check_query = """
            SELECT usuario_rol_id, es_activo
            FROM dbo.usuario_rol
            WHERE usuario_id = ? AND rol_id = ? AND cliente_id = ?
            """
            
            existing_assignment = execute_query(check_query, (usuario_id, rol_id, cliente_id))

            if existing_assignment:
                assignment = existing_assignment[0]
                
                if assignment['es_activo']:
                    # ✅ ASIGNACIÓN YA ACTIVA - Retornar existente
                    logger.info(f"Rol ID {rol_id} ya está asignado y activo para usuario ID {usuario_id} en cliente {cliente_id}")
                    get_assignment_query = """
                    SELECT usuario_rol_id, usuario_id, rol_id, fecha_asignacion, es_activo
                    FROM dbo.usuario_rol WHERE usuario_rol_id = ?
                    """
                    final_result = execute_query(get_assignment_query, (assignment['usuario_rol_id'],))
                    if not final_result:
                        raise ServiceError(
                            status_code=500,
                            detail="Error obteniendo datos de asignación existente",
                            internal_code="EXISTING_ASSIGNMENT_RETRIEVAL_ERROR"
                        )
                    return final_result[0]
                else:
                    # 🔄 REACTIVAR ASIGNACIÓN EXISTENTE
                    logger.info(f"Reactivando asignación existente para usuario {usuario_id}, rol {rol_id}")
                    update_query = """
                    UPDATE dbo.usuario_rol
                    SET es_activo = 1, fecha_asignacion = GETDATE()
                    OUTPUT INSERTED.usuario_rol_id, INSERTED.usuario_id, INSERTED.rol_id,
                           INSERTED.fecha_asignacion, INSERTED.es_activo
                    WHERE usuario_rol_id = ?
                    """
                    result = execute_update(update_query, (assignment['usuario_rol_id'],))
                    if not result:
                        raise ServiceError(
                            status_code=500,
                            detail="Error reactivando la asignación de rol",
                            internal_code="ROLE_REACTIVATION_ERROR"
                        )
                    logger.info(f"Asignación reactivada exitosamente")
                    return result
            else:
                # 🆕 CREAR NUEVA ASIGNACIÓN
                logger.info(f"Creando nueva asignación para usuario {usuario_id}, rol {rol_id}")
                insert_query = """
                INSERT INTO dbo.usuario_rol (usuario_id, rol_id, cliente_id, es_activo)
                OUTPUT INSERTED.usuario_rol_id, INSERTED.usuario_id, INSERTED.rol_id,
                       INSERTED.fecha_asignacion, INSERTED.es_activo
                VALUES (?, ?, ?, 1)
                """
                result = execute_insert(insert_query, (usuario_id, rol_id, cliente_id))
                if not result:
                    raise ServiceError(
                        status_code=500,
                        detail="Error creando la asignación de rol",
                        internal_code="ROLE_ASSIGNMENT_ERROR"
                    )
                logger.info(f"Asignación creada exitosamente")
                return result

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al asignar rol: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al asignar rol",
                internal_code="ROLE_ASSIGNMENT_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al asignar rol: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al asignar rol",
                internal_code="ROLE_ASSIGNMENT_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def revocar_rol_de_usuario(cliente_id: int, usuario_id: int, rol_id: int) -> Dict:
        """
        Revoca (desactiva) un rol asignado a un usuario.
        
        🚫 REVOCACIÓN SEGURA:
        - Verifica que la asignación exista
        - Evita operaciones redundantes
        - Mantiene el registro histórico
        
        Args:
            cliente_id: ID del cliente
            usuario_id: ID del usuario
            rol_id: ID del rol a revocar
            
        Returns:
            Dict: Asignación revocada
            
        Raises:
            NotFoundError: Si la asignación no existe
            ServiceError: Si la revocación falla
        """
        logger.info(f"Intentando revocar rol {rol_id} de usuario {usuario_id} en cliente {cliente_id}")

        try:
            # 🔍 VERIFICAR EXISTENCIA DE LA ASIGNACIÓN
            check_query = """
            SELECT usuario_rol_id, es_activo
            FROM dbo.usuario_rol
            WHERE usuario_id = ? AND rol_id = ? AND cliente_id = ?
            """
            
            existing_assignment = execute_query(check_query, (usuario_id, rol_id, cliente_id))

            if not existing_assignment:
                 raise NotFoundError(
                     detail=f"No existe asignación entre usuario ID {usuario_id} y rol ID {rol_id} en cliente {cliente_id}.",
                     internal_code="ASSIGNMENT_NOT_FOUND"
                 )

            assignment = existing_assignment[0]
            if not assignment['es_activo']:
                logger.info(f"La asignación ya estaba inactiva para usuario {usuario_id}, rol {rol_id}")
                get_assignment_query = """
                SELECT usuario_rol_id, usuario_id, rol_id, fecha_asignacion, es_activo
                FROM dbo.usuario_rol WHERE usuario_rol_id = ?
                """
                final_result = execute_query(get_assignment_query, (assignment['usuario_rol_id'],))
                return final_result[0] if final_result else {"message": "Asignación ya inactiva"}

            # 🗑️ DESACTIVAR LA ASIGNACIÓN
            logger.info(f"Desactivando asignación para usuario {usuario_id}, rol {rol_id}")
            update_query = """
            UPDATE dbo.usuario_rol
            SET es_activo = 0
            OUTPUT INSERTED.usuario_rol_id, INSERTED.usuario_id, INSERTED.rol_id,
                   INSERTED.fecha_asignacion, INSERTED.es_activo
            WHERE usuario_rol_id = ? AND es_activo = 1
            """
            
            result = execute_update(update_query, (assignment['usuario_rol_id'],))

            if not result:
                logger.warning(f"No se pudo desactivar la asignación ID {assignment['usuario_rol_id']}")
                get_assignment_query = """
                SELECT usuario_rol_id, usuario_id, rol_id, fecha_asignacion, es_activo
                FROM dbo.usuario_rol WHERE usuario_rol_id = ?
                """
                final_result = execute_query(get_assignment_query, (assignment['usuario_rol_id'],))
                return final_result[0] if final_result else {"message": "No se pudo desactivar la asignación"}

            logger.info(f"Asignación desactivada exitosamente")
            return result

        except (ValidationError, NotFoundError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD al revocar rol: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al revocar rol",
                internal_code="ROLE_REVOCATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al revocar rol: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al revocar rol",
                internal_code="ROLE_REVOCATION_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_roles_de_usuario(cliente_id: int, usuario_id: int) -> List[Dict]:
        """
        Obtiene la lista completa de roles activos asignados a un usuario.
        
        📋 LISTA DETALLADA:
        - Incluye todos los datos del rol
        - Solo roles activos (usuario y rol)
        - Ordenado por nombre del rol
        
        Args:
            cliente_id: ID del cliente
            usuario_id: ID del usuario cuyos roles se quieren obtener
            
        Returns:
            List[Dict]: Lista de roles activos del usuario
            
        Raises:
            ServiceError: Si hay errores en la consulta
        """
        try:
            query = """
            SELECT
                r.rol_id, r.nombre, r.descripcion, r.es_activo, r.fecha_creacion
            FROM dbo.rol r
            INNER JOIN dbo.usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = ? AND ur.cliente_id = ? AND ur.es_activo = 1 AND r.es_activo = 1
            ORDER BY r.nombre;
            """
            
            roles = execute_query(query, (usuario_id, cliente_id))
            logger.debug(f"Obtenidos {len(roles)} roles activos para usuario ID {usuario_id} en cliente {cliente_id}")
            return roles

        except DatabaseError as db_err:
            logger.error(f"Error de BD al obtener roles: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener roles del usuario",
                internal_code="USER_ROLES_RETRIEVAL_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado al obtener roles: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener roles del usuario",
                internal_code="USER_ROLES_RETRIEVAL_UNEXPECTED_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def get_usuarios_paginated(
        cliente_id: int,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Dict:
        """
        Obtiene una lista paginada de usuarios con sus roles.
        
        📊 PAGINACIÓN EFICIENTE:
        - Combina datos de usuario y roles en consultas optimizadas
        - Búsqueda en múltiples campos
        - Metadatos completos de paginación
        
        Args:
            cliente_id: ID del cliente
            page: Número de página (comienza en 1)
            limit: Número de usuarios por página
            search: Término de búsqueda opcional
            
        Returns:
            Dict: Respuesta paginada con usuarios y metadatos
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            ServiceError: Si hay errores en la consulta
        """
        logger.info(f"Obteniendo usuarios paginados para cliente {cliente_id}: page={page}, limit={limit}, search='{search}'")

        # 🚫 VALIDAR PARÁMETROS
        if page < 1:
            raise ValidationError(
                detail="El número de página debe ser mayor o igual a 1.",
                internal_code="INVALID_PAGE_NUMBER"
            )
        if limit < 1:
            raise ValidationError(
                detail="El límite por página debe ser mayor o igual a 0.",
                internal_code="INVALID_LIMIT"
            )

        offset = (page - 1) * limit
        search_param = f"%{search}%" if search else None

        try:
            # 📊 CONTAR TOTAL DE USUARIOS
            count_params = (cliente_id, search_param, search_param, search_param, search_param, search_param)
            count_result = execute_query(COUNT_USUARIOS_PAGINATED, count_params)

            if not count_result or not isinstance(count_result, list) or len(count_result) == 0:
                logger.error("Error al contar usuarios: resultado inesperado")
                raise ServiceError(
                    status_code=500,
                    detail="Error al obtener el total de usuarios",
                    internal_code="USER_COUNT_ERROR"
                )

            # 🎯 EXTRAER TOTAL DE FORMA ROBUSTA
            total_usuarios = count_result[0].get('') 
            if total_usuarios is None:
                try:
                    total_usuarios = list(count_result[0].values())[0]
                except (IndexError, AttributeError):
                    logger.error(f"No se pudo extraer el total de usuarios: {count_result[0]}")
                    raise ServiceError(
                        status_code=500,
                        detail="Error al interpretar el total de usuarios",
                        internal_code="USER_COUNT_PARSING_ERROR"
                    )

            logger.debug(f"Total de usuarios encontrados para cliente {cliente_id}: {total_usuarios}")

            # 📋 OBTENER DATOS PAGINADOS CON ROLES
            data_params = (search_param, search_param, search_param, search_param, search_param, offset, limit, cliente_id)
            raw_results = execute_query(SELECT_USUARIOS_PAGINATED, data_params)

            # 🎯 PROCESAR RESULTADOS - AGRUPAR ROLES POR USUARIO
            usuarios_dict: Dict[int, UsuarioReadWithRoles] = {}
            
            if raw_results:
                logger.debug(f"Procesando {len(raw_results)} filas crudas")
                
                for row in raw_results:
                    usuario_id = row['usuario_id']
                    
                    if usuario_id not in usuarios_dict:
                        # 🆕 CREAR ENTRADA DE USUARIO
                        usuarios_dict[usuario_id] = UsuarioReadWithRoles(
                            usuario_id=row['usuario_id'],
                            nombre_usuario=row['nombre_usuario'],
                            correo=row['correo'],
                            nombre=row.get('nombre'),
                            apellido=row.get('apellido'),
                            es_activo=row['es_activo'],
                            correo_confirmado=row['correo_confirmado'],
                            fecha_creacion=row['fecha_creacion'],
                            fecha_ultimo_acceso=row.get('fecha_ultimo_acceso'),
                            fecha_actualizacion=row.get('fecha_actualizacion'),
                            roles=[]
                        )

                    # ➕ AGREGAR ROL SI EXISTE
                    if row.get('rol_id') is not None:
                        rol_obj = RolRead(
                            rol_id=row['rol_id'],
                            nombre=row['nombre_rol'],
                            descripcion=None,
                            es_activo=True,
                            fecha_creacion=datetime.now()
                        )
                        
                        # 🚫 EVITAR DUPLICADOS
                        if rol_obj not in usuarios_dict[usuario_id].roles:
                            usuarios_dict[usuario_id].roles.append(rol_obj)

            lista_usuarios_procesados = list(usuarios_dict.values())
            logger.debug(f"Procesados {len(lista_usuarios_procesados)} usuarios únicos")

            # 🧮 CALCULAR METADATOS DE PAGINACIÓN
            total_paginas = math.ceil(total_usuarios / limit) if limit > 0 else 0

            # 📦 CONSTRUIR RESPUESTA FINAL
            response_data = {
                "usuarios": [u.model_dump() for u in lista_usuarios_procesados],
                "total_usuarios": total_usuarios,
                "pagina_actual": page,
                "total_paginas": total_paginas
            }

            logger.info(f"Obtención paginada de usuarios completada exitosamente")
            return response_data

        except (ValidationError, ServiceError):
            raise
        except DatabaseError as db_err:
            logger.error(f"Error de BD en get_usuarios_paginated: {db_err.detail}")
            raise ServiceError(
                status_code=500,
                detail="Error de base de datos al obtener usuarios paginados",
                internal_code="USER_PAGINATION_DB_ERROR"
            )
        except Exception as e:
            logger.exception(f"Error inesperado en get_usuarios_paginated: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno al obtener usuarios paginados",
                internal_code="USER_PAGINATION_UNEXPECTED_ERROR"
            )