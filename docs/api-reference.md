# API Reference

> **What this covers:** Summary of all REST API endpoints. The OpenAPI spec at `/docs` is the source of truth.
> **Who should read it:** Developers integrating with the SentinelChain API.

*Full endpoint documentation will be added as endpoints are implemented.*

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

- User authentication: JWT Bearer tokens via `POST /api/v1/auth/login`
- Event ingestion: API key via `X-API-Key` header

## Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe — returns OK if the process is running |
| `/ready` | GET | Readiness probe — checks all dependency connectivity |
