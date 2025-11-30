from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime

from app.infrastructure.database.queries import (
    execute_insert,
    INSERT_AUTH_AUDIT_LOG,
    INSERT_LOG_SINCRONIZACION_USUARIO,
)
from app.core.exceptions import DatabaseError
from app.infrastructure.database.repositories.base_repository import BaseService

logger = logging.getLogger(__name__)


class AuditService(BaseService):
    """
    Servicio centralizado para registrar eventos de auditoría en:
    - auth_audit_log  (autenticación / seguridad)
    - log_sincronizacion_usuario (sincronización entre instalaciones)

    IMPORTANTE:
    - No altera el flujo funcional si falla el registro de auditoría.
    - Respeta el contexto multi-tenant: la conexión usada será la misma
      que resuelva el contexto actual (cliente/subdominio) o la que
      se haya configurado previamente mediante el router multi-DB.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def registrar_auth_event(
        *,
        cliente_id: int,
        evento: str,
        exito: bool,
        usuario_id: Optional[int] = None,
        nombre_usuario_intento: Optional[str] = None,
        descripcion: Optional[str] = None,
        codigo_error: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None,
        geolocation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Registra un evento en la tabla auth_audit_log.

        Todos los parámetros se basan en las columnas reales del schema.
        """
        try:
            # Serializar metadata a JSON (respetando longitud NVARCHAR(MAX))
            metadata_json = None
            if metadata:
                try:
                    metadata_json = json.dumps(metadata, ensure_ascii=False)
                except Exception:
                    # Nunca romper por error de serialización de metadata
                    metadata_json = None

            params = (
                cliente_id,
                usuario_id,
                evento,
                nombre_usuario_intento,
                descripcion,
                1 if exito else 0,
                codigo_error,
                ip_address,
                user_agent,
                device_info,
                geolocation,
                metadata_json,
            )

            result = execute_insert(INSERT_AUTH_AUDIT_LOG, params)

            logger.info(
                "[AUDIT] auth_audit_log registrado: evento=%s, cliente_id=%s, usuario_id=%s, exito=%s",
                evento,
                cliente_id,
                usuario_id,
                exito,
            )
            return result

        except DatabaseError:
            # Dejar que el decorador de BaseService maneje el detalle
            raise
        except Exception as e:
            # No interrumpir el flujo de negocio por errores de auditoría
            logger.error(f"[AUDIT] Error registrando auth_audit_log: {e}", exc_info=True)
            # Retornar estructura mínima para no romper llamadas
            return {"rows_affected": 0}

    @staticmethod
    @BaseService.handle_service_errors
    async def registrar_log_sincronizacion_usuario(
        *,
        cliente_origen_id: Optional[int],
        cliente_destino_id: Optional[int],
        usuario_id: int,
        tipo_sincronizacion: str,
        direccion: str,
        operacion: str,
        estado: str,
        mensaje_error: Optional[str] = None,
        campos_sincronizados: Optional[Dict[str, Any]] = None,
        cambios_detectados: Optional[Dict[str, Any]] = None,
        hash_antes: Optional[str] = None,
        hash_despues: Optional[str] = None,
        usuario_ejecutor_id: Optional[int] = None,
        duracion_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Registra una entrada en log_sincronizacion_usuario.

        Pensado para ser llamado desde procesos de sincronización de usuarios
        (manuales o automáticos) entre instalaciones on-premise / cloud.
        """
        try:
            campos_sincronizados_json = None
            if campos_sincronizados:
                try:
                    campos_sincronizados_json = json.dumps(
                        campos_sincronizados, ensure_ascii=False
                    )
                except Exception:
                    campos_sincronizados_json = None

            cambios_detectados_json = None
            if cambios_detectados:
                try:
                    cambios_detectados_json = json.dumps(
                        cambios_detectados, ensure_ascii=False
                    )
                except Exception:
                    cambios_detectados_json = None

            params = (
                cliente_origen_id,
                cliente_destino_id,
                usuario_id,
                tipo_sincronizacion,
                direccion,
                operacion,
                estado,
                mensaje_error,
                campos_sincronizados_json,
                cambios_detectados_json,
                hash_antes,
                hash_despues,
                usuario_ejecutor_id,
                duracion_ms,
            )

            result = execute_insert(INSERT_LOG_SINCRONIZACION_USUARIO, params)

            logger.info(
                "[AUDIT] log_sincronizacion_usuario registrado: usuario_id=%s, origen=%s, destino=%s, estado=%s",
                usuario_id,
                cliente_origen_id,
                cliente_destino_id,
                estado,
            )
            return result

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                f"[AUDIT] Error registrando log_sincronizacion_usuario: {e}",
                exc_info=True,
            )
            return {"rows_affected": 0}




