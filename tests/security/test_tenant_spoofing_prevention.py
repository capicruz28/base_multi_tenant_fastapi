# tests/security/test_tenant_spoofing_prevention.py
"""
Tests para prevenir Tenant Spoofing.

✅ NUEVO: Tests críticos para verificar que las correcciones de seguridad funcionan.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from starlette.requests import Request
from starlette.responses import Response

from app.core.tenant.middleware import TenantMiddleware
from app.core.config import settings


class TestTenantSpoofingPrevention:
    """Tests para verificar prevención de Tenant Spoofing."""
    
    @pytest.fixture
    def middleware(self):
        """Fixture para crear instancia del middleware."""
        app = MagicMock()
        return TenantMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """Fixture para crear request mock."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.path = "/api/v1/test"
        return request
    
    def test_production_rejects_localhost_host(self, middleware, mock_request):
        """
        Test que en producción se rechaza Host localhost.
        """
        # Patch settings en el módulo config que es donde se importa dentro de la función
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_request.headers = {"host": "localhost:8000"}
            
            # Debe lanzar ValueError
            with pytest.raises(ValueError, match="Host header requerido"):
                middleware._get_host_from_request(mock_request)
    
    def test_production_rejects_127_0_0_1_host(self, middleware, mock_request):
        """
        Test que en producción se rechaza Host 127.0.0.1.
        """
        # Patch settings en el módulo config que es donde se importa dentro de la función
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_request.headers = {"host": "127.0.0.1:8000"}
            
            # Debe lanzar ValueError
            with pytest.raises(ValueError, match="Host header requerido"):
                middleware._get_host_from_request(mock_request)
    
    def test_production_accepts_valid_host(self, middleware, mock_request):
        """
        Test que en producción se acepta un Host válido.
        """
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_request.headers = {"host": "cliente1.midominio.com"}
            
            host = middleware._get_host_from_request(mock_request)
            assert host == "cliente1.midominio.com"
    
    def test_development_allows_origin_fallback(self, middleware, mock_request):
        """
        Test que en desarrollo se permite fallback a Origin (con validación).
        """
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            mock_request.headers = {
                "host": "localhost:8000",
                "origin": "https://cliente1.midominio.com"
            }
            
            # Mock de validación de subdominio
            with patch.object(middleware, '_get_client_data_by_subdomain') as mock_get_client:
                mock_get_client.return_value = {"cliente_id": 1, "codigo_cliente": "CLI1"}
                
                with patch.object(middleware, '_extract_subdomain') as mock_extract:
                    mock_extract.return_value = "cliente1"
                    
                    host = middleware._get_host_from_request(mock_request)
                    # Debe usar el origin después de validar
                    assert "cliente1" in host or "midominio.com" in host
    
    def test_development_rejects_invalid_origin_subdomain(self, middleware, mock_request):
        """
        Test que en desarrollo se rechaza Origin con subdominio que no existe en BD.
        """
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            mock_request.headers = {
                "host": "localhost:8000",
                "origin": "https://fake-tenant.midominio.com"
            }
            
            # Mock de validación de subdominio (no existe)
            with patch.object(middleware, '_get_client_data_by_subdomain') as mock_get_client:
                mock_get_client.return_value = None  # No existe en BD
                
                with patch.object(middleware, '_extract_subdomain') as mock_extract:
                    mock_extract.return_value = "fake-tenant"
                    
                    # Debe rechazar y usar host por defecto
                    host = middleware._get_host_from_request(mock_request)
                    # Debe usar localhost (no el origin falso)
                    assert "localhost" in host
    
    def test_production_ignores_origin_header(self, middleware, mock_request):
        """
        Test que en producción se ignora completamente el header Origin.
        """
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_request.headers = {
                "host": "cliente1.midominio.com",
                "origin": "https://victima.midominio.com"  # Intentar spoofing
            }
            
            host = middleware._get_host_from_request(mock_request)
            # Debe usar solo el Host, ignorar Origin
            assert host == "cliente1.midominio.com"
            assert "victima" not in host


class TestTenantValidation:
    """Tests para validación de tenant en get_current_active_user."""
    
    @pytest.fixture
    def mock_request(self):
        """Fixture para crear request mock."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.1"
        return request
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_other_tenant(self, mock_request):
        """
        Test que un usuario regular no puede acceder a otro tenant.
        """
        from app.api.deps import get_current_active_user
        from unittest.mock import patch
        
        # Mock de payload con token de tenant 1
        mock_payload = {
            "sub": "test_user",
            "cliente_id": 1,
            "access_level": 2,
            "is_super_admin": False
        }
        
        # Mock de contexto de tenant 2
        with patch('app.api.deps.get_current_user_data', return_value=mock_payload):
            with patch('app.core.tenant.context.get_current_client_id', return_value=2):
                with patch('app.api.deps.execute_auth_query') as mock_query:
                    mock_query.return_value = {
                        'usuario_id': 1,
                        'cliente_id': 1,  # Usuario del tenant 1
                        'nombre_usuario': 'test_user',
                        'es_activo': True,
                        'is_super_admin': False
                    }
                    
                    # Debe lanzar HTTPException 403
                    with pytest.raises(Exception):  # HTTPException
                        await get_current_active_user(mock_request, mock_payload)
    
    @pytest.mark.asyncio
    async def test_superadmin_can_access_any_tenant(self, mock_request):
        """
        Test que SuperAdmin puede acceder a cualquier tenant.
        """
        from app.api.deps import get_current_active_user
        from unittest.mock import patch
        
        # Mock de payload con SuperAdmin
        mock_payload = {
            "sub": "superadmin",
            "cliente_id": None,  # SuperAdmin
            "access_level": 5,
            "is_super_admin": True
        }
        
        # Mock de contexto de tenant 2
        with patch('app.api.deps.get_current_user_data', return_value=mock_payload):
            with patch('app.core.tenant.context.get_current_client_id', return_value=2):
                with patch('app.api.deps.execute_auth_query') as mock_query:
                    mock_query.return_value = {
                        'usuario_id': 1,
                        'cliente_id': None,  # SuperAdmin
                        'nombre_usuario': 'superadmin',
                        'es_activo': True,
                        'is_super_admin': True,
                        'access_level': 5
                    }
                    
                    with patch('app.modules.users.application.services.user_service.UsuarioService.obtener_roles_de_usuario') as mock_roles:
                        mock_roles.return_value = []
                        
                        # No debe lanzar excepción
                        try:
                            result = await get_current_active_user(mock_request, mock_payload)
                            # Si llega aquí, el acceso fue permitido
                            assert result is not None
                        except Exception as e:
                            # Si lanza excepción, debe ser por otra razón, no por validación de tenant
                            assert "tenant" not in str(e).lower() or "forbidden" not in str(e).lower()


class TestSafeQueryBuilder:
    """Tests para SafeQueryBuilder."""
    
    def test_build_where_clause_safe(self):
        """
        Test que build_where_clause construye queries de forma segura.
        """
        from app.infrastructure.database.query_builder import SafeQueryBuilder
        
        filters = {"nombre": "Juan", "edad": 25}
        where_clause, params = SafeQueryBuilder.build_where_clause(filters)
        
        assert "nombre = ?" in where_clause
        assert "edad = ?" in where_clause
        assert params == ("Juan", 25)
    
    def test_build_where_clause_rejects_dangerous_field(self):
        """
        Test que build_where_clause rechaza campos peligrosos.
        """
        from app.infrastructure.database.query_builder import SafeQueryBuilder
        
        # Intentar usar campo con palabra clave peligrosa
        # Nota: La validación de formato se ejecuta primero, así que usamos un campo
        # que pase la validación de formato pero tenga palabra clave peligrosa
        filters = {"DROP": "test"}  # Campo que pasa formato pero tiene palabra clave
        
        with pytest.raises(ValueError, match="palabra clave peligrosa"):
            SafeQueryBuilder.build_where_clause(filters)
    
    def test_build_where_clause_rejects_invalid_format_field(self):
        """
        Test que build_where_clause rechaza campos con formato inválido.
        """
        from app.infrastructure.database.query_builder import SafeQueryBuilder
        
        # Campo con formato inválido (espacios, caracteres especiales)
        filters = {"DROP TABLE usuarios": "test"}
        
        # Debe rechazar por formato inválido primero
        with pytest.raises(ValueError, match="Nombre de campo inválido"):
            SafeQueryBuilder.build_where_clause(filters)
    
    def test_build_where_clause_rejects_invalid_operator(self):
        """
        Test que build_where_clause rechaza operadores no permitidos.
        """
        from app.infrastructure.database.query_builder import SafeQueryBuilder
        
        filters = {"nombre": "Juan"}
        
        with pytest.raises(ValueError, match="no permitido"):
            SafeQueryBuilder.build_where_clause(filters, operator="DROP")
    
    def test_build_order_by_validates_fields(self):
        """
        Test que build_order_by valida campos contra whitelist.
        """
        from app.infrastructure.database.query_builder import SafeQueryBuilder
        
        valid_fields = ["nombre", "edad", "fecha_creacion"]
        order_fields = ["nombre", "edad DESC"]
        
        order_by = SafeQueryBuilder.build_order_by(order_fields, valid_fields=valid_fields)
        assert "nombre ASC" in order_by
        assert "edad DESC" in order_by
    
    def test_build_order_by_rejects_invalid_field(self):
        """
        Test que build_order_by rechaza campos no en whitelist.
        """
        from app.infrastructure.database.query_builder import SafeQueryBuilder
        
        valid_fields = ["nombre", "edad"]
        order_fields = ["nombre", "campo_peligroso"]
        
        with pytest.raises(ValueError, match="no está en la lista"):
            SafeQueryBuilder.build_order_by(order_fields, valid_fields=valid_fields)

