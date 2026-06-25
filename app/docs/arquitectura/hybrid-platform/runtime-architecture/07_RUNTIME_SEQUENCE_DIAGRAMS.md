# 07 — Runtime Sequence Diagrams (Conceptuales)

**Etapa:** 4 — Runtime Architecture  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Restricción:** Diagramas conceptuales. Sin clases, métodos ni implementación.

---

## 1. Login

```mermaid
sequenceDiagram
    participant C as Cliente
    participant E as Edge
    participant I as Ingress Pipeline
    participant TR as Tenant Resolution
    participant CP as Control Plane Store
    participant IAM as IAM Gate
    participant TD as Tenant Data Store
    participant R as Cache

    C->>E: POST /auth/login (Host: tenant.app.com)
    E->>I: Forward request
    I->>TR: Resolve subdomain
    TR->>CP: Lookup Tenant Registry
    CP-->>TR: Tenant active
    TR-->>I: Tenant Context
    I->>IAM: Authenticate credentials
    IAM->>TD: Verify User Identity
    TD-->>IAM: Identity valid
    IAM->>IAM: Create Session + Tokens
    IAM->>R: Register session bridge
    IAM-->>I: Identity Context + tokens
    I-->>C: 200 + access/refresh
```

---

## 2. ERP Request (Shared o Dedicated — mismo diagrama L5)

```mermaid
sequenceDiagram
    participant C as Cliente
    participant I as Ingress Pipeline
    participant TR as Tenant Resolution
    participant SG as Security Gates
    participant APP as ERP Application
    participant PG as Persistence Gateway
    participant TD as Tenant Data Store

    C->>I: GET /api/v1/inv/productos (Bearer + Host)
    I->>TR: Tenant Context
    TR-->>I: tenant_id
    I->>SG: Validate JWT + RBAC + ERP session
    SG-->>I: Identity + Company + Authorization Context
    I->>APP: Invoke list products
    APP->>PG: Data operation (tenant scope)
    PG->>PG: Resolve Tenant Data Store route
    Note over PG: Shared or Dedicated — invisible to APP
    PG->>TD: Query with tenant + company filter
    TD-->>PG: Result rows
    PG-->>APP: Domain rows
    APP-->>I: Response DTO
    I-->>C: 200 JSON paginated
```

---

## 3. Dedicated Request (énfasis L6)

```mermaid
sequenceDiagram
    participant APP as ERP Application
    participant PG as Persistence Gateway
    participant CP as Control Plane Store
    participant TD as Dedicated Tenant Store

    APP->>PG: Data operation
    PG->>CP: Read Storage Metadata
    CP-->>PG: mode=dedicated, endpoint ref
    PG->>PG: Bind Persistence Context
    PG->>TD: Execute operation
    TD-->>PG: Result
    PG-->>APP: Result
```

**Nota:** L5 idéntico a Shared request.

---

## 4. Shared Request (énfasis L6)

```mermaid
sequenceDiagram
    participant APP as ERP Application
    participant PG as Persistence Gateway
    participant CP as Control Plane Store
    participant TD as Shared Tenant Store

    APP->>PG: Data operation
    PG->>CP: Read metadata (optional)
    CP-->>PG: mode=shared or absent
    PG->>PG: Bind Persistence Context + tenant filter
    PG->>TD: Execute with logical isolation
    TD-->>PG: Result
    PG-->>APP: Result
```

---

## 5. Onboarding

```mermaid
sequenceDiagram
    participant SA as Platform Operator
    participant I as Ingress Pipeline
    participant PLT as Platform Application
    participant PROV as Provisioning Orchestrator
    participant CP as Control Plane Store
    participant TD as Tenant Data Store
    participant IAM as IAM

    SA->>I: POST /clientes
    I->>PLT: Superadmin gate
    PLT->>PROV: Start onboarding saga
    PROV->>CP: Create Tenant Registry
    PROV->>CP: Assign Installation Mode
    alt Dedicated
        PROV->>TD: Prepare dedicated store
        PROV->>CP: Write Storage Metadata
    end
    PROV->>TD: Seed Company + Roles + Grants
    PROV->>IAM: Create admin Identity
    PROV->>CP: Mark Tenant Activo
    PROV-->>PLT: Success
    PLT-->>SA: 200 + credentials
```

---

## 6. Migration Shared to Dedicated

```mermaid
sequenceDiagram
    participant PLT as Platform Ops
    participant CP as Control Plane Store
    participant IAM as IAM
    participant SRC as Shared Tenant Store
    participant DST as Dedicated Tenant Store

    PLT->>CP: Set Tenant Migrando
    PLT->>IAM: Revoke all sessions
    PLT->>SRC: Export tenant data plane
    PLT->>DST: Import tenant data plane
    PLT->>CP: Update Storage Metadata
    PLT->>CP: Set mode Dedicated
    PLT->>CP: Set Tenant Activo
    Note over PLT: Invalidate engine cache
```

---

## 7. Impersonation

```mermaid
sequenceDiagram
    participant SA as Superadmin
    participant I as Ingress Pipeline
    participant IAM as IAM
    participant R as Cache
    participant CP as Control Plane Store
    participant TD as Target Tenant Store

    SA->>I: POST impersonate/{target_tenant}
    I->>IAM: Superadmin gate
    IAM->>CP: Validate target tenant
    IAM->>R: Store parent session
    IAM-->>SA: Impersonation access token (target tenant claims)
    SA->>I: ERP request (platform Host, impersonation token)
    I->>IAM: Validate overlay
    I->>TD: ERP via L6 target tenant route
    TD-->>SA: Target tenant data
    SA->>IAM: POST impersonate/end
    IAM->>R: Restore parent session
```

---

## 8. Background Job (session cleanup)

```mermaid
sequenceDiagram
    participant SCH as Scheduler
    participant JOB as Background Job
    participant IAM as IAM Layer
    participant CP as Control Plane Store

    SCH->>JOB: Trigger cleanup
    JOB->>JOB: Synthetic system context
    JOB->>CP: Query expired sessions policy
    loop Per batch
        JOB->>IAM: Revoke expired sessions
    end
    JOB-->>SCH: Complete
```

---

## 9. Refresh Token

```mermaid
sequenceDiagram
    participant C as Cliente
    participant I as Ingress Pipeline
    participant IAM as IAM Gate
    participant R as Cache
    participant SS as Session Store

    C->>I: POST /auth/refresh (refresh cookie)
    I->>IAM: Parse refresh token
    Note over IAM: tenant_id from token not Host
    IAM->>SS: Validate session + probe
    SS-->>IAM: Session active
    IAM->>IAM: Rotate refresh
    IAM->>R: Update session bridge
    IAM-->>C: New access + refresh
```

---

## 10. Health Check

```mermaid
sequenceDiagram
    participant P as Probe
    participant I as Ingress Pipeline
    participant PG as Persistence Gateway

    P->>I: GET /health
    I->>PG: Optional connectivity check
    PG-->>I: connected / error
    I-->>P: 200 or 503
```

---

## 11. Notas sobre diagramas

- Participantes son **roles arquitectónicos**, no componentes de código.
- "Persistence Gateway" = L6 abstracto.
- Dedicated vs Shared difiere solo en diagramas 3 y 4 (L6).
- Contradicciones AS-IS (per-op resolution) no alteran diagramas L5.

---

## 12. Conclusión

Los diagramas confirman: **mismo pipeline L0–L5** para Shared y Dedicated; bifurcación solo en **Persistence Gateway → Store**.
