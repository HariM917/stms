# Changelog

All notable changes to the STMS Backend are documented here.

## [2.0.0] — 2026-05-23

### 🏗️ Architecture Overhaul

- **Consolidated auth**: Merged Node.js `auth-server.js` into FastAPI Python backend. Single server, single language.
- **Database layer**: Added async SQLAlchemy 2.0 with asyncpg (PostgreSQL) and aiosqlite (SQLite for dev).
- **Repository pattern**: Clean data access layer (`app/repositories/`) separating DB queries from route handlers.
- **Application factory**: `create_app()` pattern in `app/main.py` for testability.

### 🔐 Security

- **JWT authentication**: Real JWT tokens via `python-jose` replacing random UUIDs.
- **bcrypt password hashing**: All passwords hashed with bcrypt (was already done, now consolidated).
- **Rate limiting**: Sliding-window rate limiter on auth endpoints (configurable).
- **Security headers**: X-Content-Type-Options, X-Frame-Options, HSTS (production), etc.
- **Request ID tracing**: Every request gets a unique `X-Request-ID` for debugging.

### 📡 API Improvements

- **Versioned API**: All routes under `/api/v1/` with backward-compatible `/api/` aliases.
- **Standardized naming**: Kebab-case routes (`/traffic-signs`, `/railway-crossing`).
- **Traffic reports**: Full CRUD with pagination, role-based filtering (ported from Node.js).
- **Enhanced health**: Database connectivity check, memory usage, Kubernetes readiness probe.
- **Real optimizer**: Signal optimization endpoint now uses `TrafficSignalOptimizer` when available.
- **Structured errors**: Consistent `{success, message, request_id}` error responses.

### 🧪 Testing

- **pytest suite**: 30+ tests covering health, auth, detection, reports, and optimization.
- **Async test client**: httpx + ASGITransport with in-memory SQLite.
- **Fixtures**: Auth helpers, DB session override, registered user fixture.

### 🐳 Deployment

- **Dockerfile**: Multi-stage build, non-root user, health check.
- **docker-compose.yml**: API + PostgreSQL + volume mounts.
- **pyproject.toml**: Modern Python packaging replacing `requirements.txt`.

### 🗑️ Deprecated

- `run_stms_server.py` → `app/main.py`
- `auth-server.js` → `app/routers/auth.py`
- `api/` directory → `app/routers/`
- `schema.sql` → SQLAlchemy ORM models + auto-creation
- All Node.js dependencies → Python only

### 📝 Documentation

- Complete README rewrite with architecture, quick start, API reference.
- Inline docstrings on all modules, classes, and functions.
