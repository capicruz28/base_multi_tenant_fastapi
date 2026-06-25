"""
Generación de contraseñas temporales seguras (onboarding, reset administrativo).
"""
from __future__ import annotations

import secrets
import string


def generar_contrasena_segura(length: int = 12) -> str:
    """12 caracteres: mayúsculas, minúsculas, números y al menos 1 especial."""
    if length < 4:
        raise ValueError("La longitud mínima de contraseña es 4")
    minus = string.ascii_lowercase
    mayus = string.ascii_uppercase
    digitos = string.digits
    especiales = "!@#$%&*"
    chars = [
        secrets.choice(mayus),
        secrets.choice(minus),
        secrets.choice(digitos),
        secrets.choice(especiales),
    ]
    pool = minus + mayus + digitos + especiales
    chars.extend(secrets.choice(pool) for _ in range(length - 4))
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


__all__ = ["generar_contrasena_segura"]
