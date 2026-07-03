"""PR-F1-09 — Repository gateway delegation audit (RD-06-E02 / G-09)."""
from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.repositories.cfg_codigo_secuencia_repository import (
    CfgCodigoSecuenciaRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[2] / "app" / "infrastructure" / "database" / "repositories"

FORBIDDEN_IMPORTS = frozenset(
    {
        "get_db_connection",
        "get_connection_for_tenant",
        "create_async_engine",
    }
)
FORBIDDEN_MODULES = frozenset(
    {
        "app.core.tenant.routing",
    }
)


def _python_files_in_repositories() -> list[Path]:
    return sorted(REPO_ROOT.glob("*.py"))


def _collect_imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module)
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
    return found


@pytest.mark.unit
def test_repository_files_do_not_import_forbidden_gateway_bypass():
    violations: list[str] = []
    for path in _python_files_in_repositories():
        imports = _collect_imported_names(path)
        for forbidden in FORBIDDEN_IMPORTS:
            if forbidden in imports:
                violations.append(f"{path.name}: import {forbidden}")
        for mod in FORBIDDEN_MODULES:
            if mod in imports:
                violations.append(f"{path.name}: module {mod}")
    assert not violations, "G-09 bypass imports: " + "; ".join(violations)


@pytest.mark.unit
def test_cfg_repository_path_a_does_not_skip_tenant_validation():
    source = (REPO_ROOT / "cfg_codigo_secuencia_repository.py").read_text(encoding="utf-8")
    assert "skip_tenant_validation=True" not in source


@pytest.mark.unit
def test_base_repository_delegates_reads_via_execute_query():
    source = (REPO_ROOT / "base_repository.py").read_text(encoding="utf-8")
    assert "await execute_query(" in source
    assert "await execute_insert(" in source
    assert "await execute_update(" in source
    connection_import_line = next(
        line for line in source.splitlines()
        if line.startswith("from app.infrastructure.database.connection_async import")
    )
    assert "get_db_connection" not in connection_import_line


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cfg_repository_get_by_cliente_delegates_execute_query_when_no_session():
    repo = CfgCodigoSecuenciaRepository()
    client_id = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")

    with patch(
        "app.infrastructure.database.repositories.cfg_codigo_secuencia_repository.execute_query",
        AsyncMock(return_value=[]),
    ) as mock_execute:
        rows = await repo.get_by_cliente(client_id)

    assert rows == []
    mock_execute.assert_awaited_once()
    assert mock_execute.await_args.kwargs["connection_type"] == DatabaseConnection.ADMIN
    assert mock_execute.await_args.kwargs["client_id"] == client_id
    assert "skip_tenant_validation" not in mock_execute.await_args.kwargs
