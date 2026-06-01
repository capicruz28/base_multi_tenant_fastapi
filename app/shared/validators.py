# app/shared/validators.py
"""
Funciones de normalización de texto para schemas Pydantic (Create/Update).

Usar con @field_validator importando estas funciones en cada schema.
"""
import re
from typing import Optional

# Mismo conjunto permitido que UserDataBase.validar_nombre_apellido (auth).
_PERSON_NAME_ALLOWED_RE = re.compile(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]")


def normalize_upper(v: Optional[str]) -> Optional[str]:
    """strip + upper; tolera None."""
    return v.strip().upper() if v else v


def normalize_lower(v: Optional[str]) -> Optional[str]:
    """strip + lower; tolera None."""
    return v.strip().lower() if v else v


def normalize_strip(v: Optional[str]) -> Optional[str]:
    """solo strip; tolera None."""
    return v.strip() if v else v


def sanitize_person_name(value: Optional[str]) -> Optional[str]:
    """
    Normaliza nombre/apellido para almacenamiento o respuestas auth.

    Elimina caracteres no alfabéticos (p. ej. '.' en razón social copiada por error)
    para que UserDataWithRoles.model_validate no falle en login.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    cleaned = _PERSON_NAME_ALLOWED_RE.sub(" ", text)
    cleaned = " ".join(cleaned.split())
    if not cleaned or cleaned.replace(" ", "").replace("-", "") == "":
        return None
    return cleaned
