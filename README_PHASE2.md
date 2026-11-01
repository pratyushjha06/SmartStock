# SmartStock — Phase 2: Demand Forecasting & Inventory Optimization

Phase 2 extends the Phase 1 inventory/sales application with a forecasting baseline, reorder recommendations, purchase orders, receiving/cancellation workflows, and forecast evaluation.

## Included features
- SKU-level daily demand estimation using a configurable moving-average lookback.
- Forecast generation for a configurable horizon (bounded to 1–90 days).
- Explicit fallback label when no sales history exists (`fallback_zero_history`).
- Reorder recommendations using average daily demand × (lead time + safety-stock days), compared with current inventory.
- Purchase order creation with SKU/quantity/cost validation.
- Purchase order listing, receiving (adds received quantities to inventory), and cancellation.
- Baseline evaluation endpoint returning actual vs predicted quantity and MAPE when actual demand is non-zero.

## Setup (Windows CMD)
From the `backend` directory, activate your virtual environment and install dependencies:

```cmd
python -m pip install -r requirements.txt
set JWT_SECRET=replace-with-a-long-random-secret
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to use/test the API. Phase 1 demo login: `admin` / `admin123`.

## Phase 2 API workflow
1. Login at `POST /api/auth/login` and authorize with the returned bearer token.
2. Generate forecasts: `POST /api/forecast/generate` with JSON such as:
   ```json
   {"lookback_days":30,"horizon_days":14}
   ```
3. View forecasts: `GET /api/forecast` (optional `sku` and `limit`).
4. Get reorder suggestions: `GET /api/inventory/recommendations?lookback_days=30&lead_time_days=7&safety_stock_days=3`.
5. Create a purchase order: `POST /api/purchase-orders` with:
   ```json
   {"supplier":"Example Supplier","notes":"Restock","items":[{"sku":"SKU001","quantity":20,"unit_cost":45.5}]}
   ```
6. List orders: `GET /api/purchase-orders`.
7. Receive order: `POST /api/purchase-orders/{order_id}/receive` (updates stock once; duplicate receipt is rejected).
8. Cancel an unreceived order: `POST /api/purchase-orders/{order_id}/cancel`.
9. Evaluate a SKU baseline: `GET /api/forecast/evaluation?sku=SKU001&forecast_days=14`.

## Notes / limitations
- Forecasting is an explainable moving-average baseline, not a trained ML model. It is suitable as a project baseline and can later be compared with exponential smoothing or other models.
- Forecast records are generated on demand and stored in the database.
- Evaluation is a simple baseline comparison and should not be interpreted as a rigorous backtesting framework.
- SQLite is used by default for local development. Set `DATABASE_URL` to use another SQLAlchemy-supported database.
- This is an educational project starter; change the demo credentials and JWT secret before any deployment.
