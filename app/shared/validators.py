# app/shared/validators.py
"""
Funciones de normalización de texto para schemas Pydantic (Create/Update).

Usar con @field_validator importando estas funciones en cada schema.
"""
from typing import Optional


def normalize_upper(v: Optional[str]) -> Optional[str]:
    """strip + upper; tolera None."""
    return v.strip().upper() if v else v


def normalize_lower(v: Optional[str]) -> Optional[str]:
    """strip + lower; tolera None."""
    return v.strip().lower() if v else v


def normalize_strip(v: Optional[str]) -> Optional[str]:
    """solo strip; tolera None."""
    return v.strip() if v else v
