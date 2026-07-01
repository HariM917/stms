# Smart Traffic Management System (STMS)

> AI-powered traffic management API for Indian road conditions — built with FastAPI, SQLAlchemy, and YOLOv8.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

STMS is a production-ready backend API that uses computer vision, machine learning, and rule-based AI to analyze traffic conditions in real-time. Designed specifically for Indian road scenarios.

### Key Features

| Feature | Description |
|---|---|
| 🚗 **Object Detection** | Vehicles, pedestrians, animals via YOLOv8 |
| 🕳️ **Pothole Detection** | Road surface condition analysis |
| 🪧 **Traffic Sign Recognition** | Indian traffic signs and speed limits |
| 🌦️ **Weather Analysis** | Visibility and road safety assessment |
| 🚂 **Railway Crossing** | Train detection and crossing status |
| 🚦 **Signal Optimization** | RL-based traffic signal timing |
| 🤖 **AI Insights** | LLM-powered traffic recommendations |
| 🔐 **JWT Authentication** | Secure login with role-based access |
| 📊 **Traffic Reports** | CRUD with pagination and filtering |

---

## Architecture

```
stms-backend/
├── backend/
│   ├── app/                    # FastAPI application
│   │   ├── main.py             # App factory & lifespan
│   │   ├── config.py           # Pydantic settings
│   │   ├── database.py         # Async SQLAlchemy engine
│   │   ├── middleware/         # Request ID, rate limiting, auth, errors
│   │   ├── models/             # Pydantic + SQLAlchemy models
│   │   │   ├── auth.py         # Request/response schemas
│   │   │   ├── detection.py    # Detection schemas
│   │   │   └── db/             # ORM models (User, Session, Report)
│   │   ├── repositories/      # Data access layer (async CRUD)
│   │   ├── routers/           # API route handlers
│   │   │   ├── auth.py        # Auth (register, login, profile)
│   │   │   ├── detection.py   # 5 detection endpoints
│   │   │   ├── reports.py     # Traffic report CRUD
│   │   │   ├── optimization.py
│   │   │   ├── insights.py
│   │   │   └── health.py      # Health + readiness probes
│   │   ├── services/          # Business logic
│   │   │   ├── auth_service.py     # JWT + bcrypt
│   │   │   ├── detector_service.py # ML model management
│   │   │   └── image_service.py    # Image I/O
│   │   └── utils/             # Logging, numpy conversion
│   ├── detectors/             # ML detector modules
│   ├── optimization/          # Traffic signal optimizer
│   ├── llm/                   # LLM insights engine
│   ├── ai_models/             # Trained model weights
│   ├── tests/                 # pytest test suite
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                  # Web UI (HTML/CSS/JS)
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and configure
git clone https://github.com/dillikumar2007/stms-backend.git
cd stms-backend
cp .env.example .env  # Edit with your settings

# Start everything (API + PostgreSQL)
docker-compose up --build

# API available at http://localhost:8001
# Docs at http://localhost:8001/api/docs
```

### Option 2: Local Development

```bash
# 1. Setup Python environment
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure environment
cp ../.env.example .env
# Edit .env — set DB_DRIVER=sqlite for local dev (no PostgreSQL needed)

# 4. Run the server
python -m app.main --reload

# API: http://localhost:8001
# Docs: http://localhost:8001/api/docs
```

---

## API Reference

All endpoints are documented at **`/api/docs`** (Swagger UI) and **`/api/redoc`** (ReDoc).

### Base URLs

| Version | Prefix | Status |
|---|---|---|
| v1 (current) | `/api/v1/` | ✅ Active |
| Legacy | `/api/` | ⚠️ Backward-compatible, not in docs |

### Key Endpoints

```
# Health
GET  /api/health              # System status
GET  /api/health/ready         # Kubernetes readiness probe

# Authentication
POST /api/v1/auth/register     # Create account
POST /api/v1/auth/login        # Get JWT token
POST /api/v1/auth/logout       # End session
GET  /api/v1/auth/profile      # Get profile (auth required)
PUT  /api/v1/auth/profile      # Update profile
PUT  /api/v1/auth/change-password
DELETE /api/v1/auth/account     # Delete account

# Detection (all accept multipart file upload)
POST /api/v1/detect/objects         # Vehicles, pedestrians
POST /api/v1/detect/traffic-signs   # Indian traffic signs
POST /api/v1/detect/potholes        # Road damage
POST /api/v1/detect/weather         # Weather conditions
POST /api/v1/detect/railway-crossing # Railway crossings

# Traffic Reports (auth required)
POST /api/v1/reports           # Create report
GET  /api/v1/reports           # List (paginated)
GET  /api/v1/reports/recent    # Recent reports

# Optimization
POST /api/v1/optimize/signals  # Optimize signal timings

# AI Insights
POST /api/v1/generate/insights # Generate traffic insights
```

### Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

Get a token by calling `POST /api/v1/auth/login`.

**Default demo account:** `demo@example.com` / `demo123`

---

## Development

### Running Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Specific test file
pytest tests/test_auth.py -v
```

### Code Quality

```bash
# Lint with ruff
ruff check app/ tests/

# Format with ruff
ruff format app/ tests/

# Type checking
mypy app/
```

### Database

- **Local dev**: Uses SQLite by default (`DB_DRIVER=sqlite`). Zero setup required.
- **Production**: Uses PostgreSQL via asyncpg (`DB_DRIVER=postgresql`).
- Tables are auto-created on first startup. For production, use Alembic migrations.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DB_DRIVER` | `sqlite` | `sqlite` or `postgresql` |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | | PostgreSQL password |
| `DB_DATABASE` | `stms_db` | Database name |
| `JWT_SECRET` | `change-me...` | **Must change in production** |
| `API_PORT` | `8001` | Server port |
| `CORS_ORIGIN` | `http://localhost:5000` | Comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per window |
| `RATE_LIMIT_WINDOW` | `900` | Rate limit window in seconds |

---

## License

MIT