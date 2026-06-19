"""PA-001: paginación de GET /api/v1/usuarios/ sobre usuarios distintos, no filas JOIN."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.infrastructure.database.queries.users.user_queries import (
    SELECT_USUARIOS_PAGINATED,
    SELECT_USUARIOS_PAGINATED_MULTI_DB,
)
from app.modules.users.application.services.user_service import UsuarioService

CLIENTE_ID = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
NOW = datetime(2026, 1, 15, 10, 0, 0)


def _usuario_base(usuario_id: UUID) -> dict:
    return {
        "usuario_id": usuario_id,
        "nombre_usuario": f"user_{str(usuario_id)[:8]}",
        "correo": f"{str(usuario_id)[:8]}@test.com",
        "nombre": "Nombre",
        "apellido": "Apellido",
        "es_activo": True,
        "correo_confirmado": True,
        "fecha_creacion": NOW,
        "fecha_ultimo_acceso": None,
        "fecha_actualizacion": None,
        "cliente_id": CLIENTE_ID,
        "proveedor_autenticacion": "local",
        "fecha_ultimo_cambio_contrasena": None,
        "requiere_cambio_contrasena": False,
        "intentos_fallidos": 0,
        "fecha_bloqueo": None,
        "sincronizado_desde": None,
        "fecha_ultima_sincronizacion": None,
        "dni": None,
        "telefono": None,
        "referencia_externa_id": None,
        "referencia_externa_email": None,
        "es_eliminado": False,
    }


def _rol_fields(rol_suffix: int) -> dict:
    rol_id = uuid4()
    return {
        "rol_id": rol_id,
        "nombre_rol": f"Rol{rol_suffix}",
        "descripcion_rol": "Desc",
        "rol_es_activo": True,
        "rol_fecha_creacion": NOW,
        "rol_cliente_id": CLIENTE_ID,
        "rol_codigo_rol": f"ROL_{rol_suffix}",
    }


def _rows_multi_role(users_count: int, roles_per_user: int) -> list[dict]:
    rows: list[dict] = []
    for i in range(users_count):
        usuario_id = uuid4()
        base = _usuario_base(usuario_id)
        for r in range(roles_per_user):
            rows.append({**base, **_rol_fields(i * roles_per_user + r)})
    return rows


def _rows_single_role(users_count: int, start_index: int = 0) -> list[dict]:
    rows: list[dict] = []
    for i in range(users_count):
        usuario_id = uuid4()
        base = _usuario_base(usuario_id)
        rows.append({**base, **_rol_fields(start_index + i)})
    return rows


def _tenant_context(database_type: str = "single") -> MagicMock:
    ctx = MagicMock()
    ctx.database_type = database_type
    return ctx


@pytest.mark.asyncio
async def test_t_u1_multi_role_users_full_roles_on_page():
    """T-U1: usuarios multi-rol devuelven todos sus roles en la misma página."""
    select_rows = _rows_multi_role(users_count=5, roles_per_user=3)

    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            new_callable=AsyncMock,
            side_effect=[
                [{"": 5}],
                select_rows,
            ],
        ),
    ):
        result = await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=10,
        )

    assert len(result["usuarios"]) == 5
    assert all(len(u["roles"]) == 3 for u in result["usuarios"])
    assert result["total_usuarios"] == 5


@pytest.mark.asyncio
async def test_t_u2_respects_limit_distinct_users():
    """T-U2: la página contiene como máximo limit usuarios distintos."""
    select_rows = _rows_single_role(users_count=10)

    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            new_callable=AsyncMock,
            side_effect=[
                [{"": 25}],
                select_rows,
            ],
        ),
    ):
        result = await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=10,
        )

    assert len(result["usuarios"]) == 10
    usuario_ids = {u["usuario_id"] for u in result["usuarios"]}
    assert len(usuario_ids) == 10


@pytest.mark.asyncio
async def test_t_u3_pagination_metadata():
    """T-U3: metadatos de paginación coherentes con total y página."""
    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            new_callable=AsyncMock,
            side_effect=[
                [{"": 25}],
                _rows_single_role(users_count=10),
            ],
        ),
    ):
        result = await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=2,
            limit=10,
        )

    assert result["pagina_actual"] == 2
    assert result["total_usuarios"] == 25
    assert result["total_paginas"] == 3


@pytest.mark.asyncio
async def test_t_u4_user_without_roles():
    """T-U4: usuario sin roles aparece con roles vacío."""
    usuario_id = uuid4()
    row = {**_usuario_base(usuario_id), "rol_id": None}

    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            new_callable=AsyncMock,
            side_effect=[
                [{"": 1}],
                [row],
            ],
        ),
    ):
        result = await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=10,
        )

    assert len(result["usuarios"]) == 1
    assert result["usuarios"][0]["roles"] == []


@pytest.mark.asyncio
async def test_t_u5_search_params_propagated_to_count_and_select():
    """T-U5: búsqueda activa propaga buscar/buscar_pattern a COUNT y SELECT."""
    mock_query = AsyncMock(
        side_effect=[
            [{"": 1}],
            _rows_single_role(users_count=1),
        ]
    )

    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            mock_query,
        ),
    ):
        await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=10,
            search="ana",
        )

    assert mock_query.await_count == 2
    count_query = mock_query.await_args_list[0][0][0]
    select_query = mock_query.await_args_list[1][0][0]
    count_params = count_query.compile().params
    select_params = select_query.compile().params
    assert count_params["buscar"] == "%ana%"
    assert select_params["buscar"] == "%ana%"
    assert count_params["buscar_pattern"] == "%%ana%%"
    assert select_params["buscar_pattern"] == "%%ana%%"


@pytest.mark.asyncio
async def test_t_u6_multi_db_uses_multi_db_select_constant():
    """T-U6: database_type multi usa la variante MULTI_DB en SELECT."""
    mock_query = AsyncMock(
        side_effect=[
            [{"": 2}],
            _rows_single_role(users_count=2),
        ]
    )

    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("multi"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            mock_query,
        ),
    ):
        await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=10,
        )

    select_sql = str(mock_query.await_args_list[1][0][0])
    assert "PaginatedUsers" in select_sql
    assert ":cliente_id" not in select_sql


@pytest.mark.asyncio
async def test_t_u7_no_duplicate_user_across_pages_with_full_roles():
    """T-U7: regresión — mismo usuario no aparece en dos páginas con roles parciales."""
    page1_rows = _rows_multi_role(users_count=2, roles_per_user=3)
    page2_rows = _rows_multi_role(users_count=2, roles_per_user=2)

    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            new_callable=AsyncMock,
        ) as mock_query,
    ):
        mock_query.side_effect = [
            [{"": 4}],
            page1_rows,
            [{"": 4}],
            page2_rows,
        ]
        page1 = await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=2,
        )
        page2 = await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=2,
            limit=2,
        )

    page1_ids = {u["usuario_id"] for u in page1["usuarios"]}
    page2_ids = {u["usuario_id"] for u in page2["usuarios"]}
    assert page1_ids.isdisjoint(page2_ids)
    assert all(len(u["roles"]) == 3 for u in page1["usuarios"])
    assert all(len(u["roles"]) == 2 for u in page2["usuarios"])


def test_sql_paginates_users_before_role_expansion():
    """Verifica estructura PA-001: OFFSET en PaginatedUsers, no en SELECT final."""
    for query in (SELECT_USUARIOS_PAGINATED, SELECT_USUARIOS_PAGINATED_MULTI_DB):
        assert "PaginatedUsers AS" in query
        paginated_section = query.split("UserRoles AS")[0]
        assert "OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY" in paginated_section
        final_section = query.split("SELECT * FROM UserRoles")[1]
        assert "OFFSET" not in final_section
        assert "ORDER BY usuario_id" in query
