# app/modules/pm/presentation/endpoints.py
"""Router principal del modulo PM (Gestion de Proyectos)."""
from fastapi import APIRouter
from app.modules.pm.presentation.endpoints_proyecto import router as proyecto_router

router = APIRouter()

router.include_router(proyecto_router, prefix="/proyectos", tags=["PM - Proyectos"])
