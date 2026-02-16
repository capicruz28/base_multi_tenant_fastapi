"""
Queries SQL para auditoría.

✅ FASE 2: Queries migradas desde sql_constants.py

QUERIES INCLUIDAS:
- INSERT_AUTH_AUDIT_LOG
- INSERT_LOG_SINCRONIZACION_USUARIO
"""

# ============================================
# QUERIES PARA AUDITORIA
# ============================================

INSERT_AUTH_AUDIT_LOG = """
INSERT INTO auth_audit_log (
    cliente_id,
    usuario_id,
    evento,
    nombre_usuario_intento,
    descripcion,
    exito,
    codigo_error,
    ip_address,
    user_agent,
    device_info,
    geolocation,
    metadata_json
)
OUTPUT INSERTED.log_id, INSERTED.fecha_evento
VALUES (
    :cliente_id,
    :usuario_id,
    :evento,
    :nombre_usuario_intento,
    :descripcion,
    :exito,
    :codigo_error,
    :ip_address,
    :user_agent,
    :device_info,
    :geolocation,
    :metadata_json
);
"""

INSERT_LOG_SINCRONIZACION_USUARIO = """
INSERT INTO log_sincronizacion_usuario (
    cliente_origen_id,
    cliente_destino_id,
    usuario_id,
    tipo_sincronizacion,
    direccion,
    operacion,
    estado,
    mensaje_error,
    campos_sincronizados,
    cambios_detectados,
    hash_antes,
    hash_despues,
    usuario_ejecutor_id,
    duracion_ms,
    fecha_sincronizacion
)
OUTPUT INSERTED.log_id, INSERTED.fecha_sincronizacion
VALUES (
    :cliente_origen_id,
    :cliente_destino_id,
    :usuario_id,
    :tipo_sincronizacion,
    :direccion,
    :operacion,
    :estado,
    :mensaje_error,
    :campos_sincronizados,
    :cambios_detectados,
    :hash_antes,
    :hash_despues,
    :usuario_ejecutor_id,
    :duracion_ms,
    GETDATE()
);
"""

__all__ = [
    "INSERT_AUTH_AUDIT_LOG",
    "INSERT_LOG_SINCRONIZACION_USUARIO",
]
