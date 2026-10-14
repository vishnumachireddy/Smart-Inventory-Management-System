# StockSense — Smart Inventory & Expiry Tracker for Small Retailers

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/Neon%20PostgreSQL-16+-336791?logo=postgresql&logoColor=white)](https://neon.tech)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Pytest](https://img.shields.io/badge/Pytest-8.2+-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org)

**StockSense** is an enterprise-grade, full-stack inventory management, batch expiry tracking, and demand forecasting web application tailored for small retailers (grocery stores, pharmacies, general merchants).
It solves retail stockouts, overstocking, and perishable expiry losses through batch-level tracking, deterministic **FEFO (First Expired, First Out)** allocation, machine learning velocity forecasting, and replenishment optimization.

---

## 1. Key Features

- **Batch-Level Inventory Tracking**: Maintain separate lot numbers, intake dates, unit costs, and expiration dates per product.
- **Deterministic FEFO Engine**: Automatically exhausts earliest-expiring eligible stock first during sales fulfillment; bars expired stock from sale.
- **Machine Learning Demand Forecasting**: Transparent Moving Average baseline (7-day/14-day) paired with an advanced Random Forest regressor with lag features and time-ordered train/test validation reported via MAE and RMSE.
- **Replenishment Reorder Engine**: Data-backed safety stocks, lead-time demand calculations, and urgency prioritization.
- **POS Register Terminal**: Quick product search, barcode input, cart adjustments, configurable discounts, and printable customer receipts.
- **Real-Time Alert Reconciliation**: Dynamic low-stock, near-expiry (30-day warning window), and expired stock alerts with automatic resolution.
- **Audit Ledger**: Immutable stock movement ledger tracking all receipts, sales, customer returns, and adjustments.
- **Role-Based Access Control (RBAC)**: Distinct permissions for Shop Owner (administrative, purchasing, staff provisioning) and Staff (POS cashier, stock view).
- **Executive Dashboard**: 8 primary real-time KPI cards, continuous revenue and gross profit curves, category valuation distribution, and top velocity products.

---

## 2. Mandatory Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** with Pydantic v2 validation
- **SQLAlchemy 2.x** ORM
- **Alembic** versioned schema migrations
- **Neon Serverless PostgreSQL** via `psycopg` (psycopg 3)
- **Scikit-Learn, Pandas & NumPy** for demand forecasting
- **JWT & Bcrypt** for secure authentication and password hashing

### Frontend
- **React 19** with **Vite**
- **TypeScript**
- **Tailwind CSS**
- **React Router v6**
- **Recharts** for analytics and forecast charts
- **Lucide React** for icons
- **Axios** centralized HTTP client with interceptors

---

## 3. Architecture & Database Design

StockSense enforces strict layered separation:
- `backend/app/api/v1/`: Versioned REST API routers.
- `backend/app/services/`: Core domain business logic (FEFO allocation, sales POS, alerts, reorder engine).
- `backend/app/forecasting/`: Demand forecasting pipelines (Moving Average + Random Forest).
- `backend/app/models/`: Normalized SQLAlchemy models with indexes, foreign keys, and cascading rules.
- `frontend/src/pages/`: 18 production-ready application screens.

For detailed architecture diagrams and schema specifications:
- [Architecture Specification](docs/architecture.md)
- [Database Schema & ERD](docs/database-schema.md)
- [REST API Endpoint Guide](docs/api-guide.md)
- [Testing & Quality Assurance Guide](docs/testing.md)

---

## 4. Neon PostgreSQL Setup & Environment Configuration

StockSense uses **Neon Serverless PostgreSQL** as its primary persistence engine.

### 4.1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure your **Neon PostgreSQL Connection String** from your [Neon Dashboard](https://console.neon.tech):
```env
# Neon Serverless PostgreSQL connection string (psycopg 3 driver)
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@ep-xyz-123456.us-east-2.aws.neon.tech/neondb?sslmode=require

# Application Secret
SECRET_KEY=stocksense-production-secret-key-replace-with-random-32-bytes
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Default Business Parameters
DEFAULT_NEAR_EXPIRY_DAYS=30
DEFAULT_LEAD_TIME_DAYS=7
DEFAULT_SAFETY_STOCK_FACTOR=1.5
CURRENCY_CODE=INR
CURRENCY_SYMBOL=₹
```

> **Note**: In offline development or unit testing, StockSense also supports local SQLite databases (`DATABASE_URL=sqlite:///./stocksense_dev.db`).

---

## 5. Quickstart & Local Installation

### Step 1: Install Backend Dependencies
```bash
# From project root
python -m pip install -r backend/requirements.txt
```

### Step 2: Initialize Database & Run Migrations
Run Alembic migrations to apply all PostgreSQL tables:
```bash
python -m alembic upgrade head
```

### Step 3: Seed Synthetic Demonstration Dataset
Populate 34 catalog products across 7 retail categories, multi-batch FEFO history, 60 days of sales transactions, and alerts:
```bash
python scripts/seed_demo_data.py
```

### Step 4: Start FastAPI Backend Server
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
The interactive OpenAPI Swagger documentation is available at: **http://127.0.0.1:8000/docs**

### Step 5: Install and Start React Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: **http://localhost:5173**

---

## 6. Pre-Configured Demo Credentials

The demo seed script (`scripts/seed_demo_data.py`) provides two pre-configured accounts:

| Role | Email Address | Password | Permissions |
|---|---|---|---|
| **Shop Owner** | `owner@stocksense.com` | `Owner@123` | Full administrative control, settings, user management, and purchase receipts |
| **Staff Member** | `staff@stocksense.com` | `Staff@123` | POS cashiering, catalog view, batch inventory, and alerts |

*(Convenient one-click login buttons for both accounts are also provided directly on the Login screen).*

---

## 7. Automated Testing Suite

### Running Backend Tests (`pytest`)
All 13 automated business logic tests (authentication, FEFO batch allocation, multi-batch sales, expired stock rejection, transaction rollbacks, alerts, and moving-average forecasting) can be executed via:
```bash
python -m pytest backend/tests -v
```

### Running Frontend Tests (`vitest`)
```bash
cd frontend
npm test
```

### Running Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 8. Business Logic & FEFO Principles

1. **FEFO Prioritization**: Batches with the earliest expiration date are consumed first.
2. **Expired Stock Safety**: Batches where `expiry_date < current_date` are automatically barred from POS sales to protect consumers and prevent inventory shrinkage.
3. **Auditable Reversals**: Sales cannot be rewritten; voiding a sale creates reverse `customer_return` stock movements and atomically restores quantities back into the original batches.
4. **Demand Velocity**: Missing sales records during available in-stock days are treated as genuine 0.0 sales rather than dropped.

---

## 9. License & Deployment
Built for small retailers and demonstrative retail inventory management. Designed for deployment on Vercel/Netlify (Frontend) and Render/Railway/Fly.io (Backend FastAPI) connected to Neon Serverless PostgreSQL.
