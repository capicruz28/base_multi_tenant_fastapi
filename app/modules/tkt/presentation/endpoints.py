# app/modules/tkt/presentation/endpoints.py
"""Router principal del modulo TKT (Mesa de Ayuda)."""
from fastapi import APIRouter
from app.modules.tkt.presentation.endpoints_ticket import router as ticket_router

router = APIRouter()

router.include_router(ticket_router, prefix="/tickets", tags=["TKT - Tickets"])
