# Data dictionary and analysis contract

Source: Chen (2015), UCI Online Retail, https://doi.org/10.24432/C5BW33, CC BY 4.0.

| Field | Meaning and treatment |
|---|---|
| InvoiceNo | Nominal purchase invoice identifier; C-prefixed invoices indicate cancellations and are excluded. |
| StockCode | Stable product identifier, normalized to string. Product names can change. |
| Description | Product description. Missing descriptions become “Unnamed product”; displayed names use the most common name per stock code. |
| Quantity | Item quantity; only finite, positive quantities retained. |
| InvoiceDate | Observed transaction timestamp; parsed without timezone conversion. |
| UnitPrice | Unit price in GBP; only finite, positive prices retained. |
| CustomerID | Dataset customer identifier; missing values are retained in sales but excluded from customer analysis. |
| Country | Recorded customer country label; not verified shipping destination or customer nationality. |
| SalesPence | Derived line sales: round(Quantity × UnitPrice × 100), integer pence. |
| Month | Invoice calendar month formatted YYYY-MM. |

## Exclusions

Applied in this exact order: exact original-row duplicates; invalid/missing invoice, stock code, country, date, quantity or price; C-prefixed cancellations; non-positive quantities; non-positive prices; excluded non-merchandise stock codes.

The explicit code set is `POST`, `DOT`, `M`, `D`, `B`, `S`, `BANK CHARGES`, `AMAZONFEE`, `C2`, `CRUK`, plus codes starting with `GIFT`. These correspond to known service, manual/adjustment, charge or voucher entries. The list is a documented analytical choice, not a claim that every unusual entry has been perfectly classified. No arbitrary quantity or price outlier cutoff is applied.

Exact duplicate removal assumes identical repeated records represent duplicate lines; without a source line identifier, genuine identical repeated lines cannot be distinguished with certainty.

## Filter scopes

- Overview market/date filters apply to KPIs, monthly chart, geographic ranking, repeat-purchase insight and monthly export. The product preview follows the same market and date range.
- Customer market selection applies to the full-period segment snapshot and cohort chart. Customers are assigned to their last observed purchase country. The cohort chart follows the same last-observed-country assignment.
- Products have their own market and date selectors. Search and sorting apply to the table and product export. KPI cards describe the selected market and period's catalogue, not just search matches.
- Methodology export returns the sequential cleaning audit.

## Export contract

Sales values are decimal GBP; raw calculations use integer pence. CSV downloads use quoted UTF-8 values with a BOM for common spreadsheet compatibility. Cells beginning with formula-like characters are prefixed with an apostrophe. Product order appearances must not be summed to obtain basket counts.

## Browser payload

`invoices`: `[country, month, sales_pence, units, opaque_customer_key]`; key `0` means unidentified. Nonzero keys are sequential replacements, not original CustomerID values. They support exact deduplication of buyers over arbitrary selected month ranges. They may still be linkable to the original public data and are not claimed to provide formal anonymization.

`productMonths`: compact country/month/SKU sums that reconcile to filtered invoice totals.

`cohortMarkets`: cohort repeat-activity tables by last-observed customer country, using the global final-month cutoff.

`products`: country/SKU totals with units, invoice appearances and the most common description.

`segments`: last-observed customer country × segment summaries, including count, total sales and descriptive medians.

`cohorts`: global first-observed purchase cohorts and complete-month repeat-activity rates; no future rates are fabricated.

`meta`: population counts, source checksum, observation dates, RFM threshold and audit. Rebuilding the project recalculates every derived output from the source archive.
