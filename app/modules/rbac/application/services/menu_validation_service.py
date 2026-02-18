"""
Servicio para validar que menu_id existe en BD central.
Útil para BD dedicadas donde menu_id referencia modulo_menu en central.

✅ FASE 3: Validación cross-database para prevenir datos huérfanos.
"""
from uuid import UUID
from typing import Optional, Dict, List
import logging

from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
from app.infrastructure.database.tables_modulos import ModuloMenuTable
from sqlalchemy import select
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class MenuValidationService:
    """Valida existencia de menús en BD central."""
    
    @staticmethod
    async def validate_menu_exists_in_central(
        menu_id: UUID,
        cliente_id: UUID,
        allow_global: bool = True
    ) -> bool:
        """
        Valida que menu_id existe en BD central.
        
        ✅ FASE 3: Consulta BD central (ADMIN connection) para validar menu_id.
        Esto es crítico para BD dedicadas donde menu_id referencia modulo_menu en central.
        
        Args:
            menu_id: ID del menú a validar
            cliente_id: ID del cliente (para validar ownership si no es global)
            allow_global: Si True, permite menús globales (cliente_id=NULL)
        
        Returns:
            True si existe y es válido
        
        Raises:
            NotFoundError: Si el menú no existe
            ValidationError: Si el menú no pertenece al cliente o está inactivo
        """
        # Query en BD central (ADMIN connection)
        query = select(
            ModuloMenuTable.c.menu_id,
            ModuloMenuTable.c.cliente_id,
            ModuloMenuTable.c.es_activo,
            ModuloMenuTable.c.nombre
        ).where(
            ModuloMenuTable.c.menu_id == menu_id
        )
        
        try:
            # ✅ FASE 3: Usar conexión ADMIN para consultar BD central
            async with get_db_connection(
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            ) as session:
                result = await session.execute(query)
                menu = result.fetchone()
                
                if not menu:
                    logger.warning(
                        f"[MENU_VALIDATION] Menú {menu_id} no existe en BD central"
                    )
                    raise NotFoundError(
                        detail=f"Menú con ID {menu_id} no existe en catálogo central",
                        internal_code="MENU_NOT_FOUND_CENTRAL"
                    )
                
                menu_cliente_id = menu['cliente_id']
                es_activo = menu['es_activo']
                menu_nombre = menu.get('nombre', 'N/A')
                
                # Validar que esté activo
                if not es_activo:
                    logger.warning(
                        f"[MENU_VALIDATION] Menú {menu_id} ({menu_nombre}) está inactivo"
                    )
                    raise ValidationError(
                        detail=f"Menú con ID {menu_id} está inactivo",
                        internal_code="MENU_INACTIVE"
                    )
                
                # Validar ownership
                if menu_cliente_id is None:
                    # Menú global
                    if not allow_global:
                        logger.warning(
                            f"[MENU_VALIDATION] Menú global {menu_id} no permitido para cliente {cliente_id}"
                        )
                        raise ValidationError(
                            detail=f"Menú global {menu_id} no permitido para este cliente",
                            internal_code="GLOBAL_MENU_NOT_ALLOWED"
                        )
                    logger.debug(
                        f"[MENU_VALIDATION] Menú global {menu_id} ({menu_nombre}) válido"
                    )
                    return True
                
                # Menú específico del cliente
                if menu_cliente_id != cliente_id:
                    logger.warning(
                        f"[MENU_VALIDATION] Menú {menu_id} pertenece a cliente {menu_cliente_id}, "
                        f"pero se intenta usar desde cliente {cliente_id}"
                    )
                    raise ValidationError(
                        detail=f"Menú con ID {menu_id} no pertenece al cliente {cliente_id}",
                        internal_code="MENU_CLIENT_MISMATCH"
                    )
                
                logger.debug(
                    f"[MENU_VALIDATION] Menú {menu_id} ({menu_nombre}) válido para cliente {cliente_id}"
                )
                return True
                
        except (NotFoundError, ValidationError):
            # Re-lanzar errores de validación
            raise
        except Exception as e:
            logger.error(
                f"[MENU_VALIDATION] Error validando menú {menu_id} en BD central: {e}",
                exc_info=True
            )
            raise ValidationError(
                detail=f"Error al validar menú en catálogo central: {str(e)}",
                internal_code="MENU_VALIDATION_ERROR"
            )
    
    @staticmethod
    async def validate_multiple_menus(
        menu_ids: List[UUID],
        cliente_id: UUID,
        allow_global: bool = True
    ) -> Dict[UUID, bool]:
        """
        Valida múltiples menús en batch.
        
        ✅ FASE 3: Validación eficiente en batch para múltiples menu_ids.
        
        Args:
            menu_ids: Lista de IDs de menús a validar
            cliente_id: ID del cliente
            allow_global: Si True, permite menús globales
        
        Returns:
            Dict con menu_id -> True si válido
        
        Raises:
            NotFoundError: Si algún menú no existe
            ValidationError: Si algún menú no pertenece al cliente o está inactivo
        """
        if not menu_ids:
            return {}
        
        # Query batch en BD central
        query = select(
            ModuloMenuTable.c.menu_id,
            ModuloMenuTable.c.cliente_id,
            ModuloMenuTable.c.es_activo,
            ModuloMenuTable.c.nombre
        ).where(
            ModuloMenuTable.c.menu_id.in_(menu_ids)
        )
        
        try:
            # ✅ FASE 3: Usar conexión ADMIN para consultar BD central
            async with get_db_connection(
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            ) as session:
                result = await session.execute(query)
                menus = result.fetchall()
                
                valid_menus = {}
                invalid_menus = []
                
                for menu in menus:
                    menu_id = menu['menu_id']
                    menu_cliente_id = menu['cliente_id']
                    es_activo = menu['es_activo']
                    menu_nombre = menu.get('nombre', 'N/A')
                    
                    if not es_activo:
                        invalid_menus.append(f"{menu_id} ({menu_nombre}) - inactivo")
                        continue
                    
                    if menu_cliente_id is None:
                        # Menú global
                        if allow_global:
                            valid_menus[menu_id] = True
                        else:
                            invalid_menus.append(f"{menu_id} ({menu_nombre}) - global no permitido")
                    elif menu_cliente_id == cliente_id:
                        # Menú del cliente
                        valid_menus[menu_id] = True
                    else:
                        # Menú de otro cliente
                        invalid_menus.append(
                            f"{menu_id} ({menu_nombre}) - pertenece a cliente {menu_cliente_id}"
                        )
                
                # Verificar que todos los menu_ids fueron encontrados
                found_menu_ids = set(valid_menus.keys()) | {m['menu_id'] for m in menus}
                missing = set(menu_ids) - found_menu_ids
                
                if missing:
                    logger.warning(
                        f"[MENU_VALIDATION] Menús no encontrados en BD central: {missing}"
                    )
                    raise NotFoundError(
                        detail=f"Menús no encontrados en catálogo central: {list(missing)}",
                        internal_code="MENUS_NOT_FOUND"
                    )
                
                if invalid_menus:
                    logger.warning(
                        f"[MENU_VALIDATION] Menús inválidos: {invalid_menus}"
                    )
                    raise ValidationError(
                        detail=f"Menús inválidos: {', '.join(invalid_menus)}",
                        internal_code="MENUS_INVALID"
                    )
                
                logger.debug(
                    f"[MENU_VALIDATION] Validados {len(valid_menus)} menús para cliente {cliente_id}"
                )
                
                return valid_menus
                
        except (NotFoundError, ValidationError):
            # Re-lanzar errores de validación
            raise
        except Exception as e:
            logger.error(
                f"[MENU_VALIDATION] Error validando menús en batch: {e}",
                exc_info=True
            )
            raise ValidationError(
                detail=f"Error al validar menús en catálogo central: {str(e)}",
                internal_code="MENU_VALIDATION_BATCH_ERROR"
            )
