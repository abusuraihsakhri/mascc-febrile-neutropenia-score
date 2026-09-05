# MASCC Febrile Neutropenia Score

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

The MASCC Febrile Neutropenia Risk Index identifies low-risk febrile neutropenic cancer patients who may be suitable for outpatient oral antibiotics. This implementation provides:

- **Single case evaluation** via CLI or API
- **Batch processing** of CSV patient records
- **Multi-agent consensus** with specialized workers (QC, Safety, Protocol Conformance)
- **Zero-PHI outbound guard** preventing protected health information leakage
- **Tamper-evident HMAC-SHA256 audit trail** for all evaluations
- **FastAPI REST API** with Prometheus metrics endpoint

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/mascc-febrile-neutropenia-score.git
cd mascc-febrile-neutropenia-score

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Requirements

- Python 3.10+
- pydantic >= 2.0
- fastapi >= 0.110
- uvicorn >= 0.27

---

## Usage

### Command Line Interface

#### Single Case Evaluation
```bash
python mascc_score.py single --v1 14.5 --v2 4.2 --v3 1.8
```

#### Batch CSV Processing
```bash
python mascc_score.py batch -i sample.csv -o results.csv
```

#### Enterprise CLI (with audit trail)
```bash
# Run single task evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process with audit trail
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Interactive chat query
python cli.py chat "Explain the scoring methodology"
```

### REST API Server
```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

API Endpoints:
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /api/audit` - Submit task for evaluation
- `POST /api/chat` - Query the supervisory chat
- `GET /api/audit/logs` - Retrieve audit trail

---

## Input Data Schema

### CSV Batch Format

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Unique patient identifier | Required |
| `v1` | Primary measurement parameter | Required |
| `v2` | Secondary measurement parameter | Required |
| `v3` | Tertiary measurement parameter | Required |

### Scoring Algorithm

The MASCC score is computed as a weighted sum of input parameters:

```
score = v1 + v2/2 + v3/3 + ...
```

Results are classified into risk tiers:
- **Low / Standard** (score < 10): Standard monitoring
- **Moderate / Intermediate** (10 <= score < 25): Close observation
- **High / Severe** (score >= 25): Urgent clinical intervention

---

## Security Features

### Zero-PHI Outbound Guard
Active pattern matching blocks outbound data containing:
- Medical Record Numbers (MRN)
- Social Security Numbers
- Phone numbers
- Email addresses
- Patient names and DOB

### HMAC-SHA256 Audit Trail
- Cryptographically chained log entries
- Tamper-evident verification
- Each entry signed with SHA-256 HMAC

**Important:** Set the `AUDIT_SECRET_KEY` environment variable in production to ensure audit trail persistence across restarts. Without it, a random session key is generated.

```bash
export AUDIT_SECRET_KEY="your-secure-key-here"
```

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=.

# Run specific test files
pytest test_mascc_score.py -v
pytest tests/ -v
```

### Simulation Benchmark
```bash
python simulator.py 1000
```

---

## Docker Deployment

```bash
docker build -t mascc-febrile-neutropenia-score .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-key" mascc-febrile-neutropenia-score
```

---

## Project Structure

```
mascc-febrile-neutropenia-score/
├── agents/                  # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py              # FastAPI REST server
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── learning.py         # Bayesian calibration engine
│   ├── llm_factory.py      # LLM provider factory
│   ├── metrics.py          # Prometheus metrics collector
│   ├── models.py           # Pydantic data models
│   ├── streamer.py         # WebSocket telemetry streamer
│   ├── supervisor.py       # Multi-agent orchestrator
│   └── workers.py          # Specialized domain workers
├── tests/                  # Test suite
│   ├── test_enrichment.py
│   └── test_mascc_febrile_neutropenia_score.py
├── test_mascc_score.py     # Core scoring tests
├── cli.py                  # Enterprise CLI entry point
├── mascc_score.py          # Core scoring algorithm
├── enrichment.py           # Enrichment feature modules
├── simulator.py            # High-throughput simulation
├── sample.csv              # Sample patient data
├── pyproject.toml          # Project metadata and dependencies
├── Dockerfile              # Container build config
└── docker-compose.yml      # Multi-service orchestration
```
