# app/modules/tax/presentation/endpoints.py
"""Router principal del módulo TAX (Libros Electrónicos / PLE SUNAT)."""
from fastapi import APIRouter
from app.modules.tax.presentation.endpoints_libro_electronico import router as libro_electronico_router

router = APIRouter()

router.include_router(libro_electronico_router, prefix="/libros-electronicos", tags=["TAX - Libros Electrónicos"])
