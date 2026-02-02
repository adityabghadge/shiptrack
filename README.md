# ShipTrack 
**Uptime Monitoring & Incident Alerting Backend (FastAPI, Postgres, Docker)**

ShipTrack is a production-style backend system for monitoring HTTP endpoints, tracking uptime and latency, and managing **stateful incidents** with **Slack alerts** on meaningful transitions (OPEN → RESOLVED).  

It is designed to demonstrate real-world backend reliability patterns.

---

## What ShipTrack Does

- Runs HTTP health checks against registered endpoints
- Tracks latency, status codes, and failures
- Opens incidents after **consecutive failures**
- Resolves incidents after **consecutive recoveries**
- Sends Slack alerts **only on incident state changes** (no alert spam)
- Provides uptime and latency summaries over a rolling window
- Fully Dockerized for reproducible local execution

---

## Key Features

- HTTP uptime checks with latency measurement
- Deterministic incident detection (failure & recovery thresholds)
- Incident lifecycle management: **OPEN → RESOLVED**
- Slack alerting with deduplication
- REST API built with FastAPI
- Persistent storage with PostgreSQL
- End-to-end and unit test coverage
- Docker Compose setup for one-command startup

---

## Architecture Overview

```
Client / CLI
     |
     v
 FastAPI API
     |
     v
 PostgreSQL  <---- Incident Logic
     |
     v
 Check Executor
     |
     v
 Slack Incoming Webhook
```

---

## Screenshots

### Swagger API Documentation
![Swagger UI](docs/images/swagger.png)

### Slack Incident Alert
![Slack Alert](docs/images/slack.png)

### 100-Check Uptime & Latency Summary
![100 Checks Summary](docs/images/tests.png)

---

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **HTTP Client:** httpx
- **Containerization:** Docker, Docker Compose
- **Testing:** pytest
- **Alerts:** Slack Incoming Webhooks

---

## Project Structure

```
shiptrack/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── worker/
├── scripts/
├── tests/
├── docs/
│   └── images/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Environment Variables

Create a `.env` file in the project root (do **not** commit it):

```
API_KEY=change-me-super-secret
DATABASE_URL=postgresql+psycopg://shiptrack:shiptrack@postgres:5432/shiptrack

SLACK_ALERTS_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

---

## Running the Project

```
docker compose up -d --build
```

API Docs: http://localhost:8000/docs

---

## Testing

Run end-to-end test:

```
bash scripts/e2e.sh
```

Run unit tests:

```
docker compose exec api pytest
```

---

## Example Results

- 100 consecutive on-demand checks
- **100% uptime**
- Average latency ≈ **337 ms**
- Median latency ≈ **216 ms**
- Incident OPEN/RESOLVE lifecycle verified
- Slack alerts delivered successfully

---

## Purpose

ShipTrack demonstrates backend system design, reliability modeling, and production-grade engineering practices.

**Author:** Aditya Ghadge  
**Category:** Backend Engineering / Reliability Systems
