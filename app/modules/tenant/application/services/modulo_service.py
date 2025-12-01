# app/services/modulo_service.py
"""
Servicio para la gestión del catálogo de módulos del sistema multi-tenant.
Este servicio implementa la lógica de negocio para operaciones sobre la entidad `cliente_modulo`,
incluyendo la gestión del catálogo de módulos disponibles, validación de códigos únicos,
y consultas optimizadas para activación por cliente.

Características clave:
- Gestión centralizada del catálogo de módulos del sistema
- Validación de códigos de módulo únicos
- Consultas optimizadas para activación por cliente
- Soporte para módulos core y módulos opcionales con licencia
- Total coherencia con los patrones de BaseService y manejo de excepciones del sistema
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
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
from app.modules.tenant.presentation.schemas import ModuloCreate, ModuloUpdate, ModuloRead
from app.infrastructure.database.connection import DatabaseConnection

if TYPE_CHECKING:
    from app.modules.tenant.presentation.schemas import ModuloConInfoActivacion

logger = logging.getLogger(__name__)


class ModuloService(BaseService):
    """
    Servicio central para la administración del catálogo de módulos del sistema.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos(
        skip: int = 0, 
        limit: int = 100,
        solo_activos: bool = True
    ) -> List[ModuloRead]:
        """
        Obtiene la lista de módulos del sistema con paginación.
        """
        logger.info(f"Obteniendo catálogo de módulos - skip: {skip}, limit: {limit}")

        where_clause = "WHERE es_activo = 1" if solo_activos else ""
        query = f"""
        SELECT 
            modulo_id, codigo_modulo, nombre, descripcion, icono,
            es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
        FROM cliente_modulo
        {where_clause}
        ORDER BY orden, nombre
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        resultados = execute_query(query, (skip, limit), connection_type=DatabaseConnection.ADMIN)
        return [ModuloRead(**modulo) for modulo in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_por_id(modulo_id: int) -> Optional[ModuloRead]:
        """
        Obtiene un módulo específico por su ID.
        """
        query = """
        SELECT 
            modulo_id, codigo_modulo, nombre, descripcion, icono,
            es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
        FROM cliente_modulo
        WHERE modulo_id = ?
        """
        
        resultado = execute_query(query, (modulo_id,), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            return None
        return ModuloRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulo_por_codigo(codigo_modulo: str) -> Optional[ModuloRead]:
        """
        Obtiene un módulo específico por su código único.
        """
        if not codigo_modulo:
            raise ValidationError(
                detail="El código de módulo es obligatorio.",
                internal_code="MODULE_CODE_REQUIRED"
            )

        query = """
        SELECT 
            modulo_id, codigo_modulo, nombre, descripcion, icono,
            es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
        FROM cliente_modulo
        WHERE codigo_modulo = ?
        """
        
        resultado = execute_query(query, (codigo_modulo,), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            return None
        return ModuloRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_codigo_modulo_unico(codigo_modulo: str, modulo_id: Optional[int] = None) -> None:
        """
        Valida que el código de módulo sea único en el sistema.
        """
        query = "SELECT modulo_id FROM cliente_modulo WHERE codigo_modulo = ?"
        params = [codigo_modulo]
        
        if modulo_id:
            query += " AND modulo_id != ?"
            params.append(modulo_id)
            
        resultado = execute_query(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if resultado:
            raise ConflictError(
                detail=f"El código de módulo '{codigo_modulo}' ya está en uso.",
                internal_code="MODULE_CODE_CONFLICT"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_modulo(modulo_data: ModuloCreate) -> ModuloRead:
        """
        Crea un nuevo módulo en el catálogo del sistema.
        """
        logger.info(f"Creando nuevo módulo: {modulo_data.nombre}")

        # Validaciones de unicidad
        await ModuloService._validar_codigo_modulo_unico(modulo_data.codigo_modulo)

        # Preparar datos para inserción
        fields = [
            'codigo_modulo', 'nombre', 'descripcion', 'icono',
            'es_modulo_core', 'requiere_licencia', 'orden', 'es_activo'
        ]
        params = [getattr(modulo_data, field) for field in fields]

        query = f"""
        INSERT INTO cliente_modulo ({', '.join(fields)})
        OUTPUT 
            INSERTED.modulo_id,
            INSERTED.codigo_modulo,
            INSERTED.nombre,
            INSERTED.descripcion,
            INSERTED.icono,
            INSERTED.es_modulo_core,
            INSERTED.requiere_licencia,
            INSERTED.orden,
            INSERTED.es_activo,
            INSERTED.fecha_creacion
        VALUES ({', '.join(['?'] * len(fields))})
        """

        resultado = execute_insert(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear el módulo en la base de datos.",
                internal_code="MODULE_CREATION_FAILED"
            )

        logger.info(f"Módulo creado exitosamente con ID: {resultado['modulo_id']}")
        return ModuloRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_modulo(modulo_id: int, modulo_data: ModuloUpdate) -> ModuloRead:
        """
        Actualiza un módulo existente en el catálogo del sistema.
        """
        logger.info(f"Actualizando módulo ID: {modulo_id}")

        # Verificar que el módulo existe
        modulo_existente = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo_existente:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar unicidad si se está actualizando el código
        if modulo_data.codigo_modulo and modulo_data.codigo_modulo != modulo_existente.codigo_modulo:
            await ModuloService._validar_codigo_modulo_unico(modulo_data.codigo_modulo, modulo_id)

        # Construir query dinámica basada en los campos proporcionados
        update_fields = []
        params = []
        
        for field, value in modulo_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ?")
                params.append(value)
                
        if not update_fields:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )
            
        params.append(modulo_id)

        query = f"""
        UPDATE cliente_modulo
        SET {', '.join(update_fields)}, fecha_creacion = fecha_creacion
        OUTPUT 
            INSERTED.modulo_id,
            INSERTED.codigo_modulo,
            INSERTED.nombre,
            INSERTED.descripcion,
            INSERTED.icono,
            INSERTED.es_modulo_core,
            INSERTED.requiere_licencia,
            INSERTED.orden,
            INSERTED.es_activo,
            INSERTED.fecha_creacion
        WHERE modulo_id = ?
        """

        resultado = execute_update(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar el módulo.",
                internal_code="MODULE_UPDATE_FAILED"
            )

        logger.info(f"Módulo ID {modulo_id} actualizado exitosamente.")
        return ModuloRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos_por_cliente(cliente_id: int) -> List['ModuloConInfoActivacion']:
        """
        Obtiene todos los módulos con información de activación para un cliente específico.
        Retorna objetos ModuloConInfoActivacion con toda la información de activación.
        """
        from app.modules.tenant.presentation.schemas import ModuloConInfoActivacion  # Import local para evitar circular
        
        logger.info(f"Obteniendo módulos para cliente ID: {cliente_id}")

        query = """
        SELECT 
            m.modulo_id,
            m.codigo_modulo,
            m.nombre,
            m.descripcion,
            m.icono,
            m.es_modulo_core,
            m.requiere_licencia,
            m.orden,
            m.es_activo as modulo_activo,
            m.fecha_creacion,
            ISNULL(cma.esta_activo, 0) as activo_en_cliente,
            cma.cliente_modulo_activo_id,
            cma.fecha_activacion,
            cma.fecha_vencimiento,
            cma.configuracion_json,
            cma.limite_usuarios,
            cma.limite_registros
        FROM cliente_modulo m
        LEFT JOIN cliente_modulo_activo cma ON m.modulo_id = cma.modulo_id AND cma.cliente_id = ?
        WHERE m.es_activo = 1
        ORDER BY m.orden, m.nombre
        """
        
        resultados = execute_query(query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        
        # Mapear resultados a ModuloConInfoActivacion
        modulos = []
        for row in resultados:
            # Mapear modulo_activo a es_activo
            modulo_data = dict(row)
            modulo_data['es_activo'] = modulo_data.pop('modulo_activo', True)
            
            # Convertir activo_en_cliente de int (0/1) a bool
            if 'activo_en_cliente' in modulo_data:
                modulo_data['activo_en_cliente'] = bool(modulo_data['activo_en_cliente'])
            
            modulos.append(ModuloConInfoActivacion(**modulo_data))
        
        return modulos

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_modulos_core() -> List[ModuloRead]:
        """
        Obtiene todos los módulos core del sistema.
        """
        logger.info("Obteniendo módulos core del sistema")

        query = """
        SELECT 
            modulo_id, codigo_modulo, nombre, descripcion, icono,
            es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
        FROM cliente_modulo
        WHERE es_modulo_core = 1 AND es_activo = 1
        ORDER BY orden, nombre
        """
        
        resultados = execute_query(query, connection_type=DatabaseConnection.ADMIN)
        return [ModuloRead(**modulo) for modulo in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def contar_modulos(solo_activos: bool = True) -> int:
        """
        Cuenta el total de módulos en el sistema.
        Útil para implementar paginación completa en el frontend.
        """
        logger.info("Contando total de módulos en el sistema")

        where_clause = "WHERE es_activo = 1" if solo_activos else ""
        query = f"""
        SELECT COUNT(*) as total
        FROM cliente_modulo
        {where_clause}
        """
        
        resultado = execute_query(query, connection_type=DatabaseConnection.ADMIN)
        return resultado[0]['total'] if resultado else 0

    @staticmethod
    @BaseService.handle_service_errors
    async def buscar_modulos(
        buscar: Optional[str] = None,
        es_modulo_core: Optional[bool] = None,
        requiere_licencia: Optional[bool] = None,
        solo_activos: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModuloRead]:
        """
        Busca módulos con filtros opcionales.
        Permite buscar por nombre, código o descripción, y filtrar por características.
        """
        logger.info(f"Buscando módulos con filtros - buscar: {buscar}, core: {es_modulo_core}, licencia: {requiere_licencia}")

        # Construir cláusulas WHERE dinámicamente
        where_clauses = []
        params = []

        if solo_activos:
            where_clauses.append("es_activo = 1")

        if buscar:
            where_clauses.append("(nombre LIKE ? OR codigo_modulo LIKE ? OR descripcion LIKE ?)")
            search_pattern = f"%{buscar}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        if es_modulo_core is not None:
            where_clauses.append("es_modulo_core = ?")
            params.append(1 if es_modulo_core else 0)

        if requiere_licencia is not None:
            where_clauses.append("requiere_licencia = ?")
            params.append(1 if requiere_licencia else 0)

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
        SELECT 
            modulo_id, codigo_modulo, nombre, descripcion, icono,
            es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
        FROM cliente_modulo
        {where_clause}
        ORDER BY orden, nombre
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        params.extend([skip, limit])
        resultados = execute_query(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        return [ModuloRead(**modulo) for modulo in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def contar_modulos_busqueda(
        buscar: Optional[str] = None,
        es_modulo_core: Optional[bool] = None,
        requiere_licencia: Optional[bool] = None,
        solo_activos: bool = True
    ) -> int:
        """
        Cuenta el total de módulos que coinciden con los criterios de búsqueda.
        Útil para paginación en búsquedas filtradas.
        """
        logger.info("Contando módulos con filtros de búsqueda")

        # Construir cláusulas WHERE dinámicamente (igual que en buscar_modulos)
        where_clauses = []
        params = []

        if solo_activos:
            where_clauses.append("es_activo = 1")

        if buscar:
            where_clauses.append("(nombre LIKE ? OR codigo_modulo LIKE ? OR descripcion LIKE ?)")
            search_pattern = f"%{buscar}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        if es_modulo_core is not None:
            where_clauses.append("es_modulo_core = ?")
            params.append(1 if es_modulo_core else 0)

        if requiere_licencia is not None:
            where_clauses.append("requiere_licencia = ?")
            params.append(1 if requiere_licencia else 0)

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
        SELECT COUNT(*) as total
        FROM cliente_modulo
        {where_clause}
        """
        
        resultado = execute_query(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        return resultado[0]['total'] if resultado else 0

    @staticmethod
    @BaseService.handle_service_errors
    async def eliminar_modulo(modulo_id: int) -> bool:
        """
        Elimina (desactiva) un módulo del catálogo del sistema.
        Implementa eliminación lógica (soft delete) para mantener integridad referencial.
        
        Validaciones:
        - No se puede eliminar un módulo core
        - No se puede eliminar un módulo que esté activo para algún cliente
        """
        logger.info(f"Intentando eliminar módulo ID: {modulo_id}")

        # Verificar que el módulo existe
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar que no sea un módulo core
        if modulo.es_modulo_core:
            raise ValidationError(
                detail="No se puede eliminar un módulo core del sistema.",
                internal_code="CANNOT_DELETE_CORE_MODULE"
            )

        # Verificar que no esté activo para ningún cliente
        query_check = """
        SELECT COUNT(*) as total
        FROM cliente_modulo_activo
        WHERE modulo_id = ? AND esta_activo = 1
        """
        resultado_check = execute_query(query_check, (modulo_id,), connection_type=DatabaseConnection.ADMIN)
        clientes_activos = resultado_check[0]['total'] if resultado_check else 0

        if clientes_activos > 0:
            raise ValidationError(
                detail=f"No se puede eliminar el módulo. Está activo para {clientes_activos} cliente(s).",
                internal_code="MODULE_IN_USE"
            )

        # Realizar eliminación lógica (desactivar)
        query = """
        UPDATE cliente_modulo
        SET es_activo = 0
        WHERE modulo_id = ?
        """
        
        execute_update(query, (modulo_id,), connection_type=DatabaseConnection.ADMIN)
        logger.info(f"Módulo ID {modulo_id} desactivado exitosamente.")
        return True