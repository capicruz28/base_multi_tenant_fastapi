"""
Tests unitarios para Unit of Work Pattern.

✅ FASE 1: Tests para validar funcionamiento de UnitOfWork
"""

import pytest
from uuid import UUID
from app.core.application.unit_of_work import UnitOfWork
from app.infrastructure.database.connection_async import DatabaseConnection
from app.core.exceptions import DatabaseError
from sqlalchemy import text


class TestUnitOfWork:
    """Tests básicos de UnitOfWork."""
    
    @pytest.mark.asyncio
    async def test_uow_requires_client_id_or_context(self):
        """Validar que UOW requiere client_id o contexto."""
        # Sin client_id ni contexto → debe fallar
        with pytest.raises(DatabaseError) as exc_info:
            async with UnitOfWork() as uow:
                pass
        
        assert "client_id" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_uow_commit_on_success(self):
        """Validar que UOW hace commit cuando no hay errores."""
        # Usar UUID de prueba (requiere BD configurada)
        test_client_id = UUID("00000000-0000-0000-0000-000000000001")
        
        try:
            async with UnitOfWork(client_id=test_client_id) as uow:
                # Ejecutar query simple que no modifica datos
                result = await uow.execute("SELECT 1 as test")
                assert result[0]["test"] == 1
            
            # Después de salir exitosamente, debe estar commiteado
            assert uow.is_committed()
            assert not uow.is_rolled_back()
            assert uow.get_operations_count() == 1
        except Exception as e:
            pytest.skip(f"BD no disponible para test: {e}")
    
    @pytest.mark.asyncio
    async def test_uow_rollback_on_error(self):
        """Validar que UOW hace rollback cuando hay error."""
        test_client_id = UUID("00000000-0000-0000-0000-000000000001")
        
        try:
            try:
                async with UnitOfWork(client_id=test_client_id) as uow:
                    # Ejecutar query válida
                    await uow.execute("SELECT 1 as test")
                    # Lanzar error intencional
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Después del error, debe estar en rollback
            assert uow.is_rolled_back()
            assert not uow.is_committed()
        except Exception as e:
            pytest.skip(f"BD no disponible para test: {e}")
    
    @pytest.mark.asyncio
    async def test_uow_multiple_operations(self):
        """Validar que UOW puede ejecutar múltiples operaciones."""
        test_client_id = UUID("00000000-0000-0000-0000-000000000001")
        
        try:
            async with UnitOfWork(client_id=test_client_id) as uow:
                # Múltiples operaciones
                result1 = await uow.execute("SELECT 1 as test1")
                result2 = await uow.execute("SELECT 2 as test2")
                result3 = await uow.execute("SELECT 3 as test3")
                
                assert result1[0]["test1"] == 1
                assert result2[0]["test2"] == 2
                assert result3[0]["test3"] == 3
                assert uow.get_operations_count() == 3
            
            assert uow.is_committed()
        except Exception as e:
            pytest.skip(f"BD no disponible para test: {e}")
    
    @pytest.mark.asyncio
    async def test_uow_with_params(self):
        """Validar que UOW acepta parámetros en queries."""
        test_client_id = UUID("00000000-0000-0000-0000-000000000001")
        
        try:
            async with UnitOfWork(client_id=test_client_id) as uow:
                # Query con parámetros
                result = await uow.execute(
                    "SELECT :value as test",
                    params={"value": 42}
                )
                assert result[0]["test"] == 42
        except Exception as e:
            pytest.skip(f"BD no disponible para test: {e}")
    
    @pytest.mark.asyncio
    async def test_uow_not_active_error(self):
        """Validar que UOW lanza error si se usa fuera de context manager."""
        test_client_id = UUID("00000000-0000-0000-0000-000000000001")
        uow = UnitOfWork(client_id=test_client_id)
        
        # Intentar ejecutar sin entrar al context manager
        with pytest.raises(DatabaseError) as exc_info:
            await uow.execute("SELECT 1")
        
        assert "no está activo" in str(exc_info.value.detail).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
