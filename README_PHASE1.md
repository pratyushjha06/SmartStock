# SmartStock Phase 1 — Setup Guide

## Included
React/Vite frontend and FastAPI backend for login, products, inventory, CSV sales validation/import, duplicate detection, stock updates, sales records, and dashboard metrics. SQLite is the default database for easy local setup; PostgreSQL can be configured with `DATABASE_URL`.

## Requirements
Python 3.10+, Node.js 18+, npm.

## Backend setup (Windows PowerShell)
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:JWT_SECRET="replace-with-a-long-random-secret"
uvicorn app.main:app --reload
```
If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then activate again.

## Backend setup (macOS/Linux)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET="replace-with-a-long-random-secret"
uvicorn app.main:app --reload
```
API: http://localhost:8000 | Swagger: http://localhost:8000/docs

Demo login: `admin` / `admin123` (change before deployment).

## Frontend setup
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Optional `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

## Quick test
1. Login with demo credentials.
2. Add product SKU `SKU-001`, opening stock at least 10.
3. Go to Sales Upload and upload `public/sample-sales.csv`.
4. Verify inventory decreases by 3 and sales records appear.
5. Try duplicate upload; API should reject it.
6. Adjust stock from Inventory and check dashboard.

## CSV schema
Required headers: `transaction_id,sale_date,sku,quantity,unit_price`
Date format: `YYYY-MM-DD`; quantity positive integer; price non-negative; SKU must exist; inventory must be sufficient. Upload is all-or-nothing.

## GitHub commit
From the project root:
```bash
git init
git add .
git commit -m "feat: implement SmartStock phase 1 core inventory system"
```
Add `.gitignore` entries for `.venv`, `node_modules`, `.env`, database files, and build output before pushing.

## Phase boundary
Phase 1 includes the foundation and inventory workflow. Demand forecasting, reorder recommendations, purchase orders, and advanced analytics belong to Phase 2.
