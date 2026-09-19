# Architecture

> **What this covers:** System architecture, component responsibilities, and data flow.
> **Who should read it:** Developers, reviewers, and anyone evaluating the platform design.

## System Architecture

```mermaid
graph TB
    subgraph "Event Sources"
        SIM[Attack Simulator]
        EXT[External Logs / Wazuh]
    end

    subgraph "Ingestion Layer"
        API[FastAPI - POST /api/v1/events]
        NORM[Event Normalizer]
        STREAM[Redis Stream: events.normalized]
    end

    subgraph "Processing Pipeline"
        DET[Detection Engine + YAML Rules]
        ENR[Enrichment: Threat Intel + Assets]
        RISK[Risk Scoring + Correlation]
        INC[Incident Lifecycle Manager]
    end

    subgraph "Response Engine"
        PLAY[Playbook Policy Engine]
        GUARD[Guardrail Checker - 11 checks]
        CONN[Enforcement Connectors]
        APPROVE[Human Approval Queue]
    end

    subgraph "Integrity Layer"
        LEDGER[Hash Chain Audit Ledger]
        MERKLE[Merkle Tree Batcher]
        CONTRACT[IntegrityAnchor Contract]
        CHAIN[Anvil / Sepolia Blockchain]
    end

    subgraph "Storage"
        PG[(PostgreSQL)]
        RD[(Redis)]
        MINIO[(MinIO)]
    end

    subgraph "Presentation"
        DASH[React Dashboard]
        REPORTS[PDF / MD / JSON Reports]
    end

    SIM --> API
    EXT --> API
    API --> NORM --> STREAM
    STREAM --> DET --> ENR --> RISK --> INC
    INC --> PLAY --> GUARD
    GUARD -->|Pass| CONN
    GUARD -->|Needs Approval| APPROVE
    INC --> LEDGER --> MERKLE --> CONTRACT --> CHAIN
    DASH --> API
```

## Component Responsibilities

*Detailed component descriptions will be added as each phase is implemented.*

## Data Flow

1. **Events** arrive via HTTP → normalized → published to Redis Stream
2. **Detection worker** consumes events → evaluates rules → creates alerts
3. **Enrichment** adds threat intel + asset context → risk scoring
4. **Correlation** groups alerts into incidents → state machine manages lifecycle
5. **Response engine** matches playbooks → guardrails check → execute or queue approval
6. **Audit ledger** records every decision → Merkle batching → on-chain anchoring
7. **Dashboard** displays real-time state → reports generated on demand
