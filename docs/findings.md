# Retail Intelligence — analysis findings

Generated from the full UCI Online Retail workbook. Currency: GBP.

- Source lines: 541,909; retained merchandise lines: 522,540.
- Positive merchandise sales: £10,247,219.32 across 19,773 invoices.
- Identified purchasing customers: 4,334; 65.3% made more than one purchase during the observed period.
- United Kingdom share of merchandise sales: 85.1%.
- Highest-sales complete month: 2011-11 (£1,452,115.98).
- 131,387 retained lines have no customer ID. Their sales are included in sales KPIs but excluded from customer segmentation and cohort analysis.

## Decisions this analysis supports

1. Prioritize UK merchandising experiments, while testing country-level opportunities rather than assuming the same behavior everywhere.
2. Test retention campaigns for the rule-based At risk segment. Measure incremental repeat purchase through a randomized holdout; this analysis does not estimate campaign uplift.
3. Use product rankings as a starting point for stock planning. Sales alone do not establish profitability, and no inventory or cost data is available.

## Limits

This is historical data from one gift retailer, including wholesale buyers, not a picture of today's market. Sales exclude cancellations, non-positive quantities/prices, listed adjustment/service codes and gift vouchers; they are not net revenue or profit. RFM labels are descriptive rules, not predictions. December 2011 ends on December 9 and must not be compared as a full month. First purchase means first observed purchase, not necessarily customer acquisition. Cohorts exclude December 2011 and measure repeat activity in a month, not survival or causal retention. High spenders and large orders are retained. Country is a customer address field, not a shipping destination guarantee.
