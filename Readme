# SmartStock

## SME Retail Demand Forecasting & Inventory Optimization Platform

SmartStock is an inventory and sales management application designed for
small and medium-sized retailers. It combines core inventory operations
with a demand-forecasting baseline and reorder planning workflows.

**Frontend:** React + Vite\
**Backend:** FastAPI (Python)\
**Database:** SQLite by default; SQLAlchemy-supported database via
`DATABASE_URL`\
**Forecasting:** SKU-level moving-average baseline

------------------------------------------------------------------------

## Table of Contents

-   [Problem Statement](#problem-statement)
-   [Objectives](#objectives)
-   [Features](#features)
-   [Technology Stack](#technology-stack)
-   [Project Structure](#project-structure)
-   [Requirements](#requirements)
-   [Local Setup on Windows CMD](#local-setup-on-windows-cmd)
-   [Local Setup on PowerShell](#local-setup-on-powershell)
-   [Using the Application](#using-the-application)
-   [Sales CSV Format](#sales-csv-format)
-   [Phase 2 API Workflow](#phase-2-api-workflow)
-   [Testing Checklist](#testing-checklist)
-   [Configuration](#configuration)
-   [Deployment Overview](#deployment-overview)
-   [Known Limitations](#known-limitations)
-   [Git Commit](#git-commit)
-   [Future Enhancements](#future-enhancements)

------------------------------------------------------------------------

## Problem Statement

Small retailers often manage stock manually and have limited visibility
into sales trends, upcoming demand, and reorder timing. This can lead to
stockouts, excess inventory, and delayed replenishment.

SmartStock provides a centralized workflow for maintaining product
records, importing sales, updating stock, estimating demand, and
preparing purchase orders.

## Objectives

-   Maintain product and inventory records.
-   Import sales transactions from CSV files with validation.
-   Update inventory based on recorded sales.
-   Provide dashboard metrics and sales history.
-   Estimate future SKU-level demand from historical sales.
-   Recommend reorder quantities using demand, lead time, and
    safety-stock settings.
-   Support purchase-order creation, receiving, and cancellation.
-   Provide a baseline forecast evaluation metric.

## Features

### Phase 1 --- Core Inventory Management

-   Login with a seeded demo manager account.
-   Product listing, creation, updating, and deactivation.
-   Inventory adjustment.
-   CSV sales upload with required-field and data validation.
-   Duplicate transaction detection.
-   All-or-nothing sales import behavior.
-   Inventory reduction for valid sales.
-   Sales records and dashboard metrics.
-   React-based web interface.

### Phase 2 --- Demand Forecasting & Inventory Optimization

-   Daily demand estimates by SKU using a configurable moving-average
    lookback.
-   Forecast generation for a configurable horizon (1--90 days).
-   Explicit fallback label when no sales history exists.
-   Reorder recommendations based on average daily demand, lead time,
    safety-stock days, and current inventory.
-   Purchase-order creation and listing.
-   Purchase-order receiving (received quantities increase stock).
-   Purchase-order cancellation for unreceived orders.
-   Baseline forecast evaluation with actual-versus-predicted quantities
    and MAPE when applicable.

------------------------------------------------------------------------

## Technology Stack

  Layer                  Technology
  ---------------------- ------------------------------
  Frontend:               React, Vite, JavaScript, CSS
  Backend:                Python, FastAPI
  API documentation:      OpenAPI / Swagger UI
  ORM:                    SQLAlchemy
  Local database:         SQLite
  CSV processing:         Python CSV utilities
  Authentication:         JWT bearer tokens
  Password hashing:       Passlib with bcrypt
  Forecasting baseline:   Moving average

## Project Structure

``` text
SmartStock/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── sample-sales.csv
│   ├── src.jsx
│   ├── style.css
│   ├── index.html
│   └── package.json
├── .gitignore
└── README.md
```

## Requirements

Install these before running the project:

-   Python 3.10 or newer
-   Node.js 18 or newer
-   npm
-   Git (optional, for version control)

## Local Setup on Windows CMD

### 1. Start the backend

Open CMD and navigate to the backend folder:

``` cmd
cd backend
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
set JWT_SECRET=replace-with-a-long-random-secret
python -m uvicorn app.main:app --reload
```

Keep this terminal running.

Backend: - API base: http://127.0.0.1:8000 - Swagger docs:
http://127.0.0.1:8000/docs

### 2. Start the frontend

Open a second CMD window from the project root:

``` cmd
cd frontend
npm install
```

Create `frontend/.env` with:

``` env
VITE_API_URL=http://127.0.0.1:8000
```

Then start Vite:

``` cmd
npm run dev
```

Open the URL printed in the terminal, usually http://localhost:5173.

> If you edit `frontend/.env`, restart the Vite server for the change to
> take effect.

## Local Setup on PowerShell

### Backend

``` powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:JWT_SECRET="replace-with-a-long-random-secret"
python -m uvicorn app.main:app --reload
```

If script activation is blocked, run this in the same PowerShell window
and activate again:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Frontend

Open another PowerShell window:

``` powershell
cd frontend
npm install
npm run dev
```

Optional `frontend/.env`:

``` env
VITE_API_URL=http://127.0.0.1:8000
```

## Using the Application

### Demo login

-   **Username:** `admin`
-   **Password:** `admin123`

This is a development/demo account. Change or replace the default
credentials before deployment or public sharing.

### Suggested workflow

1.  Sign in to SmartStock.
2.  Add products with unique SKUs, category, unit price, reorder level,
    and initial stock.
3.  Review product quantities in the Inventory section.
4.  Upload a sales CSV from Sales Upload.
5.  Check Sales Records and confirm stock decreased for sold quantities.
6.  Review dashboard metrics.
7.  Open the backend Swagger page to demonstrate Phase 2 endpoints.
8.  Generate demand forecasts and inspect reorder recommendations.
9.  Create a purchase order, receive it, and verify inventory increases.
10. Try cancelling an unreceived purchase order.

## Sales CSV Format

The CSV must contain these headers:

``` csv
transaction_id,sale_date,sku,quantity,unit_price
```

Example:

``` csv
transaction_id,sale_date,sku,quantity,unit_price
TXN-1001,2026-10-28,SKU-001,2,15999
TXN-1002,2026-10-29,SKU-002,3,599
TXN-1003,2026-10-29,SKU-003,5,60
```

Validation rules: - `transaction_id` must be present and unique. -
`sale_date` must use `YYYY-MM-DD`. - `sku` must match an existing
product. - `quantity` must be a positive integer. - `unit_price` must be
non-negative. - The product must have sufficient inventory for the
sale. - Duplicate transactions are rejected. - Import is all-or-nothing:
invalid rows prevent partial import.

A sample file is included at `frontend/public/sample-sales.csv`. You can
also use the SmartStock sample CSV created for your current products.

## Phase 2 API Workflow

Use Swagger UI at:

http://127.0.0.1:8000/docs

1.  Log in using `POST /api/auth/login`.

2.  Copy the returned access token and use **Authorize** with the bearer
    token.

3.  Generate forecasts:

    `POST /api/forecast/generate`

    Example body:

    ``` json
    {
      "lookback_days": 30,
      "horizon_days": 14
    }
    ```

4.  View forecast records:

    `GET /api/forecast`

    Optional query parameters include `sku` and `limit`.

5.  Get reorder recommendations:

    `GET /api/inventory/recommendations?lookback_days=30&lead_time_days=7&safety_stock_days=3`

6.  Create a purchase order:

    `POST /api/purchase-orders`

    Example body:

    ``` json
    {
      "supplier": "Example Supplier",
      "notes": "Restock",
      "items": [
        {
          "sku": "SKU-001",
          "quantity": 20,
          "unit_cost": 45.5
        }
      ]
    }
    ```

7.  List purchase orders:

    `GET /api/purchase-orders`

8.  Receive a purchase order:

    `POST /api/purchase-orders/{order_id}/receive`

    Receiving adds the ordered quantities to inventory. A duplicate
    receipt is rejected.

9.  Cancel an unreceived purchase order:

    `POST /api/purchase-orders/{order_id}/cancel`

10. Evaluate a SKU forecast baseline:

    `GET /api/forecast/evaluation?sku=SKU-001&forecast_days=14`

Use a SKU that exists in your database when testing these requests.



## Known Limitations

-   Forecasting uses a moving-average baseline, not a trained
    machine-learning model.
-   Forecast evaluation is a simple baseline comparison, not a
    comprehensive rolling backtest.
-   MAPE is not meaningful when actual demand is zero; the evaluation
    behavior depends on available non-zero actuals.
-   The React interface primarily demonstrates Phase 1 workflows. Phase
    2 operations are available through the FastAPI Swagger API unless a
    dedicated frontend screen is added.
-   SQLite is intended for local development. Use a persistent hosted
    database for deployment.
-   This is an academic project and should be security-reviewed before
    production use.



## Future Enhancements

-   Integrate Phase 2 forecast and purchase-order features into the
    React frontend.
-   Compare moving average with exponential smoothing or other
    forecasting models.
-   Add robust rolling-origin backtesting and additional metrics such as
    MAE and RMSE.
-   Add supplier management, role-based permissions, and audit logs.
-   Add automated tests and deployment pipelines.
-   Improve data visualization and forecast explainability.
