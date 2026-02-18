"""
Queries SQL para autenticación y gestión de usuarios.

✅ FASE 2: Queries migradas desde sql_constants.py

QUERIES INCLUIDAS:
- GET_USER_MAX_ACCESS_LEVEL
- IS_USER_SUPER_ADMIN
- GET_USER_ACCESS_LEVEL_INFO_COMPLETE
- INSERT_REFRESH_TOKEN
- GET_REFRESH_TOKEN_BY_HASH
- REVOKE_REFRESH_TOKEN
- REVOKE_REFRESH_TOKEN_BY_USER
- REVOKE_ALL_USER_TOKENS
- DELETE_EXPIRED_TOKENS
- GET_ACTIVE_SESSIONS_BY_USER
- GET_ALL_ACTIVE_SESSIONS
- REVOKE_REFRESH_TOKEN_BY_ID

TODAS LAS QUERIES USAN:
- Parámetros nombrados (:param) para seguridad
- text().bindparams() para ejecución
- Filtros de tenant automáticos
"""

# ============================================
# QUERIES PARA SISTEMA DE NIVELES LBAC
# ============================================

GET_USER_MAX_ACCESS_LEVEL = """
SELECT ISNULL(MAX(r.nivel_acceso), 1) as max_level
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = :usuario_id 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = :cliente_id OR r.cliente_id IS NULL)
"""

IS_USER_SUPER_ADMIN = """
SELECT COUNT(*) as is_super_admin
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = :usuario_id 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND r.codigo_rol = 'SUPER_ADMIN'
  AND r.nivel_acceso = 5
"""

GET_USER_ACCESS_LEVEL_INFO_COMPLETE = """
SELECT 
    ISNULL(MAX(r.nivel_acceso), 1) as max_level,
    COUNT(CASE WHEN r.codigo_rol = 'SUPER_ADMIN' AND r.nivel_acceso = 5 THEN 1 END) as super_admin_count,
    COUNT(*) as total_roles
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = :usuario_id 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = :cliente_id OR r.cliente_id IS NULL)
"""

# ============================================
# QUERIES PARA REFRESH TOKENS
# ============================================

INSERT_REFRESH_TOKEN = """
INSERT INTO refresh_tokens (
    usuario_id, token_hash, expires_at, client_type, ip_address, user_agent, cliente_id
)
OUTPUT INSERTED.token_id, INSERTED.usuario_id, INSERTED.cliente_id, INSERTED.expires_at, INSERTED.created_at
VALUES (:usuario_id, :token_hash, :expires_at, :client_type, :ip_address, :user_agent, :cliente_id);
"""

GET_REFRESH_TOKEN_BY_HASH = """
SELECT 
    token_id, usuario_id, token_hash, expires_at, 
    is_revoked, created_at, client_type, cliente_id
FROM refresh_tokens
WHERE token_hash = :token_hash
  AND cliente_id = :cliente_id
  AND is_revoked = 0
  AND expires_at > GETDATE();
"""

REVOKE_REFRESH_TOKEN = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.cliente_id
WHERE token_hash = :token_hash
  AND cliente_id = :cliente_id;
"""

REVOKE_REFRESH_TOKEN_BY_USER = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.cliente_id
WHERE usuario_id = :usuario_id
  AND cliente_id = :cliente_id
  AND is_revoked = 0;
"""

REVOKE_ALL_USER_TOKENS = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
WHERE usuario_id = :usuario_id
  AND cliente_id = :cliente_id;
"""

DELETE_EXPIRED_TOKENS = """
DELETE FROM refresh_tokens
WHERE expires_at < GETDATE()
  AND is_revoked = 1
  AND cliente_id = :cliente_id;
"""

GET_ACTIVE_SESSIONS_BY_USER = """
SELECT 
    token_id, usuario_id, cliente_id, created_at, last_used_at,
    device_name, device_id, ip_address, client_type
FROM refresh_tokens
WHERE usuario_id = :usuario_id
  AND cliente_id = :cliente_id
  AND is_revoked = 0
  AND expires_at > GETDATE()
ORDER BY last_used_at DESC;
"""

GET_ALL_ACTIVE_SESSIONS = """
SELECT 
    token_id, usuario_id, cliente_id, created_at, last_used_at,
    device_name, device_id, ip_address, client_type
FROM refresh_tokens
WHERE cliente_id = :cliente_id
  AND is_revoked = 0
  AND expires_at > GETDATE()
ORDER BY last_used_at DESC;
"""

REVOKE_REFRESH_TOKEN_BY_ID = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.usuario_id, INSERTED.cliente_id
WHERE token_id = :token_id
  AND cliente_id = :cliente_id;
"""

__all__ = [
    "GET_USER_MAX_ACCESS_LEVEL",
    "IS_USER_SUPER_ADMIN",
    "GET_USER_ACCESS_LEVEL_INFO_COMPLETE",
    "INSERT_REFRESH_TOKEN",
    "GET_REFRESH_TOKEN_BY_HASH",
    "REVOKE_REFRESH_TOKEN",
    "REVOKE_REFRESH_TOKEN_BY_USER",
    "REVOKE_ALL_USER_TOKENS",
    "DELETE_EXPIRED_TOKENS",
    "GET_ACTIVE_SESSIONS_BY_USER",
    "GET_ALL_ACTIVE_SESSIONS",
    "REVOKE_REFRESH_TOKEN_BY_ID",
]
