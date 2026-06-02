"""F-006: auth-config guards use LBAC require_super_admin (platform_admin compatible)."""
from unittest.mock import MagicMock

import pytest

from app.core.authorization.lbac import require_super_admin


@pytest.mark.asyncio
async def test_lbac_require_super_admin_accepts_platform_admin_level_5():
    user = MagicMock()
    user.is_super_admin = False
    user.access_level = 5
    user.roles = []
    user.nombre_usuario = "platform@admin"

    @require_super_admin()
    async def handler(current_user=None):
        return "ok"

    result = await handler(current_user=user)
    assert result == "ok"
