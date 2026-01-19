"""
Tests unitarios básicos de aislamiento multi-tenant.

✅ FASE 3: MANTENIBILIDAD - Tests básicos
"""

import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context
from app.core.security.query_auditor import QueryAuditor
from app.core.exceptions import ValidationError, SecurityError


class TestTenantContext:
    """Tests del contexto de tenant."""
    
    def test_set_and_get_tenant_context(self):
        """Test: Establecer y obtener contexto de tenant."""
        tenant_id = uuid4()
        context = TenantContext(
            client_id=tenant_id,
            subdominio="test",
            codigo_cliente="TEST",
            database_type="single"
        )
        
        tokens = set_tenant_context(context)
        try:
            from app.core.tenant.context import get_current_tenant_context, get_current_client_id
            
            current_context = get_current_tenant_context()
            assert current_context is not None
            assert current_context.client_id == tenant_id
            assert current_context.subdominio == "test"
            
            current_id = get_current_client_id()
            assert current_id == tenant_id
        finally:
            reset_tenant_context(tokens)
    
    def test_tenant_context_isolation(self):
        """Test: Contextos de diferentes tenants no se mezclan."""
        tenant_1_id = uuid4()
        tenant_2_id = uuid4()
        
        context_1 = TenantContext(
            client_id=tenant_1_id,
            subdominio="tenant1",
            codigo_cliente="TENANT1",
            database_type="single"
        )
        
        context_2 = TenantContext(
            client_id=tenant_2_id,
            subdominio="tenant2",
            codigo_cliente="TENANT2",
            database_type="single"
        )
        
        tokens_1 = set_tenant_context(context_1)
        try:
            from app.core.tenant.context import get_current_client_id
            assert get_current_client_id() == tenant_1_id
        finally:
            reset_tenant_context(tokens_1)
        
        tokens_2 = set_tenant_context(context_2)
        try:
            from app.core.tenant.context import get_current_client_id
            assert get_current_client_id() == tenant_2_id
        finally:
            reset_tenant_context(tokens_2)


class TestQueryAuditor:
    """Tests del auditor de queries."""
    
    def test_auditor_detects_missing_tenant_filter(self):
        """Test: Auditor detecta queries sin filtro de tenant."""
        from sqlalchemy import select, text
        from app.infrastructure.database.tables import UsuarioTable
        
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
    
    def test_auditor_allows_global_tables(self):
        """Test: Auditor permite queries en tablas globales."""
        from sqlalchemy import select, text
        
        query = text("SELECT * FROM cliente")
        
        # No debe lanzar error para tablas globales
        result = QueryAuditor.validate_tenant_filter(
            query=query,
            table_name="cliente",
            client_id=uuid4()
        )
        
        assert result is True
    
    def test_auditor_allows_queries_with_tenant_filter(self):
        """Test: Auditor permite queries con filtro de tenant."""
        from sqlalchemy import select
        from app.infrastructure.database.tables import UsuarioTable
        
        tenant_id = uuid4()
        query = select(UsuarioTable).where(
            UsuarioTable.c.cliente_id == tenant_id,
            UsuarioTable.c.es_activo == True
        )
        
        result = QueryAuditor.validate_tenant_filter(
            query=query,
            table_name="usuario",
            client_id=tenant_id
        )
        
        assert result is True


class TestTenantValidation:
    """Tests de validación de tenant."""
    
    @pytest.mark.asyncio
    async def test_skip_tenant_validation_requires_flag(self):
        """Test: skip_tenant_validation requiere flag de configuración."""
        from app.infrastructure.database.queries_async import execute_query
        from sqlalchemy import select
        from app.infrastructure.database.tables import UsuarioTable
        
        tenant_id = uuid4()
        context = TenantContext(
            client_id=tenant_id,
            subdominio="test",
            codigo_cliente="TEST",
            database_type="single"
        )
        
        tokens = set_tenant_context(context)
        try:
            query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.ALLOW_TENANT_FILTER_BYPASS = False
                
                with pytest.raises(ValidationError) as exc_info:
                    await execute_query(query, skip_tenant_validation=True)
                
                assert "Bypass de validación de tenant no permitido" in str(exc_info.value.detail)
        finally:
            reset_tenant_context(tokens)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


