-- ============================================================================
-- bootstrap_v2 | schema layer — Control Plane
-- V032 — Dedicated tenant provisioning state model (F4 PR-F4-01)
-- Base de datos: bd_hybrid_sistema_central (CP)
-- PREREQUISITO: V020 (cliente)
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. tenant_provisioning_run — ejecución saga por tenant
-- ---------------------------------------------------------------------------
CREATE TABLE tenant_provisioning_run (
    provisioning_run_id     UNIQUEIDENTIFIER    NOT NULL
                            DEFAULT NEWID()
                            CONSTRAINT PK_tenant_provisioning_run PRIMARY KEY,

    cliente_id              UNIQUEIDENTIFIER    NOT NULL,

    provisioning_state      NVARCHAR(20)        NOT NULL,
    is_current              BIT                 NOT NULL DEFAULT 1,
    attempt_number          INT                 NOT NULL DEFAULT 1,

    idempotency_key         NVARCHAR(64)        NULL,
    current_step_code       NVARCHAR(40)        NULL,

    started_at              DATETIME2           NOT NULL DEFAULT SYSDATETIME(),
    updated_at              DATETIME2           NOT NULL DEFAULT SYSDATETIME(),
    ready_at                DATETIME2           NULL,
    failed_at               DATETIME2           NULL,

    last_error_code         NVARCHAR(64)        NULL,
    last_error_message      NVARCHAR(500)       NULL,

    created_by_usuario_id   UNIQUEIDENTIFIER    NULL,

    CONSTRAINT FK_tpr_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES cliente(cliente_id)
        ON DELETE CASCADE,

    CONSTRAINT CK_tpr_provisioning_state
        CHECK (provisioning_state IN ('provisioning', 'ready', 'failed'))
);

CREATE INDEX IDX_tpr_cliente
    ON tenant_provisioning_run (cliente_id, is_current, started_at DESC);

CREATE UNIQUE INDEX UQ_tpr_cliente_current
    ON tenant_provisioning_run (cliente_id)
    WHERE is_current = 1;

CREATE UNIQUE INDEX UQ_tpr_cliente_idempotency
    ON tenant_provisioning_run (cliente_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 2. tenant_provisioning_step — markers por paso saga (S1–S10)
-- ---------------------------------------------------------------------------
CREATE TABLE tenant_provisioning_step (
    provisioning_step_id    UNIQUEIDENTIFIER    NOT NULL
                            DEFAULT NEWID()
                            CONSTRAINT PK_tenant_provisioning_step PRIMARY KEY,

    provisioning_run_id     UNIQUEIDENTIFIER    NOT NULL,
    cliente_id              UNIQUEIDENTIFIER    NOT NULL,

    step_code               NVARCHAR(40)        NOT NULL,
    saga_order              TINYINT             NOT NULL,
    step_status             NVARCHAR(20)        NOT NULL DEFAULT 'pending',

    started_at              DATETIME2           NULL,
    completed_at            DATETIME2           NULL,

    error_code              NVARCHAR(64)        NULL,
    error_message           NVARCHAR(500)       NULL,
    idempotency_marker      NVARCHAR(128)       NULL,

    CONSTRAINT FK_tps_run
        FOREIGN KEY (provisioning_run_id)
        REFERENCES tenant_provisioning_run(provisioning_run_id)
        ON DELETE CASCADE,

    CONSTRAINT FK_tps_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES cliente(cliente_id)
        ON DELETE NO ACTION,

    CONSTRAINT UQ_tps_run_step
        UNIQUE (provisioning_run_id, step_code),

    CONSTRAINT CK_tps_step_code
        CHECK (step_code IN (
            'registry',
            'storage_allocation',
            'create_database',
            'apply_schema_erp',
            'apply_schema_rbac',
            'apply_catalogs',
            'seed_tenant',
            'register_metadata',
            'activate_routing',
            'mark_ready'
        )),

    CONSTRAINT CK_tps_step_status
        CHECK (step_status IN ('pending', 'running', 'completed', 'failed', 'skipped'))
);

CREATE INDEX IDX_tps_run_order
    ON tenant_provisioning_step (provisioning_run_id, saga_order);

CREATE INDEX IDX_tps_cliente
    ON tenant_provisioning_step (cliente_id);

-- ---------------------------------------------------------------------------
-- 3. cliente — denormalización estado provisioning (Dedicated F4+)
-- ---------------------------------------------------------------------------
ALTER TABLE cliente ADD
    provisioning_state              NVARCHAR(20)        NULL,
    current_provisioning_run_id       UNIQUEIDENTIFIER    NULL;

ALTER TABLE cliente ADD CONSTRAINT CK_cliente_provisioning_state
    CHECK (
        provisioning_state IS NULL
        OR provisioning_state IN ('provisioning', 'ready', 'failed')
    );

ALTER TABLE cliente ADD CONSTRAINT FK_cliente_current_provisioning_run
    FOREIGN KEY (current_provisioning_run_id)
    REFERENCES tenant_provisioning_run(provisioning_run_id)
    ON DELETE NO ACTION;

CREATE INDEX IDX_cliente_provisioning_state
    ON cliente (provisioning_state)
    WHERE provisioning_state IS NOT NULL;
