# app/modules/menus/application/services/__init__.py
"""
Servicios de aplicación para menús
"""

from app.modules.menus.application.services.menu_service import MenuService
from app.modules.menus.application.services.area_service import AreaService

__all__ = [
    "MenuService",
    "AreaService"
]



