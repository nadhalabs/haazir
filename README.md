# Haazir — On-Demand Local Services Marketplace Backend

Production-grade modular monolith backend foundation for **Haazir**, an on-demand local services marketplace connecting customers with verified local service professionals.

## V1 Service Scope
- **Plumbing** (pipe leak fixing, drain unblocking, tap/shower repair)
- **Electrical** (switchboards, fans, MCB tripping & inspection)
- **AC & Appliance Technicians** (AC servicing, refrigerator, washing machine)
- **Mechanics & Roadside Assist** (battery jumpstart, tyre puncture)
- **Locksmiths** (emergency lockouts, lock installation)
- **Carpenters** (hinge alignment, furniture assembly)
- **Cleaners** (bathroom deep clean, kitchen degreasing & sanitation)

---

## Architectural Highlights
- **Architecture**: Modular monolith with decoupled domains (`auth`, `users`, `providers`, `services`, `pricing`, `bookings`, `dispatch`, `payments`, `ratings`, `support`, `admin`, `ws`).
- **State Machine**: Explicit, validated booking lifecycle (`REQUESTED` ➔ `SEARCHING` ➔ `ASSIGNED` ➔ `PROVIDER_EN_ROUTE` ➔ `ARRIVED` ➔ `IN_PROGRESS` ➔ `COMPLETED` / `CANCELLED` / `FAILED`).
- **Server-Authoritative Pricing**: Customers request immutable, time-bounded `PriceQuote`s computed on the server. Clients cannot specify or tamper with amounts. Quotes, addresses, and provider states are immutably snapshotted at booking time.
- **Live Location & Ephemeral Presence**:
  - Redis GEO set (`haazir:geo:providers`) and Hash (`haazir:provider:presence:{provider_id}`) with 300s TTL.
  - Heartbeat endpoint: `POST /api/v1/providers/me/location`.
  - Zero high-frequency GPS ping writes to PostgreSQL. Stale providers automatically disappear from dispatch upon TTL expiry.
- **Dispatch Discovery & Matching**:
  - Server-side nearby matching for bookings in `SEARCHING`.
  - Enforces 8 strict validation gates: Verified + Active + Non-suspended + Service offered + Live Redis presence + Available + Within service radius + Sorted nearest first with approximate ETA.
- **PostgreSQL Concurrency Protection**:
  - Authoritative row locking: `SELECT ... FOR UPDATE` on `bookings` table.
  - Database-enforced partial unique constraint: `CREATE UNIQUE INDEX uq_booking_single_accepted_assignment ON booking_assignments (booking_id) WHERE (status = 'ACCEPTED')`.
  - Guarantees two providers can never simultaneously claim the same booking; losing provider receives `409 Conflict`.
- **Payment Abstraction & Financial Idempotency**: Pluggable `PaymentAdapter` pattern with `CashPaymentAdapter` and `GatewayStubAdapter`. Duplicate completion and earning ledger prevention.
- **Realtime WebSockets & REST Fallback**: Channel-based WebSocket manager (`/api/v1/ws/bookings/{id}`, `/api/v1/ws/providers/{id}`). REST remains the authoritative source of truth.

---

## Developer Quickstart

### 1. Prerequisites
- Python 3.12+
- PostgreSQL 15/16 + PostGIS
- Redis 7+

### 2. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment file
cp backend/.env.example backend/.env
```

### 3. Database Migration & Seeding
```bash
cd backend

# Run database migrations
alembic upgrade head

# Seed initial V1 categories, services, and default admin
python -m app.seed
```

### 4. Running Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/api/v1/docs`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`
- Health check: `http://localhost:8000/health`

### 5. Running Automated Test Suite
```bash
cd backend
# Runs both SQLite unit tests AND real PostgreSQL concurrency tests
PYTHONPATH=. pytest -v
```

### 6. Running with Docker Compose
```bash
cd backend
docker compose up --build
```
