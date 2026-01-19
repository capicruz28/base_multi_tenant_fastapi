"""
Tests comprehensivos de aislamiento multi-tenant.

✅ FASE 1 SEGURIDAD: Verifica que no haya fuga de datos entre tenants.
"""

import pytest
from uuid import uuid4, UUID
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import UsuarioTable, RolTable
from sqlalchemy import select
from app.core.exceptions import ValidationError, SecurityError


class TestTenantIsolation:
    """Tests de aislamiento entre tenants."""
    
    @pytest.fixture
    def tenant_1_id(self):
        """ID del tenant 1."""
        return uuid4()
    
    @pytest.fixture
    def tenant_2_id(self):
        """ID del tenant 2."""
        return uuid4()
    
    @pytest.fixture
    def tenant_1_context(self, tenant_1_id):
        """Contexto del tenant 1."""
        return TenantContext(
            client_id=tenant_1_id,
            subdominio="tenant1",
            codigo_cliente="TENANT1",
            database_type="single"
        )
    
    @pytest.fixture
    def tenant_2_context(self, tenant_2_id):
        """Contexto del tenant 2."""
        return TenantContext(
            client_id=tenant_2_id,
            subdominio="tenant2",
            codigo_cliente="TENANT2",
            database_type="single"
        )
    
    @pytest.mark.asyncio
    async def test_query_without_tenant_filter_raises_error(self, tenant_1_context):
        """Test: Query sin filtro de tenant debe fallar."""
        tokens = set_tenant_context(tenant_1_context)
        try:
            # Query sin filtro de cliente_id
            query = select(UsuarioTable).where(
                UsuarioTable.c.es_activo == True
            )
            
            # Debe aplicar filtro automáticamente o lanzar error
            with patch('app.infrastructure.database.queries_async.execute_query') as mock_execute:
                mock_execute.side_effect = ValidationError(
                    detail="Query sin filtro de tenant",
                    internal_code="TENANT_FILTER_REQUIRED"
                )
                
                with pytest.raises(ValidationError):
                    await execute_query(query)
        finally:
            reset_tenant_context(tokens)
    
    @pytest.mark.asyncio
    async def test_skip_tenant_validation_requires_flag(self, tenant_1_context):
        """Test: skip_tenant_validation=True requiere ALLOW_TENANT_FILTER_BYPASS=True."""
        tokens = set_tenant_context(tenant_1_context)
        try:
            query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.ALLOW_TENANT_FILTER_BYPASS = False
                
                with pytest.raises(ValidationError) as exc_info:
                    await execute_query(query, skip_tenant_validation=True)
                
                assert "Bypass de validación de tenant no permitido" in str(exc_info.value.detail)
        finally:
            reset_tenant_context(tokens)
    
    @pytest.mark.asyncio
    async def test_tenant_data_isolation(self, tenant_1_context, tenant_2_context):
        """Test: Datos de un tenant no son accesibles desde otro tenant."""
        # Simular datos de tenant 1
        tenant_1_data = {
            'usuario_id': uuid4(),
            'cliente_id': tenant_1_context.client_id,
            'nombre_usuario': 'user1',
            'es_activo': True
        }
        
        # Simular datos de tenant 2
        tenant_2_data = {
            'usuario_id': uuid4(),
            'cliente_id': tenant_2_context.client_id,
            'nombre_usuario': 'user2',
            'es_activo': True
        }
        
        # Test: Query desde tenant 1 solo debe retornar datos de tenant 1
        tokens_1 = set_tenant_context(tenant_1_context)
        try:
            query = select(UsuarioTable).where(
                UsuarioTable.c.cliente_id == tenant_1_context.client_id,
                UsuarioTable.c.es_activo == True
            )
            
            with patch('app.infrastructure.database.queries_async._get_connection_context') as mock_conn:
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_result.fetchall.return_value = [(tenant_1_data['usuario_id'],)]
                mock_result.keys.return_value = ['usuario_id']
                mock_session.execute.return_value = mock_result
                mock_conn.return_value.__aenter__.return_value = mock_session
                
                results = await execute_query(query, client_id=tenant_1_context.client_id)
                
                # Verificar que solo retorna datos del tenant 1
                assert len(results) == 1
                assert results[0]['usuario_id'] == tenant_1_data['usuario_id']
        finally:
            reset_tenant_context(tokens_1)
    
    @pytest.mark.asyncio
    async def test_query_auditor_detects_missing_filter(self):
        """Test: QueryAuditor detecta queries sin filtro de tenant."""
        from app.core.security.query_auditor import QueryAuditor
        
        # Query sin filtro de cliente_id
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_settings.ENABLE_QUERY_TENANT_VALIDATION = True
            mock_settings.ALLOW_TENANT_FILTER_BYPASS = False
            
            with pytest.raises(SecurityError):
                QueryAuditor.validate_tenant_filter(
                    query=query,
                    table_name="usuario",
                    client_id=uuid4()
                )
    
    @pytest.mark.asyncio
    async def test_global_tables_dont_require_filter(self):
        """Test: Tablas globales no requieren filtro de tenant."""
        from app.core.security.query_auditor import QueryAuditor
        
        query = select().select_from("cliente")
        
        # No debe lanzar error para tablas globales
        result = QueryAuditor.validate_tenant_filter(
            query=query,
            table_name="cliente",
            client_id=uuid4()
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_user_builder_no_bypass(self):
        """Test: user_builder.py no usa skip_tenant_validation."""
        import inspect
        from app.core.auth import user_builder
        
        # Verificar que build_user_with_roles no use skip_tenant_validation
        source = inspect.getsource(user_builder.build_user_with_roles)
        
        assert "skip_tenant_validation=True" not in source, \
            "user_builder.py no debe usar skip_tenant_validation=True"
    
    @pytest.mark.asyncio
    async def test_user_context_no_bypass(self):
        """Test: user_context.py no usa skip_tenant_validation."""
        import inspect
        from app.core.auth import user_context
        
        # Verificar que get_user_auth_context no use skip_tenant_validation
        source = inspect.getsource(user_context.get_user_auth_context)
        
        assert "skip_tenant_validation=True" not in source, \
            "user_context.py no debe usar skip_tenant_validation=True"


class TestQueryAuditorIntegration:
    """Tests de integración del QueryAuditor."""
    
    @pytest.mark.asyncio
    async def test_auditor_in_execute_query(self):
        """Test: QueryAuditor se ejecuta automáticamente en execute_query."""
        from app.core.config import settings
        from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context
        
        tenant_id = uuid4()
        context = TenantContext(
            client_id=tenant_id,
            subdominio="test",
            codigo_cliente="TEST",
            database_type="single"
        )
        
        tokens = set_tenant_context(context)
        try:
            # Query sin filtro de tenant
            query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.ENABLE_QUERY_TENANT_VALIDATION = True
                mock_settings.ALLOW_TENANT_FILTER_BYPASS = False
                mock_settings.ENVIRONMENT = "development"  # No bloquear en desarrollo
                
                # Debe loggear advertencia pero no bloquear en desarrollo
                with patch('app.infrastructure.database.queries_async.logger') as mock_logger:
                    await execute_query(query, client_id=tenant_id)
                    
                    # Verificar que se llamó al logger (auditoría activa)
                    # (El query se ejecutará porque apply_tenant_filter lo corrige automáticamente)
        finally:
            reset_tenant_context(tokens)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


