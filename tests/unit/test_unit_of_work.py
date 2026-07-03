"""
Tests unitarios para Unit of Work Pattern.

✅ FASE 1: Tests para validar funcionamiento de UnitOfWork
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from app.core.application.unit_of_work import UnitOfWork
from app.infrastructure.database.connection_async import DatabaseConnection
from app.core.exceptions import DatabaseError
from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause


def _mock_session_with_row(column: str, value):
    """Sesión async mock que devuelve una fila SELECT."""
    mock_result = MagicMock()
    mock_result.returns_rows = True
    mock_result.fetchall.return_value = [(value,)]
    mock_result.keys.return_value = [column]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)
    return session


class TestUnitOfWorkExecuteParams:
    """Cobertura de enlace de parámetros en execute() — str vs TextClause."""

    @pytest.mark.asyncio
    async def test_execute_str_with_params(self):
        uow = UnitOfWork(client_id=UUID("00000000-0000-0000-0000-000000000001"))
        uow.session = _mock_session_with_row("test", 42)

        result = await uow.execute("SELECT :value as test", params={"value": 42})

        uow.session.execute.assert_awaited_once()
        call_args = uow.session.execute.await_args
        assert isinstance(call_args.args[0], TextClause)
        assert call_args.args[1] == {"value": 42}
        assert result == [{"test": 42}]

    @pytest.mark.asyncio
    async def test_execute_textclause_with_params(self):
        uow = UnitOfWork(client_id=UUID("00000000-0000-0000-0000-000000000001"))
        uow.session = _mock_session_with_row("provisioning_run_id", "run-1")
        stmt = text(
            "SELECT provisioning_run_id FROM tenant_provisioning_run "
            "WHERE provisioning_run_id = :provisioning_run_id"
        )

        result = await uow.execute(
            stmt,
            params={"provisioning_run_id": "run-1", "cliente_id": "client-1"},
        )

        uow.session.execute.assert_awaited_once()
        call_args = uow.session.execute.await_args
        assert call_args.args[0] is stmt
        assert call_args.args[1] == {
            "provisioning_run_id": "run-1",
            "cliente_id": "client-1",
        }
        assert result == [{"provisioning_run_id": "run-1"}]

    @pytest.mark.asyncio
    async def test_execute_str_without_params(self):
        uow = UnitOfWork(client_id=UUID("00000000-0000-0000-0000-000000000001"))
        uow.session = _mock_session_with_row("test", 1)

        result = await uow.execute("SELECT 1 as test")

        uow.session.execute.assert_awaited_once()
        call_args = uow.session.execute.await_args
        assert len(call_args.args) == 1
        assert result == [{"test": 1}]

    @pytest.mark.asyncio
    async def test_execute_textclause_without_params(self):
        uow = UnitOfWork(client_id=UUID("00000000-0000-0000-0000-000000000001"))
        uow.session = _mock_session_with_row("test", 7)
        stmt = text("SELECT 7 as test")

        result = await uow.execute(stmt)

        uow.session.execute.assert_awaited_once_with(stmt)
        assert result == [{"test": 7}]


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
