# StockSense REST API Specification & Endpoint Guide

All versioned REST endpoints are routed under `/api/v1`.
Authentication is enforced using JSON Web Tokens (JWT) passed via `Authorization: Bearer <token>`.

---

## 1. Authentication & User Management
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Register new user. First user defaults to `shop_owner`. |
| `POST` | `/api/v1/auth/login` | Public | Authenticates user; returns JWT token, role, and details. |
| `GET` | `/api/v1/auth/me` | Authenticated | Returns profile of current user. |
| `GET` | `/api/v1/users` | Shop Owner | Lists all user accounts. |
| `POST` | `/api/v1/users` | Shop Owner | Provisions a new staff member account. |
| `PUT` | `/api/v1/users/{id}` | Shop Owner | Updates user role, active status, or password. |

---

## 2. Product Catalog & Categories
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/products` | Staff / Owner | Lists products with live stock totals and filters. |
| `POST` | `/api/v1/products` | Shop Owner | Creates product with duplicate SKU validation. |
| `GET` | `/api/v1/products/{id}` | Staff / Owner | Retrieves product with FEFO batch breakdown. |
| `PUT` | `/api/v1/products/{id}` | Shop Owner | Updates product prices, thresholds, or info. |
| `DELETE` | `/api/v1/products/{id}` | Shop Owner | Soft-deactivates product. |
| `GET` | `/api/v1/categories` | Staff / Owner | Lists categories with product counts. |
| `POST` | `/api/v1/categories` | Shop Owner | Creates a new category. |
| `PUT` | `/api/v1/categories/{id}` | Shop Owner | Updates category. |
| `DELETE`| `/api/v1/categories/{id}` | Shop Owner | Deletes category. |

---

## 3. Inventory & Expiry Management
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/inventory/batches` | Staff / Owner | Lists batches with remaining days until expiry. |
| `POST` | `/api/v1/inventory/batches` | Staff / Owner | Receives stock into a batch with movement log. |
| `POST` | `/api/v1/inventory/batches/{id}/adjust` | Shop Owner | Adjusts batch quantity with auditable reason. |
| `GET` | `/api/v1/inventory/movements` | Staff / Owner | Lists immutable stock movement ledger records. |
| `GET` | `/api/v1/inventory/expiry-summary` | Staff / Owner | Groups batches: expired, near-expiry, healthy. |

---

## 4. Sales & POS Transactions
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/sales` | Staff / Owner | Lists historical sales with date and status filters. |
| `POST` | `/api/v1/sales` | Staff / Owner | Processes POS sale with automatic FEFO allocation. |
| `GET` | `/api/v1/sales/{id}` | Staff / Owner | Detailed receipt breakdown with batch snapshots. |
| `POST` | `/api/v1/sales/{id}/cancel` | Shop Owner | Voids sale and restores batch stock via returns. |

---

## 5. Purchase Receipts & Suppliers
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/purchases` | Staff / Owner | Lists purchase receipts from suppliers. |
| `POST` | `/api/v1/purchases` | Shop Owner | Records purchase shipment and creates batches. |
| `GET` | `/api/v1/purchases/{id}` | Staff / Owner | Single purchase receipt detail. |
| `GET` | `/api/v1/suppliers` | Staff / Owner | Lists registered vendor directory. |
| `POST` | `/api/v1/suppliers` | Shop Owner | Registers a new supplier with lead times. |
| `PUT` | `/api/v1/suppliers/{id}` | Shop Owner | Updates supplier contact details or lead time. |
| `DELETE`| `/api/v1/suppliers/{id}` | Shop Owner | Deletes supplier record. |

---

## 6. Demand Forecasting & Replenishment
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/forecasts/{product_id}` | Staff / Owner | Generates demand projection and MAE/RMSE metrics. |
| `GET` | `/api/v1/forecasts` | Staff / Owner | Lists demand forecasts across active products. |
| `GET` | `/api/v1/forecasts/evaluation` | Staff / Owner | Compares Moving Average vs Random Forest models. |
| `GET` | `/api/v1/recommendations/reorder` | Staff / Owner | Calculates replenishment order points & quantities. |

---

## 7. Alerts, Analytics & Settings
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | Staff / Owner | Returns 8 real-time executive KPI metrics. |
| `GET` | `/api/v1/alerts` | Staff / Owner | Lists alerts with type, severity, and read status. |
| `POST` | `/api/v1/alerts/reconcile` | Staff / Owner | Reconciles alerts with live inventory realities. |
| `PATCH`| `/api/v1/alerts/{id}/read` | Staff / Owner | Marks alert as read. |
| `PATCH`| `/api/v1/alerts/{id}/resolve` | Staff / Owner | Resolves alert condition. |
| `GET` | `/api/v1/analytics/sales` | Staff / Owner | Continuous sales, COGS, and profit trend points. |
| `GET` | `/api/v1/analytics/categories` | Staff / Owner | Category stock and monetary valuations. |
| `GET` | `/api/v1/analytics/top-products` | Staff / Owner | Top velocity products ranked by units and profit. |
| `GET` | `/api/v1/analytics/expiry-risk` | Staff / Owner | Summary of expired and near-expiry stock risk. |
| `GET` | `/api/v1/analytics/export/csv` | Staff / Owner | Downloads sales or inventory CSV spreadsheets. |
| `GET` | `/api/v1/settings` | Staff / Owner | Retrieves application business parameters. |
| `PUT` | `/api/v1/settings/{key}` | Shop Owner | Updates setting (near-expiry days, currency, etc.). |
