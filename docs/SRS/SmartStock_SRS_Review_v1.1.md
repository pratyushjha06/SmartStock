# SmartStock SRS — Requirements Review & Revision (v1.1)

This document contains **only the sections that changed**, plus a change log. Everything else in SRS v1.0 (Sections 1, 2.1, 2.3–2.5, 3.4, 5, Appendix A) is unaffected and should be carried over as-is when this is merged back into the full SRS.

---

## CHANGE LOG (v1.0 → v1.1)

| # Type Section Change Reason |                         |     |                                                                                                                                                                    |                                                                                                                                                                                                                 |
| ---------------------------- | ----------------------- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1                            | **Fix (inconsistency)** | 3.1 | FR-2 expanded to require capturing opening stock at product creation                                                                                               | No FR previously initialized stock — "current stock" had no starting value.                                                                                                                                     |
| 2                            | **Fix (inconsistency)** | 3.1 | FR-5 clarified: stock decrements at upload-validation time, not at nightly ETL/forecast batch time                                                                 | Reorder alerts (FR-8) need near-real-time stock; the warehouse/ETL batch is for analytics and forecasting only, and runs nightly. Without this split, alerts would be stale for up to 24 hours.                 |
| 3                            | **Add (MVP, minimal)**  | 3.1 | New FR-13: Receive Purchase Order (goods receipt) increments stock; supports cancellation                                                                          | Without a receipt step, stock only ever decreases — the PO lifecycle was a dead end. This is the minimum addition to make the system internally consistent.                                                     |
| 4                            | **Add (MVP, minimal)**  | 3.1 | New FR-14: Forecast accuracy (MAPE) is computed by comparing stored forecasts to actual sales once the forecast date has passed                                    | FR-11 (display MAPE) previously had no requirement describing where that number comes from.                                                                                                                     |
| 5                            | **Add (MVP, minimal)**  | 3.1 | New FR-15: promotes the "insufficient history → fallback to moving average, flagged low-confidence" rule from a use-case alternate flow (UC-3) to a first-class FR | It's a real business rule the reorder engine depends on — it shouldn't only live inside a use-case footnote.                                                                                                    |
| 6                            | **Reprioritize**        | 3.1 | FR-10 (create PO) raised from Medium → High / MVP, to match FR-13 and the demo script                                                                              | FR-10 and FR-13 form one lifecycle; splitting their priority was inconsistent.                                                                                                                                  |
| 7                            | **Add (NFR, minimal)**  | 3.2 | New NFR-10: duplicate transaction rows must not double-decrement stock or double-count sales (idempotent ingestion)                                                | FR-5 says the ETL "deduplicates" but never defined dedup at the operational/stock-decrement layer, which runs separately (see change #2).                                                                       |
| 8                            | **Add (NFR, minimal)**  | 3.2 | New NFR-11: stock shall never display as negative; a computed negative value is floored at 0 and flagged for review                                                | Oversell / data-entry errors (sale qty > recorded stock) were previously undefined behavior.                                                                                                                    |
| 9                            | **Add (use case)**      | 3.3 | New UC-4: Receive Purchase Order                                                                                                                                   | Matches new FR-13; without it, the PO lifecycle in Section 3.3 was incomplete (create-only).                                                                                                                    |
| 10                           | **Add (subsection)**    | 3.5 | New 3.5.1: Current Stock Calculation Rule, with explicit formula                                                                                                   | Makes the "current stock" concept testable and gives the reorder-engine tests (already flagged for BVA/decision tables) something precise to test against.                                                      |
| 11                           | **Data model fix**      | 4.1 | New operational table `inventory_stock`; `purchase_orders` gets `received_quantity`, `received_at`, and an explicit status enum                                    | `dim_product` is a dimension table (slowly-changing, descriptive) and is the wrong place to store a fast-changing operational value like live stock. This was a design inconsistency, not just a missing field. |
| 12                           | **Scope clarity**       | 3.1 | Added an explicit **MVP** column (Yes/No) to the FR table, separate from Priority                                                                                  | Priority and MVP-inclusion were being conflated; FR-12 (multi-store) was already correctly marked future-only, but nothing else was labeled consistently.                                                       |
| 13                           | **No change**           | —   | FR-1, FR-3, FR-4, FR-6, FR-7, FR-8, FR-9, FR-12 unchanged; NFR-1–9 unchanged                                                                                       | Reviewed and found consistent — no gaps identified.                                                                                                                                                             |

**Net effect:** 3 new FRs, 2 new NFRs, 1 new use case, 1 new subsection, 1 modified table, 1 reprioritized FR. Nothing was added outside the inventory/stock/PO/forecast-evaluation/MVP-scope areas you asked me to check, and nothing here requires new technology, new team skills, or additional timeline — it's closing logical gaps in what was already planned.

---

## REVISED SECTION 2.2 — Product Functions (Summary)

*(bullet list — only the changed/added bullets shown; rest unchanged)*

- Product and inventory master-data management, **including capturing and maintaining opening and current stock levels**.
- Sales transaction ingestion (CSV upload or simulated feed) with validation **and immediate stock decrement**.
- \~\~Purchase-order creation workflow (manual, triggered from an alert).\~\~ → **Purchase-order lifecycle: creation, receipt (with automatic stock replenishment), and cancellation.**
- **Forecast accuracy evaluation: comparing stored forecasts against actual sales once outcomes are known.**

---

## REVISED SECTION 3.1 — Functional Requirements

| ID Requirement Description Priority MVP              |                                                                                                                                                                                                                                                                                                                                                                                                                 |          |                       |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------- |
| FR-1                                                 | The system shall allow a registered user to log in using email and password, and shall restrict access to features based on role (Owner/Manager vs. Staff).                                                                                                                                                                                                                                                     | High     | Yes                   |
| **FR-2** *(revised)*                                 | The system shall allow an Owner/Manager to create, update, and deactivate product (SKU) records, including name, category, unit cost, unit price, supplier lead time, **and opening stock quantity at time of creation**.                                                                                                                                                                                       | High     | Yes                   |
| FR-3                                                 | The system shall allow Staff to upload daily sales transactions via a CSV file.                                                                                                                                                                                                                                                                                                                                 | High     | Yes                   |
| FR-4                                                 | The system shall validate uploaded transaction data and reject/flag rows with missing SKU references, negative quantities, or malformed dates.                                                                                                                                                                                                                                                                  | High     | Yes                   |
| **FR-5** *(revised)*                                 | Upon successful validation of an uploaded transaction (FR-4), the system shall **immediately decrement the affected SKU's current stock** by the sold quantity (subject to NFR-10 and NFR-11). Separately, a scheduled ETL process shall clean, deduplicate, and load validated transactions into the warehouse fact table for forecasting and analytics; this batch process does **not** control stock levels. | High     | Yes                   |
| FR-6                                                 | The system shall generate a demand forecast for each active SKU for a configurable forecast horizon (default: next 7 days), using historical sales data.                                                                                                                                                                                                                                                        | High     | Yes                   |
| FR-7                                                 | The system shall compute a recommended reorder point for each SKU using forecasted demand, current stock level, supplier lead time, and a configurable safety-stock margin.                                                                                                                                                                                                                                     | High     | Yes                   |
| FR-8                                                 | The system shall generate an alert when a SKU's current stock falls at or below its computed reorder point.                                                                                                                                                                                                                                                                                                     | High     | Yes                   |
| FR-9                                                 | The system shall display a dashboard showing sales trends, current stock levels, active alerts, and inventory turnover for the logged-in user's store.                                                                                                                                                                                                                                                          | High     | Yes                   |
| **FR-10** *(reprioritized)*                          | The system shall allow an Owner/Manager to create a purchase order record directly from a reorder alert, specifying quantity ordered.                                                                                                                                                                                                                                                                           | **High** | **Yes**               |
| FR-11                                                | The system shall display forecast-accuracy metrics (e.g., MAPE) for evaluation/demo purposes.                                                                                                                                                                                                                                                                                                                   | Medium   | Yes                   |
| FR-12                                                | The system shall support multiple stores under a single account.                                                                                                                                                                                                                                                                                                                                                | Low      | **No — Future Scope** |
| **FR-13** *(new)*                                    | The system shall allow an Owner/Manager to mark an open purchase order as **Received**, optionally editing the actual received quantity if it differs from the ordered quantity; upon receipt, the system shall increment the corresponding SKU's current stock by the received quantity. The system shall also allow an open purchase order to be marked **Cancelled**, which shall not affect stock.          | High     | Yes                   |
| **FR-14** *(new)*                                    | Once a forecasted date has passed and actual sales data for that date is available, the system shall compute forecast accuracy (MAPE) by comparing the stored forecast against actual demand, and shall make this value available to FR-11.                                                                                                                                                                     | Medium   | Yes                   |
| **FR-15** *(new, promoted from UC-3 alternate flow)* | If a SKU has fewer than a configurable minimum number of days of historical sales data (default: 14 days), the system shall generate its forecast using a simple moving-average fallback instead of the primary model, and shall flag that forecast as "low confidence."                                                                                                                                        | High     | Yes                   |

---

## REVISED SECTION 3.2 — Non-Functional Requirements

*(only new rows shown — NFR-1 through NFR-9 unchanged, carry over as-is)*

| ID Requirement Description Category |                                                                                                                                                                                                                                                                            |                              |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| **NFR-10** *(new)*                  | The system shall treat each uploaded transaction row as idempotent with respect to stock decrement — re-uploading the same file or an overlapping file shall not decrement stock twice for the same transaction.                                                           | Data Integrity               |
| **NFR-11** *(new)*                  | The system shall never display a negative current-stock value. If a computed value would be negative (e.g., due to an oversell or data-entry error), the system shall floor it at zero and flag the SKU for manual review rather than silently discarding the discrepancy. | Reliability / Data Integrity |

---

## REVISED SECTION 3.3 — Use Cases

*(UC-1 through UC-3 unchanged, carry over as-is. New UC-4 below.)*

### UC-4: Receive Purchase Order (New)

| Field Description |                                                                                                                                                                                                                                                                                                                |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Actor             | Owner/Manager                                                                                                                                                                                                                                                                                                  |
| Precondition      | An open purchase order (created via UC created from FR-10) exists for the SKU.                                                                                                                                                                                                                                 |
| Main Flow         | 1. User opens the purchase-order list and selects an open PO. 2. User marks it as "Received," confirming or editing the received quantity. 3. System increments the SKU's current stock by the received quantity (per FR-13). 4. System updates the PO status to "Received" and records the receipt timestamp. |
| Alternate Flow    | User marks the PO as "Cancelled" instead of received; stock is unaffected and PO status is set to "Cancelled."                                                                                                                                                                                                 |
| Postcondition     | Stock reflects the newly received inventory (if received), and the PO no longer appears in the open-orders list.                                                                                                                                                                                               |

---

## REVISED SECTION 3.5 — Testing-Relevant Requirement Notes

*(existing bullets unchanged; new subsection added below them)*

### 3.5.1 Current Stock Calculation Rule (New)

To make FR-5, FR-7, FR-8, FR-13, and NFR-11 jointly testable, current stock is defined precisely as:

```
current_stock (SKU, store) =
    opening_stock (set at product creation, FR-2)
  + Σ received_quantity for all POs with status = Received (FR-13)
  − Σ quantity_sold for all validated transactions (FR-5)
  , floored at 0 (NFR-11)
```

This formula is the basis for:

- **Boundary Value Analysis** on FR-8: stock exactly at, one above, and one below the reorder point.
- **Decision Table Testing** on FR-13: combinations of (PO status = Open/Received/Cancelled) × (received quantity = ordered / more / less than ordered).
- **Equivalence Class Testing** on FR-5/NFR-11: sale quantity less than, equal to, and greater than current stock (the last case exercises the floor-at-zero rule).

---

## REVISED SECTION 4.1 — Conceptual Data Model (Star Schema)

*(fact\_sales and dim\_date unchanged. Changes below.)*

### New Operational Table: `inventory_stock`

Current stock is **operational, fast-changing data** — it does not belong in a dimension table (`dim_product` is a slowly-changing dimension describing product attributes, not live quantities). It is tracked separately:

| Column Type Description |           |                                                                                    |
| ----------------------- | --------- | ---------------------------------------------------------------------------------- |
| inventory\_id           | INT (PK)  | Unique record identifier.                                                          |
| product\_key            | INT (FK)  | References dim\_product.                                                           |
| store\_key              | INT (FK)  | References dim\_store.                                                             |
| opening\_stock          | INT       | Stock quantity captured at product creation (FR-2).                                |
| current\_stock          | INT       | Live stock quantity, maintained per the formula in 3.5.1. Never negative (NFR-11). |
| last\_updated           | TIMESTAMP | Last time current\_stock changed (sale or PO receipt).                             |

### Revised Table: `purchase_orders`

| Column Type Description        |                      |                                                                                                             |
| ------------------------------ | -------------------- | ----------------------------------------------------------------------------------------------------------- |
| po\_id                         | BIGINT (PK)          | Unique purchase order identifier.                                                                           |
| product\_key                   | INT (FK)             | References dim\_product.                                                                                    |
| store\_key                     | INT (FK)             | References dim\_store.                                                                                      |
| quantity\_ordered              | INT                  | Quantity requested at PO creation (FR-10).                                                                  |
| **received\_quantity** *(new)* | INT (nullable)       | Actual quantity received (FR-13); null until receipt.                                                       |
| status                         | ENUM                 | **Open / Received / Cancelled** *(enum now explicit — was previously an undefined free-text/status field)*. |
| created\_by                    | INT (FK → users)     | User who created the PO.                                                                                    |
| created\_at                    | TIMESTAMP            | PO creation time.                                                                                           |
| **received\_at** *(new)*       | TIMESTAMP (nullable) | Time the PO was marked Received; null until receipt.                                                        |

All other tables (`dim_product`, `dim_store`, `forecast_results`, `reorder_alerts`, `users`) are unchanged.

---

## What I deliberately did NOT add

To keep this a minimal, internally-consistent fix rather than scope creep:

- **No manual stock-adjustment/correction feature** (e.g., for shrinkage or stocktake corrections) — genuinely useful in a real product, but not needed for internal consistency of the MVP loop (sale → decrement, PO receipt → increment). Worth flagging explicitly as future scope rather than silently omitting it.
- **No partial PO receipt across multiple deliveries** — FR-13 supports one receipt event per PO with an editable received quantity, which covers the common case without adding a multi-shipment tracking model.
- **No supplier-side status (e.g., "Sent," "Confirmed")** — Open → Received/Cancelled is the minimum lifecycle needed for the reorder loop to close; anything more granular is process detail the MVP doesn't need to model.
- **No automated forecast re-training trigger off of FR-14's accuracy metric** — computing and displaying MAPE is in scope; using it to auto-select or retrain models is future scope (already listed in Section 5).

These four are worth adding one line each to Section 5 (Future Scope) when you merge this back in.
