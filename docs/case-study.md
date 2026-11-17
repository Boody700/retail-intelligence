# Retail Intelligence: from transactions to customer decisions

## The problem

A retailer can have hundreds of thousands of transaction lines and still struggle to answer basic commercial questions: which products drive sales, which markets matter, and whether customers buy again. This project creates a small, auditable analytical product that connects these questions to evidence.

The source is the UCI Online Retail dataset: a UK-based gift retailer with transactions from December 2010 through December 9, 2011, including wholesale customers. The work is a historical portfolio case study, not an engagement for a real client.

## The approach

I used a Python pipeline to download and read the full workbook, inspect data quality, and create a reproducible cleaning audit. Every exclusion is applied sequentially so the original line count equals retained lines plus exclusions. This prevents overlapping counts from making the audit impossible to reconcile.

The analytical sales definition deliberately includes positive merchandise purchases only. Cancelled invoices, non-positive quantities/prices, manual adjustments, service codes and gift vouchers are excluded. There is no attempt to match returns back to purchases, so these totals are not net revenue. The exclusion set and its limitations are documented rather than hidden behind a generic “cleaned data” label.

Missing customer IDs require two populations. Those lines remain in sales analysis, but are excluded from customer segmentation and cohort repeat activity. This preserves sales coverage without inventing customer identities. I store line sales in integer pence so Python, SQLite and browser totals reconcile exactly.

SQL queries answer the headline performance, market concentration, product-ranking, RFM and repeat-activity questions. A dependency-light static dashboard exposes the results with explicit filter scopes and CSV exports.

## Customer analysis

RFM measures recency from December 10, 2011; frequency counts distinct purchase invoices; monetary value sums retained merchandise sales. Six mutually exclusive segments are assigned through ordered, documented rules. Frequent, recent, high-spend buyers become Champions; frequent buyers inactive for over 90 days become At risk. These are descriptive labels, not trained predictions or proof that a customer will leave.

The cohort view groups buyers by first observed purchase month. It measures the share buying in each later month, including genuine zero-activity cells. Future periods are unobserved and stay blank. December 2011 is excluded because it is incomplete. A first observed purchase does not establish true acquisition, particularly for customers already active before the dataset begins.

## What the analysis shows

After cleaning, 522,540 merchandise lines contribute £10,247,219.32 across 19,773 purchase invoices. There are 4,334 identified buyers, of whom 2,829 (65.3%) purchased on more than one invoice during the observed period. The UK accounts for 85.1% of merchandise sales. November 2011 is the highest-sales complete month, at £1,452,115.98.

These findings support investigating market concentration and repeat purchase behavior. They do not establish profitability, a seasonal causal mechanism, marketing effectiveness or future growth.

## Recommended next step

Test a reactivation message for frequent buyers whose last purchase was over 90 days ago. Randomly assign an eligible group to treatment or holdout before the campaign. Prespecify a repeat-purchase outcome and observation window; compare incremental purchases and contribution margin when cost data becomes available. This project does not claim that such an experiment was run or that it generated uplift.

For product planning, examine the highest-selling stock codes alongside stock availability, lead times and contribution margin. Sales rank alone does not justify a purchasing decision.

## Engineering and validation

The dashboard serves precomputed aggregations and invoice sufficient statistics rather than the full workbook. It supports market/month filtering, buyer deduplication across periods, product search, ranking, pagination and context-specific exports. Original dataset customer IDs stay out of the browser payload.

Tests cover cleaning behavior, missing IDs, line-value arithmetic, invoice-based frequency, segment boundary rules, cohort censoring and reconciliation among raw lines, invoice summaries, products, segments, SQL and UI payloads. The refined dashboard was verified in a real browser at desktop and phone widths, including date/market filters, country cohorts, product search and a native CSV download. No console errors were observed. A full assistive-technology audit remains outside the verification performed.

## What this project demonstrates

Data cleaning with an audit trail, SQL aggregation and window functions, business metric design, customer analytics, cohort analysis, cautious interpretation, reproducible Python work and delivery of an interactive analytical product.
