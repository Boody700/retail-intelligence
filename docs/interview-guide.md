# Explain the project in an interview

## A 45-second walkthrough

“This is a historical retail analytics project using the full UCI Online Retail dataset. The goal was to explain which products and markets drive merchandise sales and how customers purchase again. The Python pipeline cleans and audits 541,909 lines, writes a SQLite database, and produces the dashboard's aggregates. I separated sales and customer populations because some purchases have no customer ID. I added transparent RFM segments, a cohort repeat-activity view, explicit treatment of the incomplete final month, and reconciliation checks across Python, SQL and the interface. The result supports questions and experiments; it does not claim profit or campaign uplift.”

Use this only after you can run and explain the code. Be clear about the choices and modifications you understand.

## Questions to prepare

**Why no machine learning model?** The business questions are descriptive. Segmentation and cohort analysis answer them directly. A churn model would first require a specific prediction date, a future outcome window, leakage controls and a useful action.

**Why not just remove missing customer IDs?** That would throw away legitimate sales. Sales analysis retains them; customer analysis excludes them. The dashboard displays identified-sales coverage.

**Why are sales different from many Online Retail tutorials?** The project uses its own explicit merchandise-only definition, drops exact duplicates and excludes known adjustment/service/voucher codes. Comparisons must use the same population and definitions.

**How do you avoid double-counting customers?** The dashboard counts unique opaque buyer keys across selected invoices and months, rather than adding monthly distinct counts. Invoice frequency is based on distinct invoices, not transaction lines.

**Why is December 2011 lower?** Only December 1–9 is observed. It is flagged in the sales chart and excluded from cohort repeat-activity periods. No full-month growth comparison is claimed.

**What is the strongest finding?** Strong market concentration: 85.1% of retained merchandise sales are associated with UK customers. It motivates additional analysis, not an unsupported recommendation to abandon other markets.

**How would you prove a win-back campaign works?** Randomize eligible buyers into treatment/holdout, define the outcome and time window beforehand, evaluate incremental repeat purchasing, and include campaign cost and margins when available.

**What would you improve with more data?** Match returns to purchases for net sales, add costs and inventory for commercial decisions, include earlier history to reduce left-censoring, and add validated marketing exposure for experimentation.

## Demo sequence

1. Overview: explain the sales definition; select a market and narrow the months.
2. Show how identified buyers differ from total orders and sales coverage.
3. Customers: explain one RFM rule and one cohort row, including blank future cells.
4. Products: search a stock code, change ranking, export the results.
5. Methodology: show the cleaning waterfall and source attribution.
6. Open the Python pipeline and one SQL query; explain the associated check.

## Portfolio and résumé wording

After studying and adapting the project, you can use wording such as:

“Developed a reproducible retail analytics pipeline and interactive dashboard using Python, SQL and JavaScript; audited 541K transaction lines, analyzed 4.3K identified buyers, and reconciled sales metrics across line, invoice and product aggregations.”

Do not add a claim of revenue growth, improved retention, model accuracy or real-client impact: none was measured here.
