"""
Tests de compatibilidad: Validar que imports antiguos siguen funcionando.

✅ FASE 2: Validar que migración a estructura modular no rompe código existente
"""

import pytest
import warnings


class TestSQLConstantsCompatibility:
    """
    Tests para validar compatibilidad durante migración FASE 2.
    
    ✅ Estos tests validan que:
    - Imports antiguos desde sql_constants.py siguen funcionando
    - Imports nuevos desde queries.{modulo} funcionan
    - Ambos apuntan a las mismas queries
    """
    
    def test_old_imports_still_work(self):
        """Validar que imports antiguos desde sql_constants.py funcionan."""
        # Capturar warnings de deprecation
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            
            # Imports antiguos deben funcionar
            from app.infrastructure.database.sql_constants import (
                GET_USER_MAX_ACCESS_LEVEL,
                GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
                SELECT_USUARIOS_PAGINATED,
                SELECT_ROLES_PAGINATED,
                GET_AREAS_PAGINATED_QUERY,
                INSERT_AUTH_AUDIT_LOG,
            )
            
            # Validar que no son None
            assert GET_USER_MAX_ACCESS_LEVEL is not None
            assert GET_USER_ACCESS_LEVEL_INFO_COMPLETE is not None
            assert SELECT_USUARIOS_PAGINATED is not None
            assert SELECT_ROLES_PAGINATED is not None
            assert GET_AREAS_PAGINATED_QUERY is not None
            assert INSERT_AUTH_AUDIT_LOG is not None
    
    def test_new_imports_work(self):
        """Validar que imports nuevos desde queries.{modulo} funcionan."""
        # Imports nuevos deben funcionar
        from app.infrastructure.database.queries.auth.auth_queries import (
            GET_USER_MAX_ACCESS_LEVEL,
            GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
        )
        
        from app.infrastructure.database.queries.users.user_queries import (
            SELECT_USUARIOS_PAGINATED,
        )
        
        from app.infrastructure.database.queries.rbac.rbac_queries import (
            SELECT_ROLES_PAGINATED,
        )
        
        from app.infrastructure.database.queries.menus.menu_queries import (
            GET_AREAS_PAGINATED_QUERY,
        )
        
        from app.infrastructure.database.queries.audit.audit_queries import (
            INSERT_AUTH_AUDIT_LOG,
        )
        
        # Validar que no son None
        assert GET_USER_MAX_ACCESS_LEVEL is not None
        assert GET_USER_ACCESS_LEVEL_INFO_COMPLETE is not None
        assert SELECT_USUARIOS_PAGINATED is not None
        assert SELECT_ROLES_PAGINATED is not None
        assert GET_AREAS_PAGINATED_QUERY is not None
        assert INSERT_AUTH_AUDIT_LOG is not None
    
    def test_old_and_new_imports_are_same(self):
        """Validar que imports antiguos y nuevos apuntan a las mismas queries."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            
            # Importar desde ambos lugares
            from app.infrastructure.database.sql_constants import (
                GET_USER_MAX_ACCESS_LEVEL as OLD_GET_USER_MAX_ACCESS_LEVEL,
            )
            
            from app.infrastructure.database.queries.auth.auth_queries import (
                GET_USER_MAX_ACCESS_LEVEL as NEW_GET_USER_MAX_ACCESS_LEVEL,
            )
            
            # Deben ser la misma query (mismo contenido)
            assert OLD_GET_USER_MAX_ACCESS_LEVEL == NEW_GET_USER_MAX_ACCESS_LEVEL
    
    def test_deprecation_warning_shown(self):
        """Validar que deprecation warning se muestra al importar sql_constants."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Importar sql_constants debe mostrar warning
            import app.infrastructure.database.sql_constants
            
            # Debe haber al menos un warning de deprecation
            assert len(w) > 0
            assert any("deprecated" in str(warning.message).lower() for warning in w)
    
    def test_queries_module_re_exports(self):
        """Validar que queries/__init__.py re-exporta correctamente."""
        # Importar desde queries/__init__.py debe funcionar
        from app.infrastructure.database.queries import (
            GET_USER_MAX_ACCESS_LEVEL,
            SELECT_USUARIOS_PAGINATED,
            SELECT_ROLES_PAGINATED,
            GET_AREAS_PAGINATED_QUERY,
            INSERT_AUTH_AUDIT_LOG,
        )
        
        assert GET_USER_MAX_ACCESS_LEVEL is not None
        assert SELECT_USUARIOS_PAGINATED is not None
        assert SELECT_ROLES_PAGINATED is not None
        assert GET_AREAS_PAGINATED_QUERY is not None
        assert INSERT_AUTH_AUDIT_LOG is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
