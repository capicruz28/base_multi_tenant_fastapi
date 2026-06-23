-- ============================================================================
-- SCRIPT: SESSION MANAGEMENT — CREATE TABLES (v3 — final con todas las correcciones)
-- DESCRIPCIÓN: Las 3 tablas del modelo de Identity Session Management
--              con Refresh Token Rotation y detección de replay attacks.
--
-- HISTORIAL DE VERSIONES:
--   v1 → Script base (capa1.sql original)
--   v2 → +login_method, +selection_token_completed en user_session
--         +usuario_id, +cliente_id desnormalizados en token_family
--   v3 → Cambios aplicados sobre v2:
--
--   user_session:
--     · last_activity_at  renombrado a last_refresh_at
--       (semántica exacta: se actualiza en POST /auth/refresh)
--     · +last_business_activity_at
--       (se actualiza con throttle de 5 min en get_current_active_user)
--     · revoked_reason ahora tiene CHECK constraint (texto libre → enum)
--     · ip_address renombrado a login_ip (clarifica que es snapshot del login)
--     · +last_seen_ip (se actualiza en cada refresh; permite rastrear cambios
--       de red: casa → oficina → VPN sin perder la IP de origen)
--
--   token_family:
--     · +current_token_id (referencia al token vigente; lookup O(1) sin buscar
--       el último is_used=0, is_revoked=0 en refresh_tokens)
--
--   refresh_tokens:
--     · revoked_reason ahora tiene CHECK constraint (igual que user_session)
--     · last_used_at se conserva (sirve para introspection endpoints donde
--       se valida el token sin rotarlo; used_at solo cubre la rotación normal)
--
-- BASE DE DATOS: bd_hybrid_sistema_central
-- PREREQUISITO:  cliente, usuario, org_empresa ya deben existir
-- DEPLOY NOTE:   Invalida todas las sesiones activas al desplegar.
--                Los usuarios deben volver a hacer login.
-- ============================================================================


-- ============================================================================
-- TABLA 1: user_session
-- ----------------------------------------------------------------------------
-- Representa la sesión lógica de un usuario por dispositivo.
-- Persiste durante toda la vida útil de la sesión (días o semanas),
-- independientemente de cuántos refresh tokens roten en ese período.
--
-- Relación clave:
--   usuario → N sesiones (multi-device: web, mobile, desktop)
--   sesión  → N familias de tokens (si la sesión se renueva o el token
--              es comprometido y se emite una nueva familia)
--   sesión  → N refresh_tokens (a través de token_family)
--
-- Campos de dispositivo viven aquí, NO en refresh_tokens, porque son
-- atributos del entorno desde donde el usuario se conectó, no del
-- token criptográfico en sí.
-- ============================================================================

CREATE TABLE user_session (

    -- ── Identificación ──────────────────────────────────────────────────────
    session_id                  UNIQUEIDENTIFIER    NOT NULL
                                DEFAULT NEWID()
                                CONSTRAINT PK_user_session PRIMARY KEY,

    -- ── Contexto multi-tenant ───────────────────────────────────────────────
    -- cliente_id y empresa_id se desnormalizan aquí para poder filtrar
    -- sesiones activas por tenant sin necesidad de JOIN a usuario.
    usuario_id                  UNIQUEIDENTIFIER    NOT NULL,
    cliente_id                  UNIQUEIDENTIFIER    NOT NULL,

    -- empresa_id puede ser NULL en el momento de creación de la sesión:
    -- el flujo de selección de empresa (selection_token) ocurre después
    -- del login. Se actualiza una vez que el usuario elige empresa.
    empresa_id                  UNIQUEIDENTIFIER    NULL,

    -- ── Método de autenticación ─────────────────────────────────────────────
    -- login_method: cómo fue autenticado el usuario al crear esta sesión.
    -- Útil para auditoría y para aplicar políticas de TTL distintas según
    -- el método. Ejemplos de política:
    --   password  → TTL 30 días
    --   sso       → TTL 8 horas (controlado por el IdP externo)
    --   2fa       → TTL 60 días (mayor confianza por segundo factor)
    --   api_key   → TTL configurable en cliente_auth_config
    login_method                NVARCHAR(20)        NOT NULL DEFAULT 'password'
                                CONSTRAINT CK_session_login_method
                                CHECK (login_method IN ('password', 'sso', '2fa', 'api_key')),

    -- ── Flujo de selección de empresa ───────────────────────────────────────
    -- selection_token_completed: registra si la sesión pasó por el flujo
    -- completo de selección de empresa:
    --   Login → selection_token (JWT stateless, blacklist por jti) → empresa → JWT final
    -- o si la empresa fue asignada directamente (usuario con una sola empresa).
    -- Este campo es informativo para auditoría; el selection_token se invalida
    -- operativamente por blacklist Redis, no por este flag.
    --   0 → empresa asignada directamente al autenticar (flujo directo)
    --   1 → empresa seleccionada después de validar el selection_token
    selection_token_completed   BIT                 NOT NULL DEFAULT 0,

    -- ── Identificación de dispositivo ───────────────────────────────────────
    -- platform: tipo de cliente que inició la sesión.
    -- Restringido a valores conocidos para evitar datos sucios.
    platform                    NVARCHAR(20)        NOT NULL
                                CONSTRAINT CK_session_platform
                                CHECK (platform IN ('web', 'mobile', 'desktop', 'api')),

    -- device_name: etiqueta legible por humanos del dispositivo.
    -- Ejemplo: "iPhone de Carlos", "Chrome en Windows 11".
    -- Se muestra al usuario en la pantalla "Mis sesiones activas".
    device_name                 NVARCHAR(100)       NULL,

    -- device_id: identificador persistente enviado por el cliente.
    -- En mobile suele ser el device token del OS; en web puede ser
    -- un UUID almacenado en localStorage al primer acceso.
    device_id                   NVARCHAR(100)       NULL,

	-- device_fingerprint: hash SHA-256 del conjunto de características del entorno
	-- (User-Agent + resolución + zona horaria + idioma + plataforma).
	-- Se genera en backend: SHA-256(JSON.stringify(datos)) → 64 chars hex.
	-- Se almacena el hash, no el JSON crudo, para evitar exponer información
	-- del dispositivo innecesariamente y optimizar comparaciones en índices.
	-- CHAR(64) y no VARCHAR porque SHA-256 hex es siempre exactamente 64 chars.
	device_fingerprint          CHAR(64)            NULL,

    -- user_agent: header raw completo. NVARCHAR(1000) para cubrir UA modernos
	-- (mobile WebView, Electron, bots) que superan fácilmente los 500 chars.
	-- Se conserva para auditoría forense y para derivar campos adicionales
	-- en el futuro si se necesitan sin perder el valor original.
	user_agent                  NVARCHAR(1000)      NULL,

    -- login_ip: IP en el momento exacto del login. Snapshot inmutable;
    -- nunca se actualiza después de la creación de la sesión.
    -- Soporta IPv4 (máx 15 chars) e IPv6 (máx 45 chars).
    login_ip                    VARCHAR(45)         NULL,

    -- last_seen_ip: última IP desde la que se usó un refresh token.
    -- Se actualiza en cada POST /auth/refresh junto con last_refresh_at.
    -- Permite detectar cambios de red (casa → oficina → VPN) como señal
    -- de riesgo sin perder la IP de origen (login_ip se conserva intacta).
    last_seen_ip                VARCHAR(45)         NULL,

    -- ── Estado de la sesión ─────────────────────────────────────────────────
    -- is_active: flag operativo para filtrar sesiones en queries frecuentes.
    -- Evaluar solo revoked_at + expires_at + familia en cada query sería
    -- costoso; este flag permite WHERE is_active = 1 directo sobre el índice.
    -- Se pone en 0 al hacer logout, al detectar compromiso, o al expirar.
    is_active                   BIT                 NOT NULL DEFAULT 1,

    -- revoked_at + revoked_reason: cuándo y por qué se cerró la sesión.
    -- revoked_reason tiene CHECK para evitar valores inconsistentes:
    --   'logout'         → cierre voluntario por el usuario
    --   'admin_force'    → revocación manual por un administrador
    --   'security'       → cierre automático por detección de ataque
    --   'expired'        → TTL máximo de sesión alcanzado
    --   'password_reset' → cambio de contraseña fuerza cierre de otras sesiones
    revoked_at                  DATETIME            NULL,
    revoked_reason              NVARCHAR(50)        NULL
                                CONSTRAINT CK_session_revoked_reason
                                CHECK (revoked_reason IS NULL OR revoked_reason IN (
                                    'logout',
                                    'admin_force',
                                    'security',
                                    'expired',
                                    'password_reset'
                                )),

    -- ── Actividad y ciclo de vida ────────────────────────────────────────────
    -- last_refresh_at: se actualiza ÚNICAMENTE en POST /auth/refresh.
    -- Representa actividad de autenticación (cuándo rotó el token por última vez).
    -- Permite calcular idle timeout de autenticación definido en
    -- cliente_auth_config.session_idle_timeout_minutes.
    -- NOTA: antes llamado last_activity_at en v1/v2. Renombrado para reflejar
    -- su semántica exacta y diferenciarlo de last_business_activity_at.
    last_refresh_at             DATETIME            NULL,

    -- last_business_activity_at: se actualiza en get_current_active_user
    -- (middleware de autenticación) cada vez que el usuario consume un
    -- endpoint protegido del ERP, con throttle de 5 minutos para no generar
    -- una escritura por request sobre el pool de 15 conexiones disponibles.
    -- Implementación sugerida en deps.py:
    --   if not last_business_activity_at or
    --      (now - last_business_activity_at) > timedelta(minutes=5):
    --       UPDATE user_session SET last_business_activity_at = now
    -- Permite mostrar en UI "Última actividad hace 2 minutos" con semántica
    -- real de negocio, independiente del ciclo de refresh del token.
    last_business_activity_at   DATETIME            NULL,

    created_at                  DATETIME            NOT NULL DEFAULT GETDATE(),

    -- expires_at: TTL máximo absoluto de la sesión.
	-- Este timeout prevalece incluso con actividad continua del usuario:
	-- si el usuario estuvo activo toda la sesión, al llegar expires_at
	-- debe volver a autenticarse de todas formas.
	-- Relación con remember_me:
	--   remember_me = false → expires_at = now + session_timeout_minutes
	--                         (sesión corta, típicamente horas)
	--   remember_me = true  → expires_at = now + remember_me_days
	--                         (sesión larga, típicamente 30-60 días)
	-- Ambos valores se configuran en cliente_auth_config por tenant.
	expires_at                  DATETIME            NOT NULL,

    -- ── Foreign keys ────────────────────────────────────────────────────────
    CONSTRAINT FK_session_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuario(usuario_id)
        ON DELETE CASCADE,                          -- Borrar usuario elimina sus sesiones

    CONSTRAINT FK_session_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES cliente(cliente_id)
        ON DELETE NO ACTION,                        -- cliente_id desnormalizado; cascade viene por usuario

    CONSTRAINT FK_session_empresa
        FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id)
        ON DELETE NO ACTION
);

-- ── Índices user_session ─────────────────────────────────────────────────────

-- Consulta más frecuente: sesiones activas de un usuario
-- (pantalla "Mis dispositivos" y validación de JWT)
CREATE INDEX IDX_session_usuario_activo
    ON user_session(usuario_id, is_active)
    WHERE is_active = 1;

-- Filtro multi-tenant: todas las sesiones de un cliente
CREATE INDEX IDX_session_cliente
    ON user_session(cliente_id, is_active);

-- Identificación de dispositivo conocido al hacer login
-- (para reusar sesión existente en lugar de crear una nueva)
CREATE INDEX IDX_session_device_usuario
    ON user_session(device_id, usuario_id)
    WHERE device_id IS NOT NULL;

-- Soporte para job nocturno de limpieza de sesiones expiradas
CREATE INDEX IDX_session_expires
    ON user_session(expires_at, is_active)
    WHERE is_active = 1;

-- Consulta por empresa (vista de sesiones activas desde el panel de admin)
CREATE INDEX IDX_session_empresa
    ON user_session(empresa_id, is_active)
    WHERE empresa_id IS NOT NULL;

-- Auditoría por método de login (ej: cuántas sesiones activas son SSO)
CREATE INDEX IDX_session_login_method
    ON user_session(login_method, is_active);

-- Detección de anomalías de red: sesiones donde login_ip ≠ last_seen_ip
-- Útil para alertas de seguridad y SIEM
CREATE INDEX IDX_session_last_seen_ip
    ON user_session(last_seen_ip, is_active)
    WHERE last_seen_ip IS NOT NULL;

-- Idle timeout de negocio: sesiones activas sin actividad real reciente
-- (job de limpieza o alertas de sesiones zombie)
CREATE INDEX IDX_session_business_activity
    ON user_session(last_business_activity_at, is_active)
    WHERE is_active = 1;


-- ============================================================================
-- TABLA 2: token_family
-- ----------------------------------------------------------------------------
-- Agrupa todos los refresh tokens que pertenecen a una misma cadena de
-- rotación dentro de una sesión. Es el mecanismo de seguridad central.
--
-- Flujo de rotación normal:
--   Token A emitido → family_id = F1
--   Token A usado   → Token B emitido, mismo family_id F1, parent_token_id = A
--   Token B usado   → Token C emitido, mismo family_id F1, parent_token_id = B
--
-- Detección de replay attack:
--   Token A fue robado y se usa después de que ya rotó a B.
--   El sistema detecta que A tiene is_used = 1.
--   Marca token_family.is_compromised = 1 en F1.
--   Todos los tokens con family_id = F1 quedan inválidos de golpe,
--   incluido el token C legítimo que tenga el usuario real.
--   Se fuerza re-autenticación completa. La sesión se revoca.
--
-- Por qué una tabla separada y no un campo en refresh_tokens:
--   Al comprometer la familia necesitamos una escritura atómica en un solo
--   registro (UPDATE token_family SET is_compromised = 1) en lugar de
--   un UPDATE masivo sobre N filas de refresh_tokens, reduciendo el riesgo
--   de condiciones de carrera bajo carga.
-- ============================================================================

CREATE TABLE token_family (

    -- ── Identificación ──────────────────────────────────────────────────────
    family_id               UNIQUEIDENTIFIER    NOT NULL
                            DEFAULT NEWID()
                            CONSTRAINT PK_token_family PRIMARY KEY,

    -- ── Vínculo con la sesión ───────────────────────────────────────────────
	-- Relación estricta 1:1 — cada sesión tiene exactamente una familia activa.
	-- Si se detecta un replay attack, la sesión se cierra (is_active = 0)
	-- y se fuerza nueva autenticación, lo que genera una nueva user_session
	-- con su propia token_family. No se reutiliza ni "salva" la sesión
	-- comprometida emitiendo una nueva familia dentro de ella.
    session_id              UNIQUEIDENTIFIER    NOT NULL,

    -- ── Contexto multi-tenant (desnormalizado) ───────────────────────────────
    -- usuario_id y cliente_id se repiten aquí para poder identificar al
    -- propietario de una familia comprometida sin necesidad de JOIN a
    -- user_session en el hot path de detección de replay attack.
    -- En ese escenario el sistema está bajo presión y cada JOIN adicional
    -- es latencia no justificada.
    usuario_id              UNIQUEIDENTIFIER    NOT NULL,
    cliente_id              UNIQUEIDENTIFIER    NOT NULL,

    -- ── Token vigente (optimización O(1)) ───────────────────────────────────
    -- current_token_id: referencia directa al último token activo de esta
    -- familia (is_used=0, is_revoked=0).
    -- Sin este campo, obtener el token vigente requiere buscar en refresh_tokens
    -- filtrando por family_id + estado, lo cual escala mal con familias longevas.
    -- Con este campo el lookup es O(1) directo.
    -- Debe actualizarse dentro de la misma transacción de rotación:
    --   BEGIN TRAN
    --     INSERT refresh_tokens (nuevo token B) → obtener token_id
    --     UPDATE token_family SET current_token_id = token_id_B
    --     UPDATE refresh_tokens SET is_used=1, used_at=now WHERE token_id = A
    --   COMMIT
    -- NULL en el instante de creación de la familia (antes de emitir el primer token).
    -- No tiene FK explícita para evitar dependencia circular con refresh_tokens;
    -- la integridad se garantiza en la capa de aplicación (transacción de rotación).
    current_token_id        UNIQUEIDENTIFIER    NULL,

    -- ── Estado de compromiso ────────────────────────────────────────────────
    -- is_compromised: flag que se activa cuando se detecta que un token
    -- ya rotado (is_used = 1 en refresh_tokens) fue presentado de nuevo.
    -- Una vez en 1, TODOS los tokens de esta familia deben rechazarse.
    is_compromised          BIT                 NOT NULL DEFAULT 0,
    compromised_at          DATETIME            NULL,

    -- invalidation_reason: razón detallada para auditoría y alertas SIEM.
    -- Valores sugeridos:
    --   'replay_detected'  → token ya usado fue presentado nuevamente
    --   'session_revoked'  → la sesión padre fue cerrada (logout, admin)
    --   'admin_force'      → invalidación manual por administrador
    --   'password_reset'   → cambio de contraseña invalida todas las familias
    --   'security_policy'  → violación de política (IP sospechosa, etc.)
    invalidation_reason     NVARCHAR(50)       NULL
                        CONSTRAINT CK_family_invalidation_reason
                        CHECK (invalidation_reason IS NULL OR invalidation_reason IN (
                            'replay_detected',
                            'session_revoked',
                            'admin_force',
                            'password_reset',
                            'security_policy'
                        )),

    -- ── Auditoría ───────────────────────────────────────────────────────────
    created_at              DATETIME            NOT NULL DEFAULT GETDATE(),

    -- ── Foreign keys ────────────────────────────────────────────────────────
    CONSTRAINT FK_family_session
        FOREIGN KEY (session_id)
        REFERENCES user_session(session_id)
        ON DELETE CASCADE,                          -- Cerrar sesión elimina sus familias

    CONSTRAINT FK_family_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuario(usuario_id)
        ON DELETE NO ACTION,                        -- Desnormalizado; cascade viene por session_id

    CONSTRAINT FK_family_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES cliente(cliente_id)
        ON DELETE NO ACTION                         -- Ídem
);

-- ── Índices token_family ─────────────────────────────────────────────────────

-- Lookup por sesión: revocar todas las familias al cerrar sesión
CREATE INDEX IDX_family_session
    ON token_family(session_id, is_compromised);

-- Monitoreo de familias comprometidas para alertas de seguridad y SIEM
CREATE INDEX IDX_family_comprometida
    ON token_family(is_compromised, compromised_at)
    WHERE is_compromised = 1;

-- Lookup directo por usuario en detección de replay (sin JOIN a user_session)
CREATE INDEX IDX_family_usuario
    ON token_family(usuario_id, is_compromised);

-- Lookup por cliente: revocar todas las familias de un tenant de golpe
CREATE INDEX IDX_family_cliente
    ON token_family(cliente_id, is_compromised);

-- Lookup directo por token vigente: cubre el flujo token → family → current_token
-- sin necesidad de buscar en refresh_tokens por family_id + estado.
CREATE INDEX IDX_family_current_token
    ON token_family(current_token_id)
    WHERE current_token_id IS NOT NULL;


-- ============================================================================
-- TABLA 3: refresh_tokens
-- ----------------------------------------------------------------------------
-- Almacena los tokens criptográficos individuales de cada rotación.
-- Cada fila representa UNA emisión de un refresh token.
--
-- Un token se usa exactamente una vez (is_used = 1 tras rotar)
-- o se revoca forzosamente (is_revoked = 1 por logout o ataque).
--
-- Semántica de estados (mutuamente excluyentes en operación normal):
--   is_used = 0, is_revoked = 0 → token vigente, puede usarse
--   is_used = 1, is_revoked = 0 → token consumido en rotación normal
--   is_used = 0, is_revoked = 1 → token invalidado forzosamente
--   is_used = 1, is_revoked = 1 → no debería ocurrir (violation en app layer)
--
-- Campos que NO están aquí (y por qué):
--   device_name, device_id, platform, ip_address, user_agent
--   → Son atributos de la sesión, no del token. Viven en user_session.
--   uso_count
--   → En RTR cada token se usa 0 o 1 veces. Si ves un 2, es un ataque;
--     para eso existe token_family.is_compromised.
-- ============================================================================

CREATE TABLE refresh_tokens (

    -- ── Identificación ──────────────────────────────────────────────────────
    token_id                UNIQUEIDENTIFIER    NOT NULL
                            DEFAULT NEWID()
                            CONSTRAINT PK_refresh_tokens PRIMARY KEY,

    -- ── Jerarquía del token ─────────────────────────────────────────────────
    -- family_id: familia de rotación a la que pertenece este token.
    -- Clave para la detección de replay: si la familia está comprometida,
    -- este token es inválido aunque no haya sido usado ni revocado.
    family_id               UNIQUEIDENTIFIER    NOT NULL,

    -- session_id: desnormalizado desde token_family para evitar un JOIN
    -- adicional en la validación de tokens (hot path del sistema).
    session_id              UNIQUEIDENTIFIER    NOT NULL,

    -- parent_token_id: token del cual nació éste en la última rotación.
    -- NULL solo en el primer token de la familia (emisión inicial).
    -- Permite reconstruir la cadena A→B→C para análisis forense:
    -- ¿desde cuándo fue robado el token que generó el replay?
    parent_token_id         UNIQUEIDENTIFIER    NULL,

    -- ── Contexto multi-tenant (desnormalizado) ───────────────────────────────
    -- Se repiten aquí por performance: la validación de tokens es el
    -- hot path del sistema y necesita el contexto de tenant sin JOINs.
    -- Patrón idéntico al usado en usuario_rol.cliente_id.
    cliente_id              UNIQUEIDENTIFIER    NOT NULL,
    empresa_id              UNIQUEIDENTIFIER    NULL,           -- NULL hasta selección de empresa
    usuario_id              UNIQUEIDENTIFIER    NOT NULL,

    -- ── Credencial criptográfica ─────────────────────────────────────────────
    -- token_hash: hash SHA-256 del token real. NUNCA almacenar el token en
    -- texto plano. El token real viaja solo en la respuesta HTTP (httpOnly cookie
    -- o body) y no se persiste. Se usa VARCHAR porque SHA-256 en hex
    -- es ASCII puro (64 chars); NVARCHAR desperdiciaría el doble de espacio.
    token_hash              VARCHAR(255)        NOT NULL
                            CONSTRAINT UQ_token_hash UNIQUE,

    -- ── Ciclo de vida ───────────────────────────────────────────────────────
    expires_at              DATETIME            NOT NULL,
    created_at              DATETIME            NOT NULL DEFAULT GETDATE(),

    -- last_used_at: momento en que este token fue presentado y procesado.
    -- En rotación normal coincide con used_at. Se mantiene separado porque
    -- last_used_at puede actualizarse en validaciones sin rotación
    -- (introspection endpoints donde se valida el token sin consumirlo).
    last_used_at            DATETIME            NULL,

    -- ── Estado del token ────────────────────────────────────────────────────
    -- is_used / used_at: el token fue consumido en una rotación normal.
    -- El sistema debe generar el token sucesor ANTES de marcar éste como usado
    -- (transacción atómica) para evitar dejar al cliente sin token válido.
    is_used                 BIT                 NOT NULL DEFAULT 0,
    used_at                 DATETIME            NULL,

    -- is_revoked / revoked_at / revoked_reason: el token fue invalidado
    -- forzosamente, fuera del flujo normal de rotación.
    -- revoked_reason tiene CHECK para evitar valores inconsistentes:
    --   'logout'             → cierre de sesión voluntario
    --   'replay_detected'    → se detectó reuso de token ya rotado
    --   'admin_force'        → revocación manual por administrador
    --   'password_reset'     → cambio de contraseña
    --   'family_compromised' → la familia fue marcada como comprometida
    is_revoked              BIT                 NOT NULL DEFAULT 0,
    revoked_at              DATETIME            NULL,
    revoked_reason          NVARCHAR(50)        NULL
                            CONSTRAINT CK_token_revoked_reason
                            CHECK (revoked_reason IS NULL OR revoked_reason IN (
                                'logout',
                                'replay_detected',
                                'admin_force',
                                'password_reset',
                                'family_compromised'
                            )),

    -- ── Foreign keys ────────────────────────────────────────────────────────
    CONSTRAINT FK_token_family
        FOREIGN KEY (family_id)
        REFERENCES token_family(family_id)
        ON DELETE NO ACTION,                        -- Conservar tokens para auditoría aunque
                                                    -- la familia sea eliminada por retención

    CONSTRAINT FK_token_session
        FOREIGN KEY (session_id)
        REFERENCES user_session(session_id)
        ON DELETE NO ACTION,                        -- Ídem: auditoría post-cierre de sesión

    CONSTRAINT FK_token_parent
        FOREIGN KEY (parent_token_id)
        REFERENCES refresh_tokens(token_id)
        ON DELETE NO ACTION,                        -- Self-reference; NO CASCADE para evitar
                                                    -- eliminaciones en cadena no controladas

    CONSTRAINT FK_token_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES cliente(cliente_id)
        ON DELETE NO ACTION,

    CONSTRAINT FK_token_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuario(usuario_id)
        ON DELETE NO ACTION,

    CONSTRAINT FK_token_empresa
        FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id)
        ON DELETE NO ACTION
);

-- ── Índices refresh_tokens ───────────────────────────────────────────────────

-- Validación de token entrante: lookup por hash (hot path, debe ser O(1))
-- El UNIQUE constraint ya genera un índice; este índice compuesto cubre
-- la consulta típica excluyendo tokens ya inválidos sin acceso al heap.
CREATE INDEX IDX_token_hash_activo
    ON refresh_tokens(token_hash, is_used, is_revoked, expires_at);

-- Validación de familia: todos los tokens activos de una familia.
-- Usado para: (a) detectar replay al encontrar un token is_used=1 siendo
-- presentado, y (b) revocar toda la familia en bloque.
CREATE INDEX IDX_token_family_estado
    ON refresh_tokens(family_id, is_used, is_revoked, expires_at);

-- Lookup por sesión: revocar todos los tokens al cerrar sesión
CREATE INDEX IDX_token_session_activo
    ON refresh_tokens(session_id, is_revoked, expires_at)
    WHERE is_revoked = 0;

-- Navegación de cadena de rotación (auditoría forense A→B→C)
CREATE INDEX IDX_token_parent
    ON refresh_tokens(parent_token_id)
    WHERE parent_token_id IS NOT NULL;

-- Soporte multi-tenant: tokens activos de un usuario en un cliente
CREATE INDEX IDX_token_usuario_cliente
    ON refresh_tokens(usuario_id, cliente_id, is_revoked, expires_at);

-- Job de limpieza nocturna: tokens expirados o ya usados candidatos a purga
CREATE INDEX IDX_token_cleanup
    ON refresh_tokens(expires_at, is_revoked, is_used);

-- Tokens usados en ventana activa: detección rápida de replay
-- (un token is_used=1 que aún no expiró siendo presentado = ataque)
CREATE INDEX IDX_token_used_activo
    ON refresh_tokens(is_used, expires_at)
    WHERE is_used = 1;

-- ============================================================================

PRINT 'Tablas user_session, token_family y refresh_tokens creadas exitosamente (v3).';
GO