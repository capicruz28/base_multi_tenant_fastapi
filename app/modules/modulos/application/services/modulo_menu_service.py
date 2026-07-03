# app/modules/modulos/application/services/modulo_menu_service.py
"""
Servicio para la gestión de menús de módulos.

Este servicio implementa la lógica de negocio para operaciones sobre la entidad `modulo_menu`,
incluyendo CRUD completo, gestión de jerarquías, y obtención del menú del usuario usando SP.

Características clave:
- CRUD completo de menús por módulo
- Gestión de jerarquías (menús padre-hijo)
- Validación de niveles máximos (3 niveles)
- Duplicación de menús para personalización
- Obtención del menú del usuario usando sp_obtener_menu_usuario
"""
from typing import List, Optional, Dict, Any
import logging
import time
from sqlalchemy import select, update, delete, and_, or_, func as sql_func, Integer, case, text
from uuid import UUID

from app.core.config import settings
from app.infrastructure.database.tables_modulos import ModuloMenuTable, ModuloTable, ModuloSeccionTable, ClienteModuloTable
from app.infrastructure.database.tables import RolMenuPermisoTable, UsuarioRolTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update, execute_procedure_params
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.core.application.base_service import BaseService
from app.modules.modulos.presentation.schemas import (
    ModuloMenuCreate, ModuloMenuUpdate, ModuloMenuRead, MenuUsuarioResponse
)
from app.modules.modulos.application.helpers.menu_transformer import transformar_sp_menu_usuario
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)


def _normalize_uuid(v: Any) -> Optional[UUID]:
    """Normaliza valor a UUID para claves de diccionario."""
    if v is None:
        return None
    if isinstance(v, UUID):
        return v
    try:
        return UUID(str(v))
    except (ValueError, TypeError):
        return None


def _menu_usuario_auth_verbose() -> bool:
    return settings.ENABLE_AUTH_VERBOSE


def _menu_usuario_log_diagnostic(message: str, *args) -> None:
    if _menu_usuario_auth_verbose():
        logger.info(message, *args)


def _menu_usuario_log_diagnostic_warning(message: str, *args) -> None:
    if _menu_usuario_auth_verbose():
        logger.warning(message, *args)


def _menu_usuario_log_item(message: str, *args) -> None:
    logger.debug(message, *args)


def _menu_usuario_log_start(usuario_id: UUID, cliente_id: UUID) -> float:
    logger.info(
        "[MENU_USUARIO] Inicio usuario=%s cliente=%s",
        usuario_id,
        cliente_id,
    )
    return time.monotonic()


def _menu_usuario_log_finish(
    started: float,
    *,
    modulos: int,
    modo: str = "",
) -> None:
    elapsed_ms = round((time.monotonic() - started) * 1000, 1)
    if modo:
        logger.info(
            "[MENU_USUARIO] Fin modulos=%s duracion_ms=%s modo=%s",
            modulos,
            elapsed_ms,
            modo,
        )
    else:
        logger.info(
            "[MENU_USUARIO] Fin modulos=%s duracion_ms=%s",
            modulos,
            elapsed_ms,
        )


class ModuloMenuService(BaseService):
    """
    Servicio central para la administración de menús de módulos.
    GET /auth/menu es la única fuente de verdad para la navegación y permisos UI del frontend.
    Mapper: rol_menu_permiso → permisos (UI actions); permiso (RBAC) → required_permission (metadata).
    """

    @staticmethod
    async def _get_required_permissions_by_modulo(
        modulo_ids: List[UUID],
        cliente_id: UUID,
    ) -> Dict[UUID, List[str]]:
        """
        Obtiene códigos de permiso RBAC (tabla permiso) por modulo_id.
        Usado para required_permissions en cada ítem de menú. Si un módulo no tiene
        permisos asociados, devuelve lista vacía.
        """
        if not modulo_ids:
            return {}
        out: Dict[UUID, List[str]] = {mid: [] for mid in modulo_ids}
        try:
            from app.core.authorization.permission_catalog_store import (
                resolve_permission_catalog_target,
            )

            catalog_conn, catalog_client_id = await resolve_permission_catalog_target(
                cliente_id
            )
            placeholders = ",".join([f":m{i}" for i in range(len(modulo_ids))])
            sql = text(
                f"""
                SELECT modulo_id, codigo
                FROM permiso
                WHERE es_activo = 1 AND modulo_id IN ({placeholders})
                """
            )
            params = {f"m{i}": str(mid) for i, mid in enumerate(modulo_ids)}
            rows = await execute_query(
                sql.bindparams(**params),
                connection_type=catalog_conn,
                client_id=catalog_client_id,
            )
            for row in (rows or []):
                mid = _normalize_uuid(row.get("modulo_id"))
                codigo = row.get("codigo")
                if mid is not None and codigo:
                    out.setdefault(mid, []).append(codigo)
        except Exception as e:
            logger.debug("required_permissions by modulo (no bloqueante): %s", e)
        return out

    @staticmethod
    def _normalizar_menu_dict(menu_dict: dict) -> dict:
        """
        Normaliza los datos de un menú antes de crear el schema.
        Convierte NULL a valores por defecto donde sea necesario.
        """
        menu_dict = dict(menu_dict)  # Crear copia para no modificar el original
        
        # Normalizar orden: si es NULL, usar 0
        if menu_dict.get('orden') is None:
            menu_dict['orden'] = 0
        
        # Asegurar que los campos opcionales sean None si vienen como None
        campos_opcionales = ['descripcion', 'icono', 'ruta', 'menu_padre_id', 
                            'configuracion_json', 'fecha_actualizacion', 
                            'seccion_id', 'cliente_id', 'codigo']
        for key in campos_opcionales:
            if key in menu_dict and menu_dict[key] is None:
                menu_dict[key] = None
        
        return menu_dict

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_menu(menu_data: ModuloMenuCreate) -> ModuloMenuRead:
        """
        Crea un nuevo menú en un módulo.
        """
        logger.debug(f"Creando nuevo menú: {menu_data.nombre} para módulo {menu_data.modulo_id}")

        # Validar que el módulo existe
        from app.modules.modulos.application.services.modulo_service import ModuloService
        modulo = await ModuloService.obtener_modulo_por_id(menu_data.modulo_id)
        if not modulo:
            raise NotFoundError(
                detail=f"Módulo con ID {menu_data.modulo_id} no encontrado.",
                internal_code="MODULE_NOT_FOUND"
            )

        # Validar sección si se proporciona
        if menu_data.seccion_id:
            from app.modules.modulos.application.services.modulo_seccion_service import ModuloSeccionService
            seccion = await ModuloSeccionService.obtener_seccion_por_id(menu_data.seccion_id)
            if not seccion:
                raise NotFoundError(
                    detail=f"Sección con ID {menu_data.seccion_id} no encontrada.",
                    internal_code="SECTION_NOT_FOUND"
                )
            if seccion.modulo_id != menu_data.modulo_id:
                raise ValidationError(
                    detail=f"La sección {menu_data.seccion_id} no pertenece al módulo {menu_data.modulo_id}.",
                    internal_code="SECTION_WRONG_MODULE"
                )

        # Validar menú padre si se proporciona
        nivel = 1
        if menu_data.menu_padre_id:
            menu_padre = await ModuloMenuService.obtener_menu_por_id(menu_data.menu_padre_id)
            if not menu_padre:
                raise NotFoundError(
                    detail=f"Menú padre con ID {menu_data.menu_padre_id} no encontrado.",
                    internal_code="MENU_PARENT_NOT_FOUND"
                )
            if menu_padre.modulo_id != menu_data.modulo_id:
                raise ValidationError(
                    detail=f"El menú padre {menu_data.menu_padre_id} no pertenece al módulo {menu_data.modulo_id}.",
                    internal_code="MENU_PARENT_WRONG_MODULE"
                )
            nivel = menu_padre.nivel + 1
            if nivel > 3:
                raise ValidationError(
                    detail="No se permiten más de 3 niveles de anidación.",
                    internal_code="MENU_MAX_LEVEL_EXCEEDED"
                )

        # Validar ruta única dentro del módulo si se proporciona
        if menu_data.ruta:
            await ModuloMenuService._validar_ruta_unica_modulo(
                menu_data.modulo_id,
                menu_data.ruta,
                cliente_id=menu_data.cliente_id
            )

        # Preparar datos para inserción
        insert_data = {
            'modulo_id': menu_data.modulo_id,
            'seccion_id': menu_data.seccion_id,
            'cliente_id': menu_data.cliente_id,
            'codigo': menu_data.codigo.upper() if menu_data.codigo else None,
            'nombre': menu_data.nombre,
            'descripcion': menu_data.descripcion,
            'icono': menu_data.icono,
            'ruta': menu_data.ruta,
            'menu_padre_id': menu_data.menu_padre_id,
            'nivel': nivel,
            'tipo_menu': menu_data.tipo_menu,
            'orden': menu_data.orden,
            'requiere_autenticacion': menu_data.requiere_autenticacion,
            'es_visible': menu_data.es_visible,
            'es_menu_sistema': menu_data.es_menu_sistema,
            'es_activo': menu_data.es_activo,
            'configuracion_json': menu_data.configuracion_json,
        }

        from sqlalchemy import insert
        stmt = insert(ModuloMenuTable).values(**insert_data).returning(ModuloMenuTable)
        
        resultado = await execute_insert(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear el menú en la base de datos.",
                internal_code="MENU_CREATION_FAILED"
            )

        logger.debug(f"Menú creado exitosamente con ID: {resultado['menu_id']}")
        menu_dict = ModuloMenuService._normalizar_menu_dict(resultado)
        return ModuloMenuRead(**menu_dict)

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_ruta_unica_modulo(
        modulo_id: UUID, 
        ruta: str, 
        cliente_id: Optional[UUID] = None,
        excluir_menu_id: Optional[UUID] = None
    ) -> None:
        """
        Valida que la ruta sea única dentro del módulo (y cliente si es menú personalizado).
        
        Nota: Usa query RAW SQL para evitar problemas con apply_tenant_filter y SQLAlchemy.
        """
        from sqlalchemy import text
        
        # Construir query RAW SQL
        if cliente_id:
            # Menú personalizado: validar por módulo, ruta y cliente
            if excluir_menu_id:
                query_raw = text("""
                    SELECT menu_id 
                    FROM modulo_menu 
                    WHERE modulo_id = :modulo_id 
                      AND ruta = :ruta 
                      AND cliente_id = :cliente_id
                      AND menu_id != :excluir_menu_id
                """).bindparams(
                    modulo_id=str(modulo_id),
                    ruta=ruta,
                    cliente_id=str(cliente_id),
                    excluir_menu_id=str(excluir_menu_id)
                )
            else:
                query_raw = text("""
                    SELECT menu_id 
                    FROM modulo_menu 
                    WHERE modulo_id = :modulo_id 
                      AND ruta = :ruta 
                      AND cliente_id = :cliente_id
                """).bindparams(
                    modulo_id=str(modulo_id),
                    ruta=ruta,
                    cliente_id=str(cliente_id)
                )
        else:
            # Menú global: validar por módulo y ruta, cliente_id debe ser NULL
            if excluir_menu_id:
                query_raw = text("""
                    SELECT menu_id 
                    FROM modulo_menu 
                    WHERE modulo_id = :modulo_id 
                      AND ruta = :ruta 
                      AND cliente_id IS NULL
                      AND menu_id != :excluir_menu_id
                """).bindparams(
                    modulo_id=str(modulo_id),
                    ruta=ruta,
                    excluir_menu_id=str(excluir_menu_id)
                )
            else:
                query_raw = text("""
                    SELECT menu_id 
                    FROM modulo_menu 
                    WHERE modulo_id = :modulo_id 
                      AND ruta = :ruta 
                      AND cliente_id IS NULL
                """).bindparams(
                    modulo_id=str(modulo_id),
                    ruta=ruta
                )
        
        resultado = await execute_query(
            query_raw,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        
        if resultado:
            raise ConflictError(
                detail=f"Ya existe un menú con la ruta '{ruta}' en este módulo.",
                internal_code="MENU_ROUTE_CONFLICT"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_menus_modulo(
        modulo_id: UUID,
        seccion_id: Optional[UUID] = None,
        solo_activos: bool = True,
        estructura_jerarquica: bool = False
    ) -> List[ModuloMenuRead]:
        """
        Obtiene todos los menús de un módulo.
        
        Nota: Incluye menús globales (cliente_id IS NULL) y menús personalizados por cliente.
        """
        logger.debug(f"Obteniendo menús para módulo {modulo_id}, seccion_id={seccion_id}, solo_activos={solo_activos}")
        
        # Intentar con query raw SQL primero para verificar que la conexión funciona
        from sqlalchemy import text
        query_raw = text("""
            SELECT menu_id, modulo_id, nombre, es_activo 
            FROM modulo_menu 
            WHERE modulo_id = :modulo_id
        """)
        resultados_raw = await execute_query(
            query_raw.bindparams(modulo_id=str(modulo_id)),
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        logger.debug(f"Query RAW SQL retornó {len(resultados_raw)} resultados")
        if resultados_raw:
            logger.debug(f"Primeros resultados RAW: {[r.get('nombre') for r in resultados_raw[:3]]}")
        
        # Usar el mismo patrón que funciona en ModuloSeccionService
        query = select(ModuloMenuTable).where(ModuloMenuTable.c.modulo_id == modulo_id)
        
        if seccion_id:
            query = query.where(ModuloMenuTable.c.seccion_id == seccion_id)
        
        if solo_activos:
            query = query.where(ModuloMenuTable.c.es_activo == True)
        
        query = query.order_by(ModuloMenuTable.c.orden, ModuloMenuTable.c.nombre)
        
        resultados = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        
        logger.debug(f"Query SQLAlchemy retornó {len(resultados)} resultados para módulo {modulo_id}")
        
        if not resultados:
            logger.warning(f"No se encontraron menús para módulo {modulo_id} con filtros: seccion_id={seccion_id}, solo_activos={solo_activos}")
            # Si la query RAW funciona pero SQLAlchemy no, el problema es con SQLAlchemy
            if resultados_raw:
                logger.error(f"INCONSISTENCIA: Query RAW retornó {len(resultados_raw)} resultados pero SQLAlchemy retornó 0")
                # Usar resultados RAW como fallback - obtener todos los datos con query RAW completa
                query_raw_completa = text("""
                    SELECT 
                        menu_id, modulo_id, seccion_id, cliente_id,
                        codigo, nombre, descripcion, icono, ruta,
                        menu_padre_id, nivel, tipo_menu, orden,
                        requiere_autenticacion, es_visible, es_menu_sistema, es_activo,
                        fecha_creacion, fecha_actualizacion, configuracion_json
                    FROM modulo_menu 
                    WHERE modulo_id = :modulo_id
                """)
                
                if seccion_id:
                    query_raw_completa = text("""
                        SELECT 
                            menu_id, modulo_id, seccion_id, cliente_id,
                            codigo, nombre, descripcion, icono, ruta,
                            menu_padre_id, nivel, tipo_menu, orden,
                            requiere_autenticacion, es_visible, es_menu_sistema, es_activo,
                            fecha_creacion, fecha_actualizacion, configuracion_json
                        FROM modulo_menu 
                        WHERE modulo_id = :modulo_id AND seccion_id = :seccion_id
                    """).bindparams(modulo_id=str(modulo_id), seccion_id=str(seccion_id))
                else:
                    query_raw_completa = query_raw_completa.bindparams(modulo_id=str(modulo_id))
                
                if solo_activos:
                    # Agregar filtro de activos a la query RAW
                    if seccion_id:
                        query_raw_completa = text("""
                            SELECT 
                                menu_id, modulo_id, seccion_id, cliente_id,
                                codigo, nombre, descripcion, icono, ruta,
                                menu_padre_id, nivel, tipo_menu, orden,
                                requiere_autenticacion, es_visible, es_menu_sistema, es_activo,
                                fecha_creacion, fecha_actualizacion, configuracion_json
                            FROM modulo_menu 
                            WHERE modulo_id = :modulo_id AND seccion_id = :seccion_id AND es_activo = 1
                            ORDER BY orden, nombre
                        """).bindparams(modulo_id=str(modulo_id), seccion_id=str(seccion_id))
                    else:
                        query_raw_completa = text("""
                            SELECT 
                                menu_id, modulo_id, seccion_id, cliente_id,
                                codigo, nombre, descripcion, icono, ruta,
                                menu_padre_id, nivel, tipo_menu, orden,
                                requiere_autenticacion, es_visible, es_menu_sistema, es_activo,
                                fecha_creacion, fecha_actualizacion, configuracion_json
                            FROM modulo_menu 
                            WHERE modulo_id = :modulo_id AND es_activo = 1
                            ORDER BY orden, nombre
                        """).bindparams(modulo_id=str(modulo_id))
                else:
                    if not seccion_id:
                        query_raw_completa = text("""
                            SELECT 
                                menu_id, modulo_id, seccion_id, cliente_id,
                                codigo, nombre, descripcion, icono, ruta,
                                menu_padre_id, nivel, tipo_menu, orden,
                                requiere_autenticacion, es_visible, es_menu_sistema, es_activo,
                                fecha_creacion, fecha_actualizacion, configuracion_json
                            FROM modulo_menu 
                            WHERE modulo_id = :modulo_id
                            ORDER BY orden, nombre
                        """).bindparams(modulo_id=str(modulo_id))
                
                resultados_raw_completa = await execute_query(
                    query_raw_completa,
                    connection_type=DatabaseConnection.ADMIN,
                    client_id=None
                )
                
                # Convertir resultados RAW a ModuloMenuRead
                menus_raw = []
                for row in resultados_raw_completa:
                    try:
                        menu_dict = ModuloMenuService._normalizar_menu_dict(row)
                        menu = ModuloMenuRead(**menu_dict)
                        menus_raw.append(menu)
                    except Exception as e:
                        logger.error(f"Error al convertir menú RAW a schema: {e}, datos: {row}")
                        continue
                
                logger.debug(f"Usando {len(menus_raw)} menús de fallback RAW")
                return menus_raw
            return []
        
        menus = []
        for menu_row in resultados:
            try:
                menu_dict = ModuloMenuService._normalizar_menu_dict(menu_row)
                menu = ModuloMenuRead(**menu_dict)
                menus.append(menu)
            except Exception as e:
                logger.error(f"Error al convertir menú a schema: {e}, datos: {menu_row}")
                logger.exception(e)
                continue
        
        logger.debug(f"Convertidos {len(menus)} menús a schema ModuloMenuRead")
        
        if estructura_jerarquica:
            # Construir jerarquía
            menus_dict = {m.menu_id: m for m in menus}
            root_menus = []
            
            for menu in menus:
                if not menu.menu_padre_id:
                    root_menus.append(menu)
                else:
                    # Este código asume que ModuloMenuRead tiene un campo 'submenus'
                    # que se puede agregar dinámicamente
                    pass
            
            return root_menus
        
        return menus

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_menu_por_id(menu_id: UUID) -> Optional[ModuloMenuRead]:
        """
        Obtiene un menú específico por su ID.
        
        Nota: Usa query RAW SQL como fallback debido a problemas con SQLAlchemy y la tabla modulo_menu.
        """
        # Intentar primero con SQLAlchemy
        query = select(ModuloMenuTable).where(ModuloMenuTable.c.menu_id == menu_id)
        
        resultado = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        
        # Si SQLAlchemy no funciona, usar query RAW como fallback
        if not resultado:
            logger.debug(f"SQLAlchemy no retornó resultados para menu_id {menu_id}, intentando con query RAW")
            from sqlalchemy import text
            
            query_raw = text("""
                SELECT 
                    menu_id, modulo_id, seccion_id, cliente_id,
                    codigo, nombre, descripcion, icono, ruta,
                    menu_padre_id, nivel, tipo_menu, orden,
                    requiere_autenticacion, es_visible, es_menu_sistema, es_activo,
                    fecha_creacion, fecha_actualizacion, configuracion_json
                FROM modulo_menu 
                WHERE menu_id = :menu_id
            """).bindparams(menu_id=str(menu_id))
            
            resultado = await execute_query(
                query_raw,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )
            
            if not resultado:
                logger.warning(f"Menú con ID {menu_id} no encontrado (ni con SQLAlchemy ni con RAW)")
                return None
            
            logger.debug(f"Menú encontrado usando query RAW: {menu_id}")
        
        if not resultado:
            return None
        
        try:
            menu_dict = ModuloMenuService._normalizar_menu_dict(resultado[0])
            return ModuloMenuRead(**menu_dict)
        except Exception as e:
            logger.error(f"Error al convertir menú a schema: {e}, datos: {resultado[0]}")
            raise

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_submenus(menu_padre_id: UUID) -> List[ModuloMenuRead]:
        """
        Obtiene todos los submenús de un menú padre.
        """
        query = select(ModuloMenuTable).where(
            and_(
                ModuloMenuTable.c.menu_padre_id == menu_padre_id,
                ModuloMenuTable.c.es_activo == True
            )
        ).order_by(ModuloMenuTable.c.orden)
        
        resultados = await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        return [ModuloMenuRead(**ModuloMenuService._normalizar_menu_dict(menu)) for menu in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_menu(menu_id: UUID, menu_data: ModuloMenuUpdate) -> ModuloMenuRead:
        """
        Actualiza un menú existente.
        """
        logger.debug(f"Actualizando menú ID: {menu_id}")

        # Verificar que el menú existe
        menu_existente = await ModuloMenuService.obtener_menu_por_id(menu_id)
        if not menu_existente:
            raise NotFoundError(
                detail=f"Menú con ID {menu_id} no encontrado.",
                internal_code="MENU_NOT_FOUND"
            )

        update_dict = menu_data.model_dump(exclude_unset=True)
        
        # Validar menú padre si se está actualizando
        if 'menu_padre_id' in update_dict:
            if update_dict['menu_padre_id'] == menu_id:
                raise ValidationError(
                    detail="Un menú no puede ser su propio padre.",
                    internal_code="MENU_SELF_REFERENCE"
                )
            
            if update_dict['menu_padre_id']:
                menu_padre = await ModuloMenuService.obtener_menu_por_id(update_dict['menu_padre_id'])
                if not menu_padre:
                    raise NotFoundError(
                        detail=f"Menú padre con ID {update_dict['menu_padre_id']} no encontrado.",
                        internal_code="MENU_PARENT_NOT_FOUND"
                    )
                if menu_padre.modulo_id != menu_existente.modulo_id:
                    raise ValidationError(
                        detail=f"El menú padre {update_dict['menu_padre_id']} no pertenece al mismo módulo.",
                        internal_code="MENU_PARENT_WRONG_MODULE"
                    )
                # Calcular nuevo nivel
                nuevo_nivel = menu_padre.nivel + 1
                if nuevo_nivel > 3:
                    raise ValidationError(
                        detail="No se permiten más de 3 niveles de anidación.",
                        internal_code="MENU_MAX_LEVEL_EXCEEDED"
                    )
                update_dict['nivel'] = nuevo_nivel

        # Validar ruta única si se está actualizando
        if 'ruta' in update_dict:
            await ModuloMenuService._validar_ruta_unica_modulo(
                menu_existente.modulo_id,
                update_dict['ruta'],
                menu_existente.cliente_id,
                menu_id
            )

        if not update_dict:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )

        update_dict['fecha_actualizacion'] = sql_func.getdate()

        stmt = (
            update(ModuloMenuTable)
            .where(ModuloMenuTable.c.menu_id == menu_id)
            .values(**update_dict)
        )

        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado or resultado.get('rows_affected', 0) == 0:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar el menú.",
                internal_code="MENU_UPDATE_FAILED"
            )

        # Obtener el menú actualizado completo desde la BD para asegurar que todos los campos estén correctos
        menu_actualizado = await ModuloMenuService.obtener_menu_por_id(menu_id)
        if not menu_actualizado:
            raise ServiceError(
                status_code=500,
                detail="El menú fue actualizado pero no se pudo recuperar.",
                internal_code="MENU_RETRIEVE_AFTER_UPDATE_FAILED"
            )

        logger.debug(f"Menú ID {menu_id} actualizado exitosamente.")
        return menu_actualizado

    @staticmethod
    @BaseService.handle_service_errors
    async def eliminar_menu(menu_id: UUID) -> bool:
        """
        Elimina un menú (validando que no tenga submenús o permisos).
        """
        logger.debug(f"Intentando eliminar menú ID: {menu_id}")

        # Verificar que el menú existe
        menu = await ModuloMenuService.obtener_menu_por_id(menu_id)
        if not menu:
            raise NotFoundError(
                detail=f"Menú con ID {menu_id} no encontrado.",
                internal_code="MENU_NOT_FOUND"
            )

        # Validar que no tenga submenús
        submenus = await ModuloMenuService.obtener_submenus(menu_id)
        if submenus:
            raise ValidationError(
                detail=f"No se puede eliminar el menú. Tiene {len(submenus)} submenú(s) asociado(s).",
                internal_code="MENU_HAS_SUBMENUS"
            )

        # Validar que no tenga permisos asignados
        from app.infrastructure.database.tables import RolMenuPermisoTable
        query_check = select(sql_func.count()).select_from(RolMenuPermisoTable).where(
            RolMenuPermisoTable.c.menu_id == menu_id
        )
        
        resultado_check = await execute_query(
            query_check,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        permisos_asociados = resultado_check[0]['count_1'] if resultado_check else 0

        if permisos_asociados > 0:
            raise ValidationError(
                detail=f"No se puede eliminar el menú. Tiene {permisos_asociados} permiso(s) asignado(s).",
                internal_code="MENU_HAS_PERMISSIONS"
            )

        # Eliminar físicamente
        stmt = delete(ModuloMenuTable).where(ModuloMenuTable.c.menu_id == menu_id)
        
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        logger.debug(f"Menú ID {menu_id} eliminado exitosamente.")
        return True

    @staticmethod
    @BaseService.handle_service_errors
    async def activar_menu(menu_id: UUID) -> ModuloMenuRead:
        """Activa un menú."""
        menu = await ModuloMenuService.obtener_menu_por_id(menu_id)
        if not menu:
            raise NotFoundError(
                detail=f"Menú con ID {menu_id} no encontrado.",
                internal_code="MENU_NOT_FOUND"
            )
        
        stmt = (
            update(ModuloMenuTable)
            .where(ModuloMenuTable.c.menu_id == menu_id)
            .values(es_activo=True, fecha_actualizacion=sql_func.getdate())
            .returning(ModuloMenuTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo activar el menú.",
                internal_code="MENU_ACTIVATION_FAILED"
            )
        menu_dict = ModuloMenuService._normalizar_menu_dict(resultado)
        return ModuloMenuRead(**menu_dict)

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_menu(menu_id: UUID) -> ModuloMenuRead:
        """Desactiva un menú."""
        menu = await ModuloMenuService.obtener_menu_por_id(menu_id)
        if not menu:
            raise NotFoundError(
                detail=f"Menú con ID {menu_id} no encontrado.",
                internal_code="MENU_NOT_FOUND"
            )
        
        stmt = (
            update(ModuloMenuTable)
            .where(ModuloMenuTable.c.menu_id == menu_id)
            .values(es_activo=False, fecha_actualizacion=sql_func.getdate())
            .returning(ModuloMenuTable)
        )
        
        resultado = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo desactivar el menú.",
                internal_code="MENU_DEACTIVATION_FAILED"
            )
        menu_dict = ModuloMenuService._normalizar_menu_dict(resultado)
        return ModuloMenuRead(**menu_dict)

    @staticmethod
    @BaseService.handle_service_errors
    async def reordenar_menus(seccion_id: UUID, ordenes: Dict[UUID, int]) -> List[ModuloMenuRead]:
        """
        Reordena los menús dentro de una sección.
        """
        logger.debug(f"Reordenando menús de la sección {seccion_id}")

        # Validar que todas las secciones pertenecen a la sección
        query_menus = select(ModuloMenuTable).where(ModuloMenuTable.c.seccion_id == seccion_id)
        menus_result = await execute_query(
            query_menus,
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        menus_ids = {UUID(m['menu_id']) for m in menus_result}
        
        for menu_id in ordenes.keys():
            if menu_id not in menus_ids:
                raise ValidationError(
                    detail=f"Menú {menu_id} no pertenece a la sección {seccion_id}.",
                    internal_code="MENU_WRONG_SECTION"
                )

        # Actualizar órdenes
        for menu_id, nuevo_orden in ordenes.items():
            stmt = (
                update(ModuloMenuTable)
                .where(ModuloMenuTable.c.menu_id == menu_id)
                .values(orden=nuevo_orden, fecha_actualizacion=sql_func.getdate())
            )
            await execute_update(
                stmt,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )

        # Retornar menús actualizados
        return await ModuloMenuService.obtener_menus_modulo(
            modulo_id=None,  # Necesitamos obtener el módulo de la sección
            seccion_id=seccion_id,
            solo_activas=False
        )

    @staticmethod
    @BaseService.handle_service_errors
    async def duplicar_menu(menu_id: UUID, cliente_id: UUID, nuevo_nombre: Optional[str] = None) -> ModuloMenuRead:
        """
        Duplica un menú para crear una versión personalizada para un cliente.
        """
        logger.debug(f"Duplicando menú {menu_id} para cliente {cliente_id}")

        # Obtener menú original
        menu_original = await ModuloMenuService.obtener_menu_por_id(menu_id)
        if not menu_original:
            raise NotFoundError(
                detail=f"Menú con ID {menu_id} no encontrado.",
                internal_code="MENU_NOT_FOUND"
            )

        # Crear datos del nuevo menú
        nuevo_menu_data = ModuloMenuCreate(
            modulo_id=menu_original.modulo_id,
            seccion_id=menu_original.seccion_id,
            cliente_id=cliente_id,
            codigo=None,  # Menús personalizados no tienen código
            nombre=nuevo_nombre or f"{menu_original.nombre} (Personalizado)",
            descripcion=menu_original.descripcion,
            icono=menu_original.icono,
            ruta=menu_original.ruta,  # Puede necesitar ajuste
            menu_padre_id=None,  # Se duplica como raíz
            nivel=1,
            tipo_menu=menu_original.tipo_menu,
            orden=menu_original.orden,
            requiere_autenticacion=menu_original.requiere_autenticacion,
            es_visible=menu_original.es_visible,
            es_menu_sistema=False,  # Es personalizado
            es_activo=menu_original.es_activo,
            configuracion_json=menu_original.configuracion_json,
        )

        return await ModuloMenuService.crear_menu(nuevo_menu_data)

    @staticmethod
    @BaseService.handle_service_errors
    async def resolve_admin_tenant_rol_id(cliente_id: UUID) -> Optional[UUID]:
        """Resuelve rol_id ADMIN_TENANT del tenant (menú impersonación)."""
        from sqlalchemy import text as sa_text

        query = sa_text("""
            SELECT rol_id FROM rol
            WHERE cliente_id = :cliente_id
              AND codigo_rol = N'ADMIN_TENANT'
              AND es_activo = 1
        """).bindparams(cliente_id=cliente_id)
        rows = await execute_query(
            query,
            connection_type=DatabaseConnection.DEFAULT,
            client_id=cliente_id,
        )
        if not rows:
            return None
        rid = rows[0].get("rol_id")
        if rid is None:
            return None
        return rid if isinstance(rid, UUID) else UUID(str(rid))

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_menu_impersonacion_tenant(
        usuario_id: UUID,
        cliente_id: UUID,
        *,
        empresa_id: Optional[UUID] = None,
        effective_permission_codes: Optional[List[str]] = None,
    ) -> MenuUsuarioResponse:
        """
        Menú impersonación: RMP del ADMIN_TENANT del tenant (operador SYSTEM sin usuario_rol).
        """
        admin_rol_id = await ModuloMenuService.resolve_admin_tenant_rol_id(cliente_id)
        if not admin_rol_id:
            _menu_usuario_log_diagnostic_warning(
                "[MENU_USUARIO] Impersonación: ADMIN_TENANT no encontrado cliente=%s",
                cliente_id,
            )
            return MenuUsuarioResponse(modulos=[])
        return await ModuloMenuService.obtener_menu_usuario(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            is_super_admin=False,
            as_tenant_admin=False,
            empresa_id=empresa_id,
            effective_permission_codes=effective_permission_codes,
            permisos_rol_id=admin_rol_id,
        )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_menu_usuario(
        usuario_id: UUID,
        cliente_id: UUID,
        is_super_admin: bool = False,
        as_tenant_admin: bool = False,
        *,
        empresa_id: Optional[UUID] = None,
        effective_permission_codes: Optional[List[str]] = None,
        permisos_rol_id: Optional[UUID] = None,
    ) -> MenuUsuarioResponse:
        """
        Obtiene el menú completo del usuario combinando datos de BD central y BD del cliente.
        
        ARQUITECTURA (Modelo Owner):
        - Módulos contratados: QUERY 1 (cliente_modulo)
        - Visibilidad UI: QUERY 2 (rol_menu_permiso) para todos los usuarios tenant
        - Elevación: solo is_super_admin (platform); tenant_admin usa rol_menu_permiso
        
        permisos_rol_id: cuando se setea (impersonación), QUERY 2 usa ese rol directamente
        sin join usuario_rol (operador SYSTEM no tiene usuario_rol en tenant).
        """
        from app.core.tenant.empresa_context import (
            resolve_empresa_id,
            sql_empresa_filter_usuario_rol,
        )

        resolved_empresa_id = resolve_empresa_id(empresa_id)
        use_elevated_menu = is_super_admin
        if as_tenant_admin and not is_super_admin:
            _menu_usuario_log_item(
                "[MENU_USUARIO] as_tenant_admin ignorado (Modelo Owner); usando rol_menu_permiso"
            )
        menu_started = _menu_usuario_log_start(usuario_id, cliente_id)
        _menu_usuario_log_diagnostic(
            "[MENU_USUARIO] Contexto is_super_admin=%s permisos_rol_id=%s empresa_id=%s",
            is_super_admin,
            permisos_rol_id,
            resolved_empresa_id,
        )

        try:
            # ============================================================
            # QUERY 1: Catálogo menú + módulos contratados (ADMIN Shared / DEFAULT Dedicated)
            # ============================================================
            from datetime import datetime
            from app.core.authorization.menu_catalog_store import (
                resolve_menu_catalog_query1_target,
            )
            
            # Menús de módulos activos del cliente (store según installation mode)
            query_menus_central = select(
                # Datos del módulo
                ModuloTable.c.modulo_id,
                ModuloTable.c.codigo.label('modulo_codigo'),
                ModuloTable.c.nombre.label('modulo_nombre'),
                ModuloTable.c.descripcion.label('modulo_descripcion'),
                ModuloTable.c.icono.label('modulo_icono'),
                ModuloTable.c.color.label('modulo_color'),
                ModuloTable.c.categoria.label('modulo_categoria'),
                ModuloTable.c.orden.label('modulo_orden'),
                
                # Datos de la sección
                ModuloSeccionTable.c.seccion_id,
                ModuloSeccionTable.c.codigo.label('seccion_codigo'),
                ModuloSeccionTable.c.nombre.label('seccion_nombre'),
                ModuloSeccionTable.c.descripcion.label('seccion_descripcion'),
                ModuloSeccionTable.c.icono.label('seccion_icono'),
                ModuloSeccionTable.c.orden.label('seccion_orden'),
                
                # Datos del menú
                ModuloMenuTable.c.menu_id,
                ModuloMenuTable.c.codigo.label('menu_codigo'),
                ModuloMenuTable.c.nombre.label('menu_nombre'),
                ModuloMenuTable.c.descripcion.label('menu_descripcion'),
                ModuloMenuTable.c.icono.label('menu_icono'),
                ModuloMenuTable.c.ruta.label('menu_ruta'),
                ModuloMenuTable.c.menu_padre_id,
                ModuloMenuTable.c.nivel.label('menu_nivel'),
                ModuloMenuTable.c.tipo_menu.label('menu_tipo'),
                ModuloMenuTable.c.orden.label('menu_orden'),
                ModuloMenuTable.c.requiere_autenticacion,
                ModuloMenuTable.c.configuracion_json.label('menu_configuracion'),
                
                # Información del cliente-módulo
                ClienteModuloTable.c.fecha_vencimiento,
                ClienteModuloTable.c.modo_prueba,
                ClienteModuloTable.c.limite_usuarios,
                ClienteModuloTable.c.limite_registros
            ).select_from(
                ModuloMenuTable
                .join(ModuloTable, ModuloMenuTable.c.modulo_id == ModuloTable.c.modulo_id)
                .outerjoin(ModuloSeccionTable, ModuloMenuTable.c.seccion_id == ModuloSeccionTable.c.seccion_id)
                .join(ClienteModuloTable, 
                      and_(
                          ModuloTable.c.modulo_id == ClienteModuloTable.c.modulo_id,
                          ClienteModuloTable.c.cliente_id == cliente_id,
                          ClienteModuloTable.c.esta_activo == True,
                          or_(
                              ClienteModuloTable.c.fecha_vencimiento.is_(None),
                              ClienteModuloTable.c.fecha_vencimiento > datetime.now()
                          )
                      )
                )
            ).where(
                and_(
                    ModuloMenuTable.c.es_activo == True,
                    ModuloMenuTable.c.es_visible == True,
                    ModuloTable.c.es_activo == True,
                    or_(
                        ModuloSeccionTable.c.es_activo == True,
                        ModuloSeccionTable.c.seccion_id.is_(None)
                    ),
                    or_(
                        ModuloMenuTable.c.cliente_id.is_(None),
                        ModuloMenuTable.c.cliente_id == cliente_id
                    )
                )
            ).order_by(
                ModuloTable.c.orden.asc(),
                sql_func.isnull(ModuloSeccionTable.c.orden, 999).asc(),
                ModuloMenuTable.c.nivel.asc(),
                ModuloMenuTable.c.orden.asc()
            )
            
            catalog_connection, catalog_client_id = await resolve_menu_catalog_query1_target(
                cliente_id
            )

            menus_central = await execute_query(
                query_menus_central,
                connection_type=catalog_connection,
                client_id=catalog_client_id,
            )
            
            if not menus_central:
                _menu_usuario_log_finish(menu_started, modulos=0, modo="sin_catalogo")
                return MenuUsuarioResponse(modulos=[])

            # Permisos RBAC por módulo (permiso → required_permissions). Una sola consulta central.
            modulo_ids_distinct = [
                mid for r in menus_central
                if (mid := _normalize_uuid(r.get("modulo_id"))) is not None
            ]
            modulo_ids_distinct = list(dict.fromkeys(modulo_ids_distinct))
            required_permissions_by_modulo = await ModuloMenuService._get_required_permissions_by_modulo(
                modulo_ids_distinct,
                cliente_id,
            )

            # ============================================================
            # SUPER_ADMIN platform: menús contratados con permisos UI completos
            # ============================================================
            if use_elevated_menu:
                elevated_rows = menus_central
                _menu_usuario_log_diagnostic(
                    "[MENU_USUARIO] Elevado super_admin: %s ítems (sin rol_menu_permiso)",
                    len(elevated_rows),
                )
                resultado_combinado = []
                for menu_row in elevated_rows:
                    resultado_combinado.append({
                        **menu_row,
                        'puede_ver': True,
                        'puede_crear': True,
                        'puede_editar': True,
                        'puede_eliminar': True,
                        'puede_exportar': True,
                        'puede_imprimir': True,
                        'puede_aprobar': True,
                        'permisos_extra': None,
                    })
                menu_response = transformar_sp_menu_usuario(
                    resultado_combinado,
                    required_permissions_by_modulo=required_permissions_by_modulo,
                )
                _menu_usuario_log_finish(
                    menu_started,
                    modulos=len(menu_response.modulos),
                    modo="elevated",
                )
                return menu_response
            
            # Obtener IDs de menús para filtrar permisos
            menu_ids = [row['menu_id'] for row in menus_central if row.get('menu_id')]
            
            if not menu_ids:
                _menu_usuario_log_finish(menu_started, modulos=0, modo="sin_menu_ids")
                return MenuUsuarioResponse(modulos=[])
            
            # ============================================================
            # QUERY 2: Obtener permisos desde BD del CLIENTE
            # ============================================================
            # ✅ USAR RAW SQL directamente para evitar problemas con SQLAlchemy
            # Esta query obtiene los permisos del usuario filtrando por:
            # - usuario_id y cliente_id en usuario_rol
            # - rol_id en rol_menu_permiso
            # - solo menús con puede_ver = 1
            # - solo roles activos y no expirados
            
            _menu_usuario_log_diagnostic(
                "[MENU_USUARIO] Ejecutando query de permisos usuario=%s cliente=%s menu_ids=%s",
                usuario_id,
                cliente_id,
                len(menu_ids),
            )
            
            if permisos_rol_id is not None:
                menu_ids_placeholders = ",".join(
                    [f":menu_id_{i}" for i in range(len(menu_ids))]
                )
                query_raw = text(f"""
                SELECT p.menu_id,
                       MAX(CAST(p.puede_ver AS INT)) AS puede_ver,
                       MAX(CAST(p.puede_crear AS INT)) AS puede_crear,
                       MAX(CAST(p.puede_editar AS INT)) AS puede_editar,
                       MAX(CAST(p.puede_eliminar AS INT)) AS puede_eliminar,
                       MAX(CAST(p.puede_exportar AS INT)) AS puede_exportar,
                       MAX(CAST(p.puede_imprimir AS INT)) AS puede_imprimir,
                       MAX(CAST(p.puede_aprobar AS INT)) AS puede_aprobar
                FROM rol_menu_permiso p
                WHERE p.rol_id = :rol_id
                  AND p.cliente_id = :cliente_id
                  AND p.menu_id IN ({menu_ids_placeholders})
                  AND p.puede_ver = 1
                GROUP BY p.menu_id
                """).bindparams(
                    rol_id=str(permisos_rol_id),
                    cliente_id=str(cliente_id),
                    **{f"menu_id_{i}": str(mid) for i, mid in enumerate(menu_ids)},
                )
                _menu_usuario_log_diagnostic(
                    "[MENU_USUARIO] Query impersonación/admin_rol rol_id=%s",
                    permisos_rol_id,
                )
                permisos_cliente = await execute_query(
                    query_raw,
                    connection_type=DatabaseConnection.DEFAULT,
                    client_id=cliente_id,
                )
            else:
                menu_ids_placeholders = ",".join(
                    [f":menu_id_{i}" for i in range(len(menu_ids))]
                )
                empresa_sql = (
                    sql_empresa_filter_usuario_rol("ur")
                    if resolved_empresa_id
                    else ""
                )
                query_raw = text(f"""
                SELECT p.menu_id,
                       MAX(CAST(p.puede_ver AS INT)) AS puede_ver,
                       MAX(CAST(p.puede_crear AS INT)) AS puede_crear,
                       MAX(CAST(p.puede_editar AS INT)) AS puede_editar,
                       MAX(CAST(p.puede_eliminar AS INT)) AS puede_eliminar,
                       MAX(CAST(p.puede_exportar AS INT)) AS puede_exportar,
                       MAX(CAST(p.puede_imprimir AS INT)) AS puede_imprimir,
                       MAX(CAST(p.puede_aprobar AS INT)) AS puede_aprobar
                FROM rol_menu_permiso p
                INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id
                WHERE ur.usuario_id = :usuario_id
                  AND ur.cliente_id = :cliente_id
                  AND ur.es_activo = 1
                  AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
                  {empresa_sql}
                  AND p.cliente_id = :p_cliente_id
                  AND p.menu_id IN ({menu_ids_placeholders})
                  AND p.puede_ver = 1
                GROUP BY p.menu_id
                """)
                bind_params = {
                    "usuario_id": str(usuario_id),
                    "cliente_id": str(cliente_id),
                    "p_cliente_id": str(cliente_id),
                    **{f"menu_id_{i}": str(mid) for i, mid in enumerate(menu_ids)},
                }
                if resolved_empresa_id:
                    bind_params["empresa_id"] = str(resolved_empresa_id)
                query_raw = query_raw.bindparams(**bind_params)
                
                _menu_usuario_log_diagnostic(
                    "[MENU_USUARIO] Query RAW SQL generada con %s menu_ids en IN clause",
                    len(menu_ids),
                )
                
                permisos_cliente = await execute_query(
                    query_raw,
                    connection_type=DatabaseConnection.DEFAULT,
                    client_id=cliente_id,
                )
                
                _menu_usuario_log_diagnostic(
                    "[MENU_USUARIO] Query RAW SQL retornó %s registros",
                    len(permisos_cliente),
                )
                if permisos_cliente:
                    _menu_usuario_log_diagnostic(
                        "[MENU_USUARIO] Menu IDs con permisos: %s",
                        [str(p['menu_id']) for p in permisos_cliente],
                    )
                else:
                    _menu_usuario_log_diagnostic_warning(
                        "[MENU_USUARIO] No se encontraron permisos para usuario %s en cliente %s",
                        usuario_id,
                        cliente_id,
                    )
            
            _menu_usuario_log_diagnostic(
                "[MENU_USUARIO] Query de permisos retornó %s registros",
                len(permisos_cliente),
            )
            if permisos_cliente:
                _menu_usuario_log_item(
                    "[MENU_USUARIO] Primeros permisos obtenidos: %s",
                    permisos_cliente[:3],
                )
            
            # Crear diccionario de permisos por menu_id (ya agregados por MAX en la query)
            # ✅ CRÍTICO: Normalizar menu_id a UUID para comparación correcta
            permisos_por_menu: Dict[UUID, Dict[str, Any]] = {}
            for perm in permisos_cliente:
                menu_id_raw = perm['menu_id']
                # Normalizar a UUID si es string
                if isinstance(menu_id_raw, str):
                    try:
                        menu_id = UUID(menu_id_raw)
                    except (ValueError, AttributeError):
                        _menu_usuario_log_item(
                            "[MENU_USUARIO] Menu ID inválido en permisos: %s",
                            menu_id_raw,
                        )
                        continue
                elif isinstance(menu_id_raw, UUID):
                    menu_id = menu_id_raw
                else:
                    _menu_usuario_log_item(
                        "[MENU_USUARIO] Menu ID tipo desconocido: %s valor=%s",
                        type(menu_id_raw),
                        menu_id_raw,
                    )
                    continue
                
                permisos_por_menu[menu_id] = {
                    'puede_ver': bool(perm.get('puede_ver', 0)),
                    'puede_crear': bool(perm.get('puede_crear', 0)),
                    'puede_editar': bool(perm.get('puede_editar', 0)),
                    'puede_eliminar': bool(perm.get('puede_eliminar', 0)),
                    'puede_exportar': bool(perm.get('puede_exportar', 0)),
                    'puede_imprimir': bool(perm.get('puede_imprimir', 0)),
                    'puede_aprobar': bool(perm.get('puede_aprobar', 0)),
                }
            
            _menu_usuario_log_item(
                "[MENU_USUARIO] Permisos normalizados: %s menús (sample keys=%s)",
                len(permisos_por_menu),
                list(permisos_por_menu.keys())[:3],
            )
            
            _menu_usuario_log_diagnostic(
                "[MENU_USUARIO] Permisos procesados: %s menús con permisos de %s menús disponibles",
                len(permisos_por_menu),
                len(menu_ids),
            )
            _menu_usuario_log_item(
                "[MENU_USUARIO] Menu IDs con permisos: %s",
                list(permisos_por_menu.keys()),
            )
            
            # ✅ DIAGNÓSTICO: Verificar si hay roles asignados al usuario (mismo scope empresa)
            role_diag_conditions = [
                UsuarioRolTable.c.usuario_id == usuario_id,
                UsuarioRolTable.c.cliente_id == cliente_id,
                UsuarioRolTable.c.es_activo == True,
            ]
            if resolved_empresa_id:
                role_diag_conditions.append(
                    or_(
                        UsuarioRolTable.c.empresa_id.is_(None),
                        UsuarioRolTable.c.empresa_id == resolved_empresa_id,
                    )
                )
            query_roles_usuario = select(
                UsuarioRolTable.c.rol_id,
                UsuarioRolTable.c.es_activo
            ).where(and_(*role_diag_conditions))
            roles_usuario = await execute_query(
                query_roles_usuario,
                connection_type=DatabaseConnection.DEFAULT,
                client_id=cliente_id
            )
            _menu_usuario_log_diagnostic(
                "[MENU_USUARIO] Usuario %s tiene %s roles activos: %s",
                usuario_id,
                len(roles_usuario),
                [r['rol_id'] for r in roles_usuario],
            )
            
            # ============================================================
            # COMBINAR RESULTADOS: Agregar permisos a cada menú
            # ============================================================
            resultado_combinado = []
            menus_sin_permisos = []
            menus_con_permisos = []
            
            for menu_row in menus_central:
                menu_id_raw = menu_row.get('menu_id')
                
                # ✅ CRÍTICO: Normalizar menu_id a UUID para comparación correcta
                if isinstance(menu_id_raw, str):
                    try:
                        menu_id = UUID(menu_id_raw)
                    except (ValueError, AttributeError):
                        _menu_usuario_log_item(
                            "[MENU_USUARIO] Menu ID inválido en menus_central: %s",
                            menu_id_raw,
                        )
                        menus_sin_permisos.append(menu_id_raw)
                        continue
                elif isinstance(menu_id_raw, UUID):
                    menu_id = menu_id_raw
                else:
                    _menu_usuario_log_item(
                        "[MENU_USUARIO] Menu ID tipo desconocido en menus_central: %s valor=%s",
                        type(menu_id_raw),
                        menu_id_raw,
                    )
                    menus_sin_permisos.append(menu_id_raw)
                    continue
                
                # ✅ CRÍTICO: Solo incluir menús donde el usuario tiene permiso de ver
                # Verificar EXPLÍCITAMENTE que el menu_id esté en permisos_por_menu
                # y que tenga puede_ver == True
                if menu_id in permisos_por_menu:
                    permisos = permisos_por_menu[menu_id]
                    _menu_usuario_log_item(
                        "[MENU_USUARIO] Menú %s en permisos_por_menu puede_ver=%s",
                        menu_id,
                        permisos.get('puede_ver'),
                    )
                    # Solo incluir si tiene permiso de ver
                    puede_ver_value = permisos.get('puede_ver', False)
                    if puede_ver_value:
                        resultado_combinado.append({
                            **menu_row,
                            'puede_ver': permisos.get('puede_ver', False),
                            'puede_crear': permisos.get('puede_crear', False),
                            'puede_editar': permisos.get('puede_editar', False),
                            'puede_eliminar': permisos.get('puede_eliminar', False),
                            'puede_exportar': permisos.get('puede_exportar', False),
                            'puede_imprimir': permisos.get('puede_imprimir', False),
                            'puede_aprobar': permisos.get('puede_aprobar', False),
                            'permisos_extra': None  # TODO: Implementar si es necesario
                        })
                        menus_con_permisos.append(menu_id)
                        _menu_usuario_log_item(
                            "[MENU_USUARIO] Menú %s INCLUIDO: puede_ver=True",
                            menu_id,
                        )
                    else:
                        menus_sin_permisos.append(menu_id)
                        _menu_usuario_log_item(
                            "[MENU_USUARIO] Menú %s excluido: puede_ver=%s",
                            menu_id,
                            puede_ver_value,
                        )
                else:
                    menus_sin_permisos.append(menu_id)
                    menu_ids_esperados = [
                        'a6942632-d39b-4660-8207-0aedfb42d17d',
                        '59753cb5-5480-4034-baed-117f8531be02',
                        '1bc07807-3cd2-42f4-8ef0-20dc48b2c329',
                        'edf3437b-83ef-427c-97e0-299415d50a38'
                    ]
                    menu_id_str = str(menu_id).lower()
                    if any(mid in menu_id_str for mid in menu_ids_esperados):
                        _menu_usuario_log_diagnostic_warning(
                            "[MENU_USUARIO] Menú %s NO encontrado en permisos_por_menu. Keys sample=%s",
                            menu_id,
                            [str(k) for k in list(permisos_por_menu.keys())[:10]],
                        )
            
            _menu_usuario_log_diagnostic(
                "[MENU_USUARIO] Resumen: %s incluidos, %s excluidos de %s disponibles",
                len(menus_con_permisos),
                len(menus_sin_permisos),
                len(menus_central),
            )
            
            if not resultado_combinado:
                _menu_usuario_log_finish(menu_started, modulos=0, modo="sin_permisos")
                return MenuUsuarioResponse(modulos=[])

            # Transformar resultado combinado a estructura jerárquica
            menu_response = transformar_sp_menu_usuario(
                resultado_combinado,
                required_permissions_by_modulo=required_permissions_by_modulo,
            )

            _menu_usuario_log_finish(
                menu_started,
                modulos=len(menu_response.modulos),
                modo="permisos",
            )
            return menu_response
            
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

