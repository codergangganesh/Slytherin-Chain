# Future Work

> **What this covers:** Features and improvements deferred from the MVP.
> **Who should read it:** Anyone planning the next iteration of SentinelChain.

## Scale-Up Path

- **Kafka** — Replace Redis Streams for higher throughput and multi-consumer patterns
- **Kubernetes** — Container orchestration for production deployment
- **Elasticsearch** — Dedicated search cluster for event log analysis
- **Temporal** — Workflow orchestration for complex response playbooks

## Authentication & Authorization

- **Keycloak** — Enterprise SSO/OIDC integration
- **SAML** — Enterprise federation
- **API key rotation** — Automated key rotation with grace periods

## Detection Enhancements

- **ML-based anomaly detection** — Complement rule-based detection with statistical baselines
- **Wazuh adapter** — Full integration with Wazuh alert JSON format (STRETCH item)
- **Sigma rule compatibility** — Import Sigma detection rules

## Response Enhancements

- **Real Linux nftables enforcement** — Behind `ENABLE_REAL_ENFORCEMENT` flag (STRETCH item)
- **EDR agent integration** — CrowdStrike, SentinelOne, Carbon Black connectors
- **SOAR integration** — Bi-directional sync with Cortex XSOAR, Splunk SOAR

## Blockchain

- **Mainnet deployment** — Production anchoring on Ethereum L2 (Polygon, Arbitrum)
- **On-chain Merkle proof verification** — Solidity function for full proof verification (STRETCH)
- **STIX 2.1 export** — Structured threat intelligence exchange format (STRETCH)

## Reporting

- **Scheduled reports** — Automated daily/weekly summary reports
- **Custom report templates** — User-defined Jinja2 templates
- **Multi-language support** — Localized report generation

## Operations

- **Multi-tenancy** — Isolated tenant environments
- **Audit log export** — SIEM forwarding of platform audit logs
- **Backup and restore** — Automated database and evidence backup
