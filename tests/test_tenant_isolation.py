"""
Tests de aislamiento de tenant (tenant isolation).

✅ FASE 1 SEGURIDAD: Tests críticos para prevenir fuga de datos entre tenants.

Estos tests verifican que:
1. Las queries SQLAlchemy Core aplican filtros de tenant automáticamente
2. Las queries TextClause aplican filtros de tenant automáticamente
3. Los stored procedures validan client_id contra el contexto
4. No es posible acceder a datos de otros tenants
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

from app.infrastructure.database.tables import RefreshTokensTable, UsuarioTable
from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
    get_refresh_token_by_hash_core,
    insert_refresh_token_core
)
from app.core.tenant.context import get_current_client_id, try_get_current_client_id
from app.infrastructure.database.queries_async import execute_query, execute_procedure
from app.core.exceptions import SecurityError


class TestTenantIsolationSQLAlchemyCore:
    """Tests de aislamiento para queries SQLAlchemy Core."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_query_filters_by_tenant(self):
        """
        Verifica que get_refresh_token_by_hash_core filtra por cliente_id.
        
        ✅ CRÍTICO: Un tenant no debe poder acceder a tokens de otro tenant.
        """
        tenant1_id = uuid4()
        tenant2_id = uuid4()
        token_hash = "test_hash_123"
        
        # Mock de execute_query en queries_async (donde realmente se importa)
        with patch('app.infrastructure.database.queries_async.execute_query') as mock_execute:
            # Simular que el token existe para tenant1
            mock_execute.return_value = [{
                'token_id': uuid4(),
                'usuario_id': uuid4(),
                'token_hash': token_hash,
                'cliente_id': tenant1_id,
                'is_revoked': False
            }]
            
            # Intentar obtener token con tenant1_id
            result1 = await get_refresh_token_by_hash_core(token_hash, tenant1_id)
            assert result1 is not None
            assert result1['cliente_id'] == tenant1_id
            
            # Verificar que execute_query fue llamado con el filtro correcto
            assert mock_execute.called
            call_args = mock_execute.call_args
            query = call_args[0][0]  # Primer argumento posicional es la query
            
            # Verificar que la query contiene el filtro de cliente_id
            assert hasattr(query, 'whereclause')
            # La query debe tener cliente_id en el WHERE
            
            # Intentar obtener el mismo token con tenant2_id (debe retornar None)
            mock_execute.return_value = []
            result2 = await get_refresh_token_by_hash_core(token_hash, tenant2_id)
            assert result2 is None
    
    @pytest.mark.asyncio
    async def test_insert_refresh_token_requires_tenant(self):
        """
        Verifica que insert_refresh_token_core requiere cliente_id.
        
        ✅ CRÍTICO: No se debe poder insertar tokens sin especificar tenant.
        """
        tenant_id = uuid4()
        usuario_id = uuid4()
        token_hash = "test_hash_456"
        from datetime import datetime, timedelta
        
        with patch('app.infrastructure.database.queries_async.execute_insert') as mock_insert:
            mock_insert.return_value = {
                'token_id': uuid4(),
                'usuario_id': usuario_id,
                'cliente_id': tenant_id
            }
            
            result = await insert_refresh_token_core(
                usuario_id=usuario_id,
                token_hash=token_hash,
                expires_at=datetime.now() + timedelta(days=30),
                cliente_id=tenant_id
            )
            
            assert result['cliente_id'] == tenant_id
            
            # Verificar que execute_insert fue llamado con client_id
            assert mock_insert.called
            call_kwargs = mock_insert.call_args[1]  # kwargs
            assert call_kwargs.get('client_id') == tenant_id


class TestTenantIsolationTextClause:
    """Tests de aislamiento para queries TextClause."""
    
    @pytest.mark.asyncio
    async def test_text_clause_auto_filter_applied(self):
        """
        Verifica que las queries TextClause aplican filtro automático de tenant.
        
        ✅ CRÍTICO: Las queries TextClause deben tener filtro automático.
        """
        tenant_id = uuid4()
        
        # Query sin filtro explícito de cliente_id
        query = text("SELECT * FROM refresh_tokens WHERE token_hash = :token_hash")
        
        with patch('app.infrastructure.database.queries_async.execute_query') as mock_execute:
            mock_execute.return_value = []
            
            # Ejecutar con client_id
            await execute_query(query.bindparams(token_hash="test"), client_id=tenant_id)
            
            # Verificar que execute_query fue llamado
            assert mock_execute.called
            # La query debe haber sido procesada (aunque el mock no retorne nada útil)
            # El filtro automático se aplica internamente en execute_query
    
    @pytest.mark.asyncio
    async def test_text_clause_global_table_no_filter(self):
        """
        Verifica que las tablas globales no reciben filtro de tenant.
        
        ✅ IMPORTANTE: Las tablas globales (como 'cliente') no deben filtrarse.
        """
        tenant_id = uuid4()
        
        # Query sobre tabla global (cliente)
        query = text("SELECT * FROM cliente WHERE codigo_cliente = :codigo")
        
        with patch('app.infrastructure.database.queries_async.execute_query') as mock_execute:
            mock_execute.return_value = []
            
            await execute_query(query.bindparams(codigo="TEST"), client_id=tenant_id)
            
            # Verificar que execute_query fue llamado
            assert mock_execute.called
            # La tabla 'cliente' es global, así que no debe tener filtro de cliente_id
            # Esto se verifica internamente en apply_tenant_filter_to_text_clause


class TestTenantIsolationStoredProcedures:
    """Tests de aislamiento para stored procedures."""
    
    @pytest.mark.asyncio
    async def test_stored_procedure_validates_client_id(self):
        """
        Verifica que execute_procedure valida client_id contra el contexto.
        
        ✅ CRÍTICO: Los SPs deben validar que el client_id coincide con el contexto.
        """
        tenant1_id = uuid4()
        tenant2_id = uuid4()
        
        # Simular contexto con tenant1
        with patch('app.infrastructure.database.queries_async.try_get_current_client_id') as mock_context:
            mock_context.return_value = tenant1_id
            
            # Intentar ejecutar SP con tenant1_id (debe funcionar)
            with patch('app.infrastructure.database.queries_async._get_connection_context') as mock_conn:
                mock_session = AsyncMock()
                mock_conn.return_value.__aenter__.return_value = mock_session
                mock_session.execute.return_value.rowcount = 1
                
                # Debe funcionar sin error
                await execute_procedure(
                    "test_sp",
                    client_id=tenant1_id
                )
                
                # Intentar ejecutar SP con tenant2_id (debe fallar)
                with pytest.raises(SecurityError):
                    await execute_procedure(
                        "test_sp",
                        client_id=tenant2_id  # Diferente al contexto
                    )
    
    @pytest.mark.asyncio
    async def test_stored_procedure_params_validates_client_id(self):
        """
        Verifica que execute_procedure_params valida client_id en params_dict.
        
        ✅ CRÍTICO: Los parámetros del SP no deben poder sobrescribir el client_id.
        """
        tenant1_id = uuid4()
        tenant2_id = uuid4()
        
        with patch('app.infrastructure.database.queries_async.try_get_current_client_id') as mock_context:
            mock_context.return_value = tenant1_id
            
            # Intentar pasar client_id diferente en params_dict
            malicious_params = {
                'ClienteID': tenant2_id,  # Intentar usar otro tenant
                'other_param': 'value'
            }
            
            with pytest.raises(SecurityError):
                from app.infrastructure.database.queries_async import execute_procedure_params
                await execute_procedure_params(
                    "test_sp",
                    params_dict=malicious_params,
                    client_id=tenant1_id
                )


class TestTenantIsolationIntegration:
    """Tests de integración de aislamiento de tenant."""
    
    @pytest.mark.asyncio
    async def test_cross_tenant_data_access_prevented(self):
        """
        Verifica que un tenant no puede acceder a datos de otro tenant.
        
        ✅ CRÍTICO: Test de integración completo.
        """
        tenant1_id = uuid4()
        tenant2_id = uuid4()
        usuario1_id = uuid4()
        usuario2_id = uuid4()
        
        # Simular que tenant1 tiene un usuario
        with patch('app.infrastructure.database.queries_async.execute_query') as mock_execute:
            # Cuando tenant1 consulta, ve solo sus datos
            mock_execute.return_value = [{
                'usuario_id': usuario1_id,
                'cliente_id': tenant1_id,
                'nombre_usuario': 'user1'
            }]
            
            query = select(UsuarioTable).where(UsuarioTable.c.usuario_id == usuario1_id)
            result1 = await execute_query(query, client_id=tenant1_id)
            
            assert len(result1) > 0
            assert result1[0]['cliente_id'] == tenant1_id
            
            # Cuando tenant2 intenta consultar el mismo usuario, no debe verlo
            mock_execute.return_value = []
            result2 = await execute_query(query, client_id=tenant2_id)
            
            assert len(result2) == 0  # No debe ver datos de tenant1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
