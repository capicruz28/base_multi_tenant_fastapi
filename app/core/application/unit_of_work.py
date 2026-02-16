"""
Unit of Work Pattern para transacciones atómicas multi-operación.

✅ FASE 1: Implementación híbrida que convive con código existente.
- Código nuevo puede usar UnitOfWork
- Código viejo sigue usando execute_query() directamente
- Ambos funcionan simultáneamente

USO:
    async with UnitOfWork(client_id=current_client_id) as uow:
        await uow.execute(calcular_totales_query)
        await uow.execute(actualizar_estado_query)
        await uow.execute(crear_asientos_query)
        # Todo se commitea o rollback juntos
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Dict, Any, Union, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, Select, Update, Delete, Insert
from sqlalchemy.sql import ClauseElement, TextClause

from app.infrastructure.database.connection_async import (
    get_db_connection, DatabaseConnection
)
from app.core.tenant.context import get_current_client_id
from app.core.exceptions import DatabaseError
import logging

logger = logging.getLogger(__name__)


class UnitOfWork:
    """
    Unit of Work Pattern para transacciones atómicas.
    
    ✅ HÍBRIDO: Puede usarse junto con execute_query() existente.
    - Código nuevo: Usa UnitOfWork para operaciones multi-paso
    - Código viejo: Sigue usando execute_query() (sin cambios)
    
    Características:
    - Transacciones atómicas multi-operación
    - Rollback automático en caso de error
    - Commit automático al salir exitosamente
    - Compatible con código existente
    
    Ejemplo:
        async with UnitOfWork(client_id=current_client_id) as uow:
            # Paso 1: Calcular totales
            await uow.execute(calcular_totales_query, {"planilla_id": planilla_id})
            
            # Paso 2: Actualizar estado
            await uow.execute(actualizar_estado_query, {"planilla_id": planilla_id})
            
            # Paso 3: Generar asientos
            await uow.execute(crear_asientos_query, {"planilla_id": planilla_id})
            
            # Si cualquier paso falla, todo se revierte automáticamente
    """
    
    def __init__(
        self,
        client_id: Optional[UUID] = None,
        connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
    ):
        """
        Inicializa Unit of Work.
        
        Args:
            client_id: ID del cliente (opcional, usa contexto si no se proporciona)
            connection_type: Tipo de conexión (DEFAULT o ADMIN)
        """
        self.client_id = client_id or self._get_client_id()
        self.connection_type = connection_type
        self.session: Optional[AsyncSession] = None
        self._committed = False
        self._rolled_back = False
        self._operations_count = 0
    
    def _get_client_id(self) -> UUID:
        """Obtiene client_id del contexto o lanza error."""
        try:
            return get_current_client_id()
        except RuntimeError:
            raise DatabaseError(
                detail="UnitOfWork requiere client_id o contexto de tenant",
                internal_code="UOW_CLIENT_ID_REQUIRED"
            )
    
    async def __aenter__(self):
        """Inicia la transacción."""
        self.session = await get_db_connection(
            connection_type=self.connection_type,
            client_id=self.client_id
        ).__aenter__()
        logger.debug(
            f"[UOW] Transacción iniciada para cliente {self.client_id} "
            f"(connection_type={self.connection_type.value})"
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra la transacción (commit o rollback)."""
        if exc_type:
            # Error ocurrió → Rollback
            if self.session:
                await self.session.rollback()
                self._rolled_back = True
                logger.warning(
                    f"[UOW] Rollback ejecutado para cliente {self.client_id} "
                    f"después de {self._operations_count} operaciones: {exc_val}"
                )
        else:
            # Sin errores → Commit
            if self.session:
                await self.session.commit()
                self._committed = True
                logger.debug(
                    f"[UOW] Commit ejecutado para cliente {self.client_id} "
                    f"({self._operations_count} operaciones)"
                )
        
        # Cerrar sesión
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
    
    async def execute(
        self,
        query: Union[str, ClauseElement, TextClause],
        params: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Ejecuta una query dentro de la transacción.
        
        Args:
            query: Query SQL. Puede ser:
                - String SQL (se convierte a TextClause)
                - Objeto SQLAlchemy Core (Select, Update, Delete, Insert)
                - TextClause (resultado de text().bindparams())
            params: Parámetros opcionales (solo para strings).
                Si query es string y tiene params, se usa text().bindparams()
        
        Returns:
            - Para SELECT: Lista de diccionarios con resultados
            - Para UPDATE/DELETE/INSERT: Dict con {"rows_affected": N}
        
        Raises:
            DatabaseError: Si UnitOfWork no está activo o hay error en ejecución
        """
        if not self.session:
            raise DatabaseError(
                detail="UnitOfWork no está activo. Usar dentro de 'async with'",
                internal_code="UOW_NOT_ACTIVE"
            )
        
        # Convertir string a TextClause si es necesario
        if isinstance(query, str):
            if params:
                query = text(query).bindparams(**params)
            else:
                query = text(query)
        
        try:
            self._operations_count += 1
            result = await self.session.execute(query)
            
            # Si es SELECT, retornar resultados
            if isinstance(query, (Select, TextClause)) or isinstance(query, str):
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
            
            # Para UPDATE/DELETE/INSERT, retornar rowcount
            return {"rows_affected": result.rowcount}
            
        except Exception as e:
            logger.error(
                f"[UOW] Error ejecutando query (operación #{self._operations_count}): {e}",
                exc_info=True
            )
            raise DatabaseError(
                detail=f"Error en UnitOfWork: {str(e)}",
                internal_code="UOW_EXECUTION_ERROR"
            )
    
    def is_committed(self) -> bool:
        """Verifica si la transacción fue commiteada."""
        return self._committed
    
    def is_rolled_back(self) -> bool:
        """Verifica si la transacción fue revertida."""
        return self._rolled_back
    
    def get_operations_count(self) -> int:
        """Retorna el número de operaciones ejecutadas en esta transacción."""
        return self._operations_count


# Función helper para uso directo
@asynccontextmanager
async def unit_of_work(
    client_id: Optional[UUID] = None,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
) -> AsyncIterator[UnitOfWork]:
    """
    Context manager helper para UnitOfWork.
    
    Ejemplo:
        async with unit_of_work(client_id=current_client_id) as uow:
            await uow.execute(query1)
            await uow.execute(query2)
    """
    async with UnitOfWork(client_id=client_id, connection_type=connection_type) as uow:
        yield uow
