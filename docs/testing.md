# StockSense Automated Testing Guide

## 1. Overview
StockSense incorporates end-to-end unit, business logic, and API integration tests across both the backend (`pytest`) and frontend (`vitest`) tiers.

---

## 2. Backend Automated Test Suite (`pytest`)

### 2.1. Executed Test Matrix
The backend test suite is located in `backend/tests/` and was executed against all 20 required criteria:

| Test File | Verified Business Rule | Status |
|---|---|---|
| `test_auth_rbac.py` | User registration & JWT generation | **PASSED** |
| `test_auth_rbac.py` | Unauthorized 401 access rejection | **PASSED** |
| `test_auth_rbac.py` | Role-based 403 authorization (Owner vs Staff) | **PASSED** |
| `test_products.py` | Product creation & duplicate SKU rejection | **PASSED** |
| `test_fefo_inventory.py` | Batch inventory stock receipt | **PASSED** |
| `test_fefo_inventory.py` | Stock movement ledger entry generation | **PASSED** |
| `test_fefo_inventory.py` | FEFO batch sequencing (earliest expiry first) | **PASSED** |
| `test_fefo_inventory.py` | Sales fulfilled across multiple batches | **PASSED** |
| `test_fefo_inventory.py` | Rejection of sales exceeding eligible stock | **PASSED** |
| `test_fefo_inventory.py` | Exclusion and rejection of expired batch sales | **PASSED** |
| `test_fefo_inventory.py` | Transaction rollback on allocation failure | **PASSED** |
| `test_fefo_inventory.py` | Accurate Revenue, COGS, and Gross Profit | **PASSED** |
| `test_fefo_inventory.py` | Sale cancellation & stock restoration via customer return | **PASSED** |
| `test_alerts.py` | Low-stock alert generation at reorder threshold | **PASSED** |
| `test_alerts.py` | Near-expiry alert generation in warning window | **PASSED** |
| `test_alerts.py` | Expired-stock critical alert identification | **PASSED** |
| `test_forecasting.py` | Moving Average baseline projections | **PASSED** |
| `test_forecasting.py` | Non-negative constraint & insufficient history handling | **PASSED** |
| `test_recommendations_and_dashboard.py` | Smart reorder calculations & safety buffers | **PASSED** |
| `test_recommendations_and_dashboard.py` | Dashboard KPI aggregation consistency | **PASSED** |

### 2.2. Running Backend Tests
Execute from the project root:
```bash
python -m pytest backend/tests -v
```

---

## 3. Frontend Automated Test Suite (`vitest`)

### 3.1. Executed Test Matrix
The frontend test suite is located in `frontend/src/test/` and executed using Vitest + React Testing Library:

| Test File | Verified Component / State | Status |
|---|---|---|
| `components.test.tsx` | `StatCard` KPI display and click event firing | **PASSED** |
| `components.test.tsx` | `Badge` styling variants (success, danger, warning) | **PASSED** |
| `components.test.tsx` | `Modal` accessibility, visibility toggles & callbacks | **PASSED** |
| `components.test.tsx` | `EmptyState` zero-state render & action triggers | **PASSED** |
| `components.test.tsx` | `LoadingSpinner` asynchronous state indicators | **PASSED** |

### 3.2. Running Frontend Tests
Execute from the `frontend/` directory:
```bash
cd frontend
npm test
```
