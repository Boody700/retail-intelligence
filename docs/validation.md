# Validation record

## Completed

- Full source workbook processed: 541,909 original rows; 522,540 retained merchandise lines.
- Original archive SHA-256 recorded in `data/quality.json` and the dashboard.
- Sequential exclusions plus retained lines reconcile to the original population.
- Sales reconcile in integer pence across retained lines, invoice summaries, product summaries, SQLite and the dashboard payload.
- Customer counts and identified sales reconcile across invoices and segment summaries.
- No original `CustomerID` field is included in the browser payload.
- Customer frequencies count invoices rather than line items; customer segment boundary priority is checked at 30/90/91 days.
- Cohort checks distinguish zero activity from unobserved future months and exclude the incomplete final month.
- All seven SQL queries execute against the generated SQLite database.
- **13 Python unit/integration checks pass** with `python -m unittest discover -s tests -v`.
- JavaScript syntax checked with `node --check dist/app.js`.
- Dashboard logic harness passes all routes, country/date filtering, inverted-range correction, product search/sorting/pagination, empty results and CSV exports.
- Local HTTP server returns 200 and serves only the deployable `dist/` directory.
- Both exported report figures were generated and visually inspected for labels, readability and incomplete-period treatment.

## Real-browser verification

Desktop and phone layouts were inspected at 1440 × 1000 and 390 × 844. Market/date filters, market-specific cohort counts, product search and native CSV download were exercised. The downloaded France / February–April 2011 product CSV was inspected. No browser console warnings or errors were observed during these checks. A dashboard screenshot is included in reports/dashboard-desktop.jpg.

Keyboard-accessible form controls, visible focus styles, polite status announcements and a skip link are implemented. A full screen-reader/assistive-technology audit has not been performed. Exported report figures are independent analysis plots, not dashboard screenshots.

## Suggested real-browser review

1. Open Overview at desktop and phone widths; verify that controls, cards and chart labels fit.
2. Change a market and month range; verify matching metrics and monthly export.
3. Navigate all pages using keyboard links and focus indicators.
4. Search a product, sort, paginate and open the exported CSV in a spreadsheet app.
5. Confirm that the cohort table scrolls horizontally and unobserved cells remain blank.
6. Confirm that source and methodology links are reachable and readable.
