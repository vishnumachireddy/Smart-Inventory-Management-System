# StockSense — Smart Inventory & Expiry Tracker for Small Retailers

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/Neon%20PostgreSQL-16+-336791?logo=postgresql&logoColor=white)](https://neon.tech)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Pytest](https://img.shields.io/badge/Pytest-8.2+-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org)

**StockSense** is an enterprise-grade, full-stack inventory management, batch expiry tracking, and demand forecasting platform engineered for small retailers, grocery stores, pharmacies, and general merchants.

It prevents retail stockouts, eliminates perishable expiry losses, and optimizes replenishment using **batch-level tracking**, deterministic **FEFO (First Expired, First Out)** allocation, **machine learning velocity forecasting**, full-duplex **WebSockets**, and automated **daily scheduled audits with email notifications**, all backed by **Neon Serverless PostgreSQL**.

---

## Table of Contents
1. [Key Features](#1-key-features)
2. [Technology Stack](#2-technology-stack)
3. [Architecture & System Design](#3-architecture--system-design)
4. [Step-by-Step Installation & Quickstart](#4-step-by-step-installation--quickstart)
5. [Pre-Configured Demo Credentials](#5-pre-configured-demo-credentials)
6. [Complete Step-by-Step User & Feature Guide](#6-complete-step-by-step-user--feature-guide)
   - [Step 1: Public Showcase & Landing Page (`/home`)](#step-1-public-showcase--landing-page-home)
   - [Step 2: Authentication & Role-Based Access Control (`/login`)](#step-2-authentication--role-based-access-control-login)
   - [Step 3: Smart Login-Time Inventory Alert Dialog](#step-3-smart-login-time-inventory-alert-dialog)
   - [Step 4: Executive Real-Time Dashboard (`/`)](#step-4-executive-real-time-dashboard-)
   - [Step 5: Products Catalog & Dynamic Stock (`/products`)](#step-5-products-catalog--dynamic-stock-products)
   - [Step 6: Batch-Level Inventory & Expiry Tracking (`/batches`)](#step-6-batch-level-inventory--expiry-tracking-batches)
   - [Step 7: Perishable Expiry Tracker (`/expiry`)](#step-7-perishable-expiry-tracker-expiry)
   - [Step 8: Point-of-Sale (POS) Register Terminal (`/pos`)](#step-8-point-of-sale-pos-register-terminal-pos)
   - [Step 9: Sales History & Auditable Refunds (`/sales`)](#step-9-sales-history--auditable-refunds-sales)
   - [Step 10: Stock Movement Audit Ledger (`/movements`)](#step-10-stock-movement-audit-ledger-movements)
   - [Step 11: Purchase Receipts & Supplier Intake (`/purchases`)](#step-11-purchase-receipts--supplier-intake-purchases)
   - [Step 12: Supplier Directory & Lead Time Config (`/suppliers`)](#step-12-supplier-directory--lead-time-config-suppliers)
   - [Step 13: Machine Learning Demand Forecasting (`/forecasts`)](#step-13-machine-learning-demand-forecasting-forecasts)
   - [Step 14: Replenishment & Reorder Recommendations (`/recommendations`)](#step-14-replenishment--reorder-recommendations-recommendations)
   - [Step 15: Dedicated Alerts Screen & Resolution (`/alerts`)](#step-15-dedicated-alerts-screen--resolution-alerts)
   - [Step 16: Financial Analytics & CSV Exports (`/analytics`)](#step-16-financial-analytics--csv-exports-analytics)
   - [Step 17: Staff User Management (`/users`)](#step-17-staff-user-management-users)
   - [Step 18: Notification & Scheduling Settings (`/settings`)](#step-18-notification--scheduling-settings-settings)
7. [How It Works: Core Business Rules & Mechanics](#7-how-it-works-core-business-rules--mechanics)
   - [Deterministic FEFO Engine](#deterministic-fefo-engine)
   - [Real-Time WebSocket Streaming & Caching](#real-time-websocket-streaming--caching)
   - [Daily Automated Inventory Audit & Email Engine](#daily-automated-inventory-audit--email-engine)
   - [Neon Serverless PostgreSQL Resilience](#neon-serverless-postgresql-resilience)
8. [Daily Audit & Notification CLI](#8-daily-audit--notification-cli)
9. [Automated Verification & Testing](#9-automated-verification--testing)
10. [Troubleshooting & FAQ](#10-troubleshooting--faq)

---

## 1. Key Features

- **Public Showcase / Landing Page (`/home`)**: Interactive showcase presenting system capabilities, high-level architecture, live connection indicators, and one-click authentication shortcuts.
- **Smart Login-Time Inventory Alert Dialog**: Modal dialog automatically presented upon initial login session with three segregated tabs: *Products Nearing Expiry* (&le;7 days configurable), *Very Low-Stock Products*, and *Out-of-Stock Products* with urgency severity badges, recommended mitigation actions, and direct inventory navigation.
- **Real-Time WebSocket Telemetry (`/api/v1/ws`)**: Full-duplex WebSocket stream delivering instant KPI metrics and live inventory broadcasts directly to the browser upon connection, eliminating polling overhead.
- **Sub-Millisecond In-Memory Cache (`FastInMemoryCache`)**: Thread-safe in-memory cache with selective invalidation shielding Neon PostgreSQL from repetitive queries and accelerating warm API reads to &le;1ms.
- **Single-Roundtrip Bundled Dashboard API (`/api/v1/dashboard/bundle`)**: High-performance endpoint consolidating KPI metrics, 30-day sales curves, category distributions, velocity leaders, and expiry risk vectors into a single network payload.
- **Deterministic FEFO Engine (First Expired, First Out)**: Automatically exhausts earliest-expiring eligible batches first during checkout; strictly prevents sale of expired stock.
- **Batch-Level Inventory Tracking**: Tracks lot numbers, received dates, per-batch unit costs, and expiration dates.
- **Dual-Tier Machine Learning Forecasting**: Transparent 7/14-day Moving Average baseline paired with a Scikit-Learn Random Forest Regressor using lag features, day-of-week seasonality, and train/test evaluation (MAE and RMSE).
- **Replenishment Reorder Engine**: Data-backed safety stocks, lead-time demand calculations, and urgency prioritization (Critical, Moderate, Healthy).
- **POS Register Terminal**: Instant SKU and barcode search, real-time cart pricing, configurable order discounts, multi-batch FEFO deduction, and printable customer receipts.
- **Automated Daily Inventory Check**: Scheduled background service running daily at 08:00 (Asia/Kolkata timezone) that reconciles alert state, generates dated snapshots (`DailyInventorySnapshot`), logs job execution status (`ScheduledJobRun`), and dispatches multi-section HTML emails.
- **Email Notification Service**: Responsive multi-section HTML emails + plain-text fallbacks, SMTP with STARTTLS, retry backoff, idempotency deduplication keys (`{report_type}:{date}:{recipient}`), and complete audit logging (`EmailDeliveryLog`).
- **Audit Ledger**: Immutable stock movement ledger recording all receipts, sales, customer returns, and adjustments.
- **Role-Based Access Control (RBAC)**: Distinct permissions for Shop Owner (administrative, purchasing, staff provisioning, notification settings) and Staff (POS cashier, stock view).

---

## 2. Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (Asynchronous REST API + WebSockets)
- **Validation**: Pydantic v2
- **ORM**: SQLAlchemy 2.x
- **Database Driver**: `psycopg` (psycopg 3 driver with TCP keepalives and serverless pool recycling)
- **Database Migrations**: Alembic
- **Machine Learning & Analytics**: Pandas, NumPy, Scikit-Learn
- **Security & Authentication**: JWT (JSON Web Tokens) & Passlib with Bcrypt

### Frontend
- **Framework**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **Charts & Visualizations**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios with centralized request/response interceptors

### Database
- **Primary Engine**: Neon Serverless PostgreSQL 16 (AWS `us-east-2`)
- **Connection Mode**: Pooled (`ep-*-pooler.c-6.us-east-2.aws.neon.tech`) with SQLAlchemy `pool_recycle=60` and `pool_pre_ping=True`

---

## 3. Architecture & System Design

```mermaid
flowchart TD
    subgraph Browser ["Client Web Browser (React 19 + TypeScript + Vite)"]
        UI["18 Application Screens\n(Dashboard, POS, Batches, Alerts, Forecasts, Settings)"]
        WSClient["WebSocketContext (Ping Keepalive, Event Dispatch)"]
        AxiosClient["Axios API Client (JWT Bearer, Auto Timezone)"]
        UI --> WSClient
        UI --> AxiosClient
    end

    subgraph BackendApp ["FastAPI Application Backend (Python 3.11)"]
        WSHandler["WebSocket Router (/api/v1/ws)"]
        APIRouters["REST API Routers (/api/v1/*)"]
        AuthGuard["JWT Security & Role-Based Access Control (RBAC)"]
        MemCache["FastInMemoryCache (TTL Store, Selective Invalidation)"]
        
        subgraph DomainServices ["Domain Services"]
            FEFO["FEFO Inventory Engine"]
            AlertService["InventoryAlertService (Reconciliation & Snapshots)"]
            Scheduler["DailySchedulerService (08:00 Asia/Kolkata)"]
            EmailService["EmailNotificationService (SMTP STARTTLS)"]
            MLForecast["ForecastingPipeline (Moving Avg + Random Forest)"]
            ReorderEngine["RecommendationService (Lead-Time Safety Stock)"]
        end
        
        APIRouters --> AuthGuard
        AuthGuard --> DomainServices
        WSHandler --> MemCache
        DomainServices --> MemCache
        Scheduler --> AlertService
        Scheduler --> EmailService
    end

    subgraph DatabaseLayer ["Persistence Layer"]
        SQLA["SQLAlchemy 2.0 ORM Engine"]
        PoolMgr["Serverless Connection Pool (pool_recycle=60, pre-ping)"]
        NeonDB[("Neon Serverless PostgreSQL (AWS us-east-2)")]
        
        DomainServices --> SQLA
        SQLA --> PoolMgr
        PoolMgr --> NeonDB
    end

    WSClient <-->|"Full-Duplex WS Stream"| WSHandler
    AxiosClient <-->|"HTTP / REST Payloads"| APIRouters
```

---

## 4. Step-by-Step Installation & Quickstart

### Prerequisites
1. **Python 3.11+** installed (`python --version`)
2. **Node.js 18+** & **npm** installed (`node --version`, `npm --version`)
3. A **Neon Serverless PostgreSQL** database connection string (from [Neon Console](https://console.neon.tech))

---

### Step 1: Clone the Repository & Configure `.env`
Navigate to the project root directory:
```bash
# Copy the example environment template
cp .env.example .env
```
Open `.env` in any text editor and paste your Neon PostgreSQL connection string:
```env
# Neon Serverless PostgreSQL Connection String (psycopg 3 driver)
DATABASE_URL=postgresql+psycopg://neondb_owner:YOUR_PASSWORD@ep-your-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require

# Application Secrets
SECRET_KEY=stocksense-secure-random-secret-key-replace-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Default Business Parameters
DEFAULT_NEAR_EXPIRY_DAYS=7
DEFAULT_LEAD_TIME_DAYS=7
DEFAULT_SAFETY_STOCK_FACTOR=1.5
CURRENCY_CODE=INR
CURRENCY_SYMBOL=₹
APP_TIMEZONE=Asia/Kolkata
```

---

### Step 2: Install Backend Dependencies & Run Migrations
From the project root:
```bash
# 1. Install backend requirements
python -m pip install -r backend/requirements.txt

# 2. Run Alembic database migrations to create PostgreSQL tables
python -m alembic upgrade head
```

---

### Step 3: Seed Synthetic Demonstration Dataset
Populate 34 catalog products across 7 retail categories, multi-batch FEFO history, 60 days of sales transactions, and alerts:
```bash
python scripts/seed_demo_data.py
```

---

### Step 4: Start the FastAPI Backend Server
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: **http://127.0.0.1:8000**
- Interactive OpenAPI Swagger UI: **http://127.0.0.1:8000/docs**
- Health Check: **http://127.0.0.1:8000/api/v1/health**

---

### Step 5: Install & Start the React Frontend
In a **separate terminal window**, navigate to `frontend`:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: **http://localhost:5173**

---

## 5. Pre-Configured Demo Credentials

The database seed script provides two pre-configured accounts:

| Role | Email Address | Password | Permissions & Scope |
|---|---|---|---|
| **Shop Owner / Admin** | `owner@stocksense.com` | `Owner@123` | Full access: Dashboard, Products, Batches, POS, Purchases, Suppliers, Forecasts, Reorders, Alerts, Analytics, Users, Settings |
| **Staff Member / Cashier** | `staff@stocksense.com` | `Staff@123` | Operational access: Dashboard, POS Register, Catalog view, Batches view, Expiry view, Alerts |

> **Tip**: Convenient one-click login buttons for both accounts are available directly on the `/login` screen for fast evaluation.

---

## 6. Complete Step-by-Step User & Feature Guide

### Step 1: Public Showcase & Landing Page (`/home`)
- **How it works**: Open **http://localhost:5173/home**. This public presentation screen displays an overview of StockSense's value proposition, architecture highlights, live system status indicators, and direct authentication links.
- **How to use**: Click **"Enter Shop Console"** or **"Sign In"** to proceed to the login screen.

---

### Step 2: Authentication & Role-Based Access Control (`/login`)
- **How it works**: Uses stateless JWT authentication. Tokens are stored securely in browser `localStorage` and dispatched via the `Authorization: Bearer <TOKEN>` header.
- **How to use**:
  1. Click **"Demo: Shop Owner"** to instantly fill `owner@stocksense.com` / `Owner@123`.
  2. Or click **"Demo: Staff Member"** to fill `staff@stocksense.com` / `Staff@123`.
  3. Click **"Sign in to StockSense"** to authenticate.

---

### Step 3: Smart Login-Time Inventory Alert Dialog
- **How it works**: Upon the first dashboard navigation of any authenticated session, StockSense fetches the live inventory alert state and displays a 3-tab modal dialog.
- **The Three Segregated Tabs**:
  1. **Products Nearing Expiry**: Lists batch numbers, remaining units, expiration dates, days remaining (&le;7 days configurable), severity (`critical` &le;3d, `warning` &le;7d), and recommended action (*"Quarantine or mark down immediately"*). Authorized users can adjust the warning threshold window directly from the inline selector (7, 14, 30, or 60 days).
  2. **Very Low-Stock Products**: Displays products where sellable stock is positive but at or below the reorder threshold, daily demand estimates, and suggested order quantities.
  3. **Out-of-Stock Products**: Displays items where total eligible sellable quantity is 0, timestamp of last movement, and replenishment action.
- **Business Rules Enforced**:
  - A product is **never** classified as both low-stock and out-of-stock simultaneously (strict mutual exclusivity).
  - Expired batches are automatically excluded from sellable inventory.
- **How to use**:
  - Click any product row to navigate straight to that product's detail screen.
  - Click **"Remind Me Later"** to dismiss for the session, or **"Acknowledge & Close"** to close.
  - The modal only shows once per login session, preventing annoying interruptions on route changes.

---

### Step 4: Executive Real-Time Dashboard (`/`)
- **How it works**: Powered by the bundled `/api/v1/dashboard/bundle` endpoint and the live WebSocket feed (`/api/v1/ws`).
- **Dashboard Sections**:
  - **Live WebSocket Feed Pill**: Shows a green pulsating badge indicating active real-time connection. Any sale, purchase, or stock movement automatically pushes instant updates to this screen without page refreshing.
  - **8 Primary KPI Cards**: Total Active Products, Total Eligible Units, Low-Stock Products, Near-Expiry Batches, Expired Batches, Today's Revenue, Today's Sales Orders, and Period Gross Profit.
  - **Revenue & Gross Profit Trend Curve**: Interactive Recharts line chart showing daily revenue, cost, and profit over 7, 14, 30, or 60 days.
  - **Category Stock Valuation Breakdown**: Bar chart showing total inventory value and units across retail categories.
  - **Top Velocity Products**: Table ranking best-selling products by sales volume, revenue, and gross profit contribution.
  - **Urgent Expiry Risk Items**: Table showing batches closest to expiration.
  - **Quick Action Bar**: Buttons to jump directly to **POS Register**, **Receive Stock**, **Run Audit**, and **Export CSV Reports**.

---

### Step 5: Products Catalog & Dynamic Stock (`/products`)
- **How it works**: Lists all catalog items with real-time aggregated sellable inventory (summed across active, non-expired batches).
- **How to use**:
  1. **Search**: Type product name, SKU, or barcode in the search bar.
  2. **Filter**: Filter by Category or Stock Status (*In Stock*, *Low Stock*, *Out of Stock*).
  3. **Sort**: Sort by Product Name, SKU, Selling Price, or Stock level.
  4. **Create Product** (Shop Owner only): Click **"Add Product"**, enter Name, SKU, Barcode, Category, Supplier, Unit, Purchase Cost, Selling Price, and Reorder Threshold.
  5. **View Product Detail**: Click any product to open `/products/:id` showing lot-by-lot batch breakdown and sales velocity.

---

### Step 6: Batch-Level Inventory & Expiry Tracking (`/batches`)
- **How it works**: Tracks individual lots with received dates, lot numbers, unit costs, and expiration dates.
- **How to use**:
  1. Click **"Receive Batch"** to record intake of new stock into a specific batch.
  2. Inspect remaining units, unit cost, and days until expiry.
  3. Click **"Adjust"** on any batch to perform an auditable manual stock adjustment (damaged goods, cycle count correction) with a mandatory audit reason.

---

### Step 7: Perishable Expiry Tracker (`/expiry`)
- **How it works**: Segregates inventory lots into 4 distinct health categories:
  - **Expired Batches** (Red): Expiry date < current date. Automatically barred from sales.
  - **Near Expiry** (Amber): Expiring within the configured warning window (&le;7 days).
  - **Healthy Batches** (Green): Expiry date beyond the warning window.
  - **Non-Expiring Items** (Blue): Products without expiry dates (hardware, general goods).
- **How to use**:
  - Inspect days remaining on each perishable lot.
  - Use the quarantine action to remove expired items before they cause shrinkage.

---

### Step 8: Point-of-Sale (POS) Register Terminal (`/pos`)
- **How it works**: Fast cashier terminal for ringing up sales. When an order is placed, StockSense's **FEFO engine** automatically chooses batches with the earliest expiration date to fulfill the quantity.
- **How to use**:
  1. Click products from the grid or scan barcodes using the barcode input.
  2. Adjust line item quantities with `+` and `-`.
  3. Enter an optional **Discount Amount (₹)**.
  4. Select **Payment Method** (*Cash*, *UPI / Digital*, *Card*).
  5. Click **"Complete Sale (₹...)"**.
  6. A printable customer receipt modal appears showing receipt number, date, line items, batch IDs consumed, subtotal, discount, total, and cashier name. Click **"Print Receipt"** to print or save as PDF.

---

### Step 9: Sales History & Auditable Refunds (`/sales`)
- **How it works**: Complete chronological ledger of every sales transaction.
- **How to use**:
  1. Filter sales by date range (*Today*, *Last 7 Days*, *This Month*) or Status (*Completed*, *Cancelled*).
  2. Click any transaction to inspect line items, batches allocated, and cashier ID.
  3. Click **"Cancel / Refund"** to void a transaction. StockSense prompts for a cancellation reason, marks the sale cancelled, generates reverse `customer_return` stock movements, and restores stock back into the original batches atomically.

---

### Step 10: Stock Movement Audit Ledger (`/movements`)
- **How it works**: Immutable ledger recording every physical change in inventory:
  - `purchase_receipt`: Intake of new supplier shipments.
  - `sale`: Units deducted during POS checkout.
  - `customer_return`: Restored units from voided sales.
  - `adjustment_in` / `adjustment_out`: Manual inventory corrections.
  - `expiry_quarantine`: Expired items removed from circulation.
- **How to use**: Search by product SKU or filter by movement type to audit exactly who changed stock, when, which batch was affected, and why.

---

### Step 11: Purchase Receipts & Supplier Intake (`/purchases`)
- **How it works**: Records incoming shipments from registered suppliers.
- **How to use**:
  1. Click **"New Purchase Receipt"**.
  2. Select Supplier and Received Date.
  3. Add items: specify Product, Batch Number, Quantity Received, Unit Cost, and Expiry Date.
  4. Click **"Save Purchase Receipt"**. StockSense generates a unique receipt number (`REC-YYYYMMDD-XXXX`), inserts the batches, logs `purchase_receipt` movements, and recalculates store valuation.

---

### Step 12: Supplier Directory & Lead Time Config (`/suppliers`)
- **How it works**: Maintains supplier contact information and lead times (days needed to deliver goods), which directly powers the reorder replenishment engine.
- **How to use**: Add or edit suppliers, configure their typical lead time in days, contact email, phone, and address.

---

### Step 13: Machine Learning Demand Forecasting (`/forecasts`)
- **How it works**: Select any product to evaluate historical sales patterns and generate future demand forecasts.
- **Models Available**:
  - **Moving Average Baseline (7-Day / 14-Day)**: Transparent, deterministic moving average covering weekly demand rhythms.
  - **Random Forest Regressor**: Scikit-Learn regressor utilizing lag features (lag 1, lag 7, lag 14), 7-day rolling statistics, and day-of-week seasonality.
- **Model Evaluation**: Evaluates forecasts against historical holdout data using **MAE (Mean Absolute Error)** and **RMSE (Root Mean Squared Error)**.
- **How to use**:
  1. Select a product from the dropdown.
  2. Choose Forecast Horizon (7, 14, or 30 days).
  3. Choose Model Type (*Auto-Select*, *Random Forest*, *Moving Average*).
  4. Inspect the interactive Recharts forecast graph showing historical sales vs predicted demand.

---

### Step 14: Replenishment & Reorder Recommendations (`/recommendations`)
- **How it works**: Uses lead-time demand formulas and safety stock factors to tell store owners exactly when and how much to reorder:
  $$\text{Lead Time Demand} = \text{Daily Demand} \times \text{Lead Time (days)}$$
  $$\text{Safety Stock} = \max\left(\lceil 0.5 \times \text{Threshold}\rceil, \lceil 1.5 \times \sqrt{\text{Lead Time}} \times \sigma_{\text{demand}}\rceil\right)$$
  $$\text{Reorder Point} = \max(\text{Threshold}, \text{Lead Time Demand} + \text{Safety Stock})$$
  $$\text{Suggested Order} = \max(0, \text{Target Stock} - \text{Current Stock})$$
- **How to use**:
  - Filter by urgency: **Critical** (stockout or below reorder point), **Moderate** (approaching reorder point), or **Healthy**.
  - Review suggested order quantities and supplier contact info to generate purchase orders.

---

### Step 15: Dedicated Alerts Screen & Resolution (`/alerts`)
- **How it works**: Centralized hub for all active store alerts (Low Stock, Out of Stock, Near Expiry, Expired).
- **How to use**:
  - Filter by alert type or severity (*Critical*, *Warning*, *Info*).
  - Click **"Mark as Read"** on individual alerts or **"Mark All as Read"**.
  - Click **"Reconcile Alerts"** to force an instant database-wide scan.

---

### Step 16: Financial Analytics & CSV Exports (`/analytics`)
- **How it works**: Aggregates financial performance, revenue, cost of goods sold (COGS), gross margins, and inventory turns.
- **How to use**:
  - Inspect margin distributions across categories.
  - Click any **"Export CSV"** button to download full spreadsheets:
    - Products Catalog CSV (`stocksense_products_YYYY-MM-DD.csv`)
    - Sales Ledger CSV (`stocksense_sales_YYYY-MM-DD.csv`)
    - Batch Expiry CSV (`stocksense_batches_YYYY-MM-DD.csv`)
    - Stock Movement Ledger CSV (`stocksense_movements_YYYY-MM-DD.csv`)

---

### Step 17: Staff User Management (`/users`)
- **How it works** (Shop Owner only): Allows provisioning and deactivating staff cashier accounts.
- **How to use**: Click **"Add User"**, enter Full Name, Email, Password, and Role (`staff` or `shop_owner`). Staff members can ring up sales and check inventory but cannot alter store financial settings.

---

### Step 18: Notification & Scheduling Settings (`/settings`)
- **How it works** (Shop Owner only): Configures daily automated inventory check times, SMTP email servers, and notification recipients.
- **Settings Available**:
  - **Daily Schedule Time**: Time of day to run the automated audit (default: `08:00`, timezone: `Asia/Kolkata`).
  - **Expiry Warning Window**: Threshold days before expiration to generate warnings (default: 7 days).
  - **Email Notifications Toggle**: Enable or disable automated email dispatch.
  - **Recipient Emails**: Comma-separated list of store manager emails to receive daily summaries.
  - **SMTP Configuration**: Host, Port (587, 465, 25), Username, Password, and From Email.
  - **"Run Audit Now" Button**: Triggers the daily audit workflow immediately on demand.

---

## 7. How It Works: Core Business Rules & Mechanics

### Deterministic FEFO Engine
1. **Priority by Expiration Date**: During sales checkout, batches with the earliest expiration date (`expiry_date ASC`) are allocated first.
2. **Expired Lot Protection**: Batches where `expiry_date < current_date` are strictly excluded from sellable stock. The POS register refuses to sell expired units.
3. **Atomic Multi-Batch Depletion**: If a customer orders 10 units of an item and Batch A has 4 units while Batch B has 6 units, StockSense splits the order across both batches in a single atomic database transaction.
4. **Audit Integrity on Refund**: Voiding a sale restores stock back into the exact batches it was drawn from and records compensating `customer_return` ledger entries.

---

### Real-Time WebSocket Streaming & Caching
1. **Instant JWT Handshake**: Handshake tokens are verified in-memory from the JWT claims (&le;5ms) without making blocking database queries before WebSocket acceptance.
2. **Immediate Push**: Upon connection, the server immediately pushes current store KPIs and active alert counts (`INITIAL_STATE`).
3. **Event Broadcasting**: When any sale is completed or inventory received, backend routes emit live events (`SALE_COMPLETED`, `BATCH_RECEIVED`, `STOCK_ADJUSTED`). All connected browsers update their UI in real-time.
4. **Sub-Millisecond In-Memory Caching (`FastInMemoryCache`)**: Dashboard metrics and product summaries are cached in memory. Queries return in &le;1ms, bypassing Neon database round-trips. Caches are invalidated instantly when transactions occur.

---

### Daily Automated Inventory Audit & Email Engine
1. **Schedule**: Runs automatically every day at 08:00 (Asia/Kolkata timezone).
2. **Reconciliation**: Scans all products and batches, recalculating low-stock, near-expiry, and out-of-stock items.
3. **Daily Snapshot**: Records a dated `DailyInventorySnapshot` storing total store valuation, active units, and financial totals.
4. **Idempotency & Deduplication**: Checks `scheduled_job_runs` to ensure the daily job runs only once per calendar date.
5. **Responsive HTML Email**: Dispatches an HTML email report with color-coded severity headers, product breakdown tables, and a plain-text fallback. If SMTP is disabled or unconfigured, the job logs execution status gracefully without crashing.

---

### Neon Serverless PostgreSQL Resilience
1. **Connection Recycling (`pool_recycle=60`)**: Neon serverless connection poolers terminate idle connections after 60–120 seconds. Recycling connections every 60 seconds guarantees connections are always fresh.
2. **Connection Pre-Pinging (`pool_pre_ping=True`)**: Verifies connection liveness before executing queries.
3. **TCP Keepalives**: Configured with `keepalives_idle=15`, `keepalives_interval=5`, and `keepalives_count=3` to detect dead sockets in &le;30 seconds instead of hanging for OS TCP timeouts.
4. **Lean Connection Pool (`pool_size=5, max_overflow=10`)**: Prevents connection exhaustion on serverless database tiers.

---

## 8. Daily Audit & Notification CLI

You can trigger the automated daily inventory check and snapshot workflow manually from the command line:

```bash
# Standard execution (respects once-per-day idempotency)
python scripts/run_daily_check.py

# Force execution (bypasses duplicate run guard for testing/auditing)
python scripts/run_daily_check.py --force
```

CLI Output Example:
```text
================================================================================
StockSense Daily Inventory Audit & Notification CLI
Timezone: Asia/Kolkata | Target Schedule: 08:00
================================================================================
Connecting to Neon PostgreSQL... Connected!
[1/4] Running inventory reconciliation & snapshot... Done.
      - Total Valuation: ₹184,320.50
      - Near-Expiry Batches: 4
      - Low-Stock Products: 3
      - Out-of-Stock Products: 2
[2/4] Saving DailyInventorySnapshot record... Saved for 2026-10-14.
[3/4] Checking email notification configuration...
      - Dispatching daily summary email to: owner@stocksense.com... Accepted!
[4/4] Logging ScheduledJobRun audit entry... Job Run ID: 12 (status: completed).
================================================================================
Daily inventory check completed successfully in 1.42s!
================================================================================
```

---

## 9. Automated Verification & Testing

StockSense features an automated test suite across backend and frontend:

### Backend Tests (`pytest` — 37 Tests)
Covers real-time WebSockets, in-memory caching, deterministic FEFO allocation, expiry exclusion, smart alerts, scheduled audits, idempotency deduplication, email delivery retries, RBAC security, and demand forecasting:
```bash
python -m pytest backend/tests -v
```
Test Suite Output:
```text
backend/tests/test_alerts.py::test_low_stock_and_expiry_alerts_generation PASSED
backend/tests/test_auth_rbac.py::test_user_registration_and_login PASSED
backend/tests/test_auth_rbac.py::test_unauthorized_access_rejected PASSED
backend/tests/test_auth_rbac.py::test_role_based_authorization PASSED
backend/tests/test_fefo_inventory.py::test_batch_receipt_and_stock_movements PASSED
backend/tests/test_fefo_inventory.py::test_fefo_order_and_multi_batch_sale_allocation PASSED
backend/tests/test_fefo_inventory.py::test_rejection_of_sales_exceeding_stock PASSED
backend/tests/test_fefo_inventory.py::test_prevention_of_sales_from_expired_batches PASSED
backend/tests/test_fefo_inventory.py::test_sale_cancellation_and_stock_restoration PASSED
backend/tests/test_forecasting.py::test_moving_average_forecast_calculations PASSED
backend/tests/test_forecasting.py::test_forecast_insufficient_history PASSED
backend/tests/test_products.py::test_product_creation_and_duplicate_sku_validation PASSED
backend/tests/test_recommendations_and_dashboard.py::test_reorder_recommendation_and_dashboard_aggregation PASSED
backend/tests/test_smart_alerts_notifications.py::test_near_expiry_detection PASSED
backend/tests/test_smart_alerts_notifications.py::test_low_stock_detection PASSED
backend/tests/test_smart_alerts_notifications.py::test_out_of_stock_detection PASSED
backend/tests/test_smart_alerts_notifications.py::test_expired_batches_excluded_from_sellable_stock PASSED
backend/tests/test_smart_alerts_notifications.py::test_no_overlap_between_low_stock_and_out_of_stock PASSED
backend/tests/test_smart_alerts_notifications.py::test_alert_reconciliation_and_deduplication PASSED
backend/tests/test_smart_alerts_notifications.py::test_login_time_alert_retrieval_api PASSED
backend/tests/test_smart_alerts_notifications.py::test_alert_visibility_and_mark_all_read PASSED
backend/tests/test_smart_alerts_notifications.py::test_daily_job_execution PASSED
backend/tests/test_smart_alerts_notifications.py::test_repeated_job_execution_duplicate_prevention PASSED
backend/tests/test_smart_alerts_notifications.py::test_email_settings_persistence PASSED
backend/tests/test_smart_alerts_notifications.py::test_scheduled_email_eligibility PASSED
backend/tests/test_smart_alerts_notifications.py::test_email_content_generation PASSED
backend/tests/test_smart_alerts_notifications.py::test_missing_email_configuration_graceful_handling PASSED
backend/tests/test_smart_alerts_notifications.py::test_provider_rejection_and_retry_handling PASSED
backend/tests/test_smart_alerts_notifications.py::test_email_idempotency_deduplication PASSED
backend/tests/test_smart_alerts_notifications.py::test_timezone_aware_scheduling PASSED
backend/tests/test_smart_alerts_notifications.py::test_authorization_for_settings PASSED
backend/tests/test_smart_alerts_notifications.py::test_empty_report_behavior PASSED
backend/tests/test_smart_alerts_notifications.py::test_accurate_daily_snapshot_creation PASSED
backend/tests/test_websockets.py::test_websocket_anonymous_handshake PASSED
backend/tests/test_websockets.py::test_websocket_authenticated_handshake PASSED
backend/tests/test_websockets.py::test_websocket_ping_pong PASSED
backend/tests/test_websockets.py::test_cache_invalidation_and_event_broadcast PASSED

======================= 37 passed in 114.17s ========================
```

---

### Frontend Tests (`vitest` — 5 Tests)
```bash
cd frontend
npm test -- --run
```
Output:
```text
 ✓ src/test/components.test.tsx (5 tests) 95ms
 Test Files  1 passed (1)
      Tests  5 passed (5)
```

---

### Production TypeScript Build
```bash
cd frontend
npm run build
```
Output:
```text
✓ 2581 modules transformed.
dist/index.html                   0.49 kB
dist/assets/index-DQdjCAMS.css   42.40 kB
dist/assets/index-BBJyxPhe.js   966.13 kB
✓ built in 3.76s
```

---

## 10. Troubleshooting & FAQ

#### Q: The browser shows `404 Not Found` when opening `http://localhost:8000`.
- **A**: Port `8000` is the FastAPI backend API server. Open **`http://localhost:5173`** for the React application UI. Interactive API documentation is available at **`http://localhost:8000/docs`**.

#### Q: How do I configure Neon PostgreSQL connection string?
- **A**: Ensure your `.env` contains the `postgresql+psycopg://` URL schema (psycopg 3 driver):
  ```env
  DATABASE_URL=postgresql+psycopg://neondb_owner:PASSWORD@ep-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require
  ```

#### Q: Why does the WebSocket status badge turn amber?
- **A**: The amber badge indicates that the WebSocket connection is temporarily reconnecting. StockSense has an automatic exponential backoff reconnect mechanism that re-establishes the connection within 1–10 seconds.

#### Q: Can I run StockSense completely offline without Neon?
- **A**: Yes. In development or test environments, set `DATABASE_URL=sqlite:///./stocksense_dev.db` in your `.env`. Alembic and SQLAlchemy will create a local SQLite database file automatically.

#### Q: How do I change the currency symbol?
- **A**: Update `CURRENCY_SYMBOL` in your `.env` file (e.g., `CURRENCY_SYMBOL=$` or `CURRENCY_SYMBOL=€`). All frontend prices and reports automatically update to the configured currency symbol.

---

## 11. License
Developed for small retailers, grocery stores, community pharmacies, and general store inventory management. Licensed under the MIT License.
