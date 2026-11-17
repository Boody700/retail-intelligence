"""Download, audit and analyze UCI Online Retail. Run from any directory."""
from pathlib import Path
import hashlib
import json
import sqlite3
import urllib.request
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'
NON_MERCHANDISE = {'POST', 'DOT', 'M', 'D', 'B', 'S', 'BANK CHARGES', 'AMAZONFEE', 'C2', 'CRUK'}


def clean(raw):
    """Sequential exclusion counts reconcile exactly to the source row count."""
    frame = raw.copy()
    audit = [{'step': 'Source rows', 'rows': len(frame)}]
    def exclude(label, mask):
        nonlocal frame
        count = int(mask.sum())
        audit.append({'step': label, 'excluded': count})
        frame = frame.loc[~mask].copy()
    exclude('Exact duplicate rows', frame.duplicated())
    for col in ['InvoiceNo', 'StockCode', 'Country']:
        frame[col] = frame[col].astype('string').str.strip()
    frame['InvoiceDate'] = pd.to_datetime(frame['InvoiceDate'], errors='coerce')
    for col in ['Quantity', 'UnitPrice']:
        frame[col] = pd.to_numeric(frame[col], errors='coerce')
    exclude('Missing or invalid transaction fields', frame[['InvoiceNo', 'StockCode', 'Country', 'InvoiceDate', 'Quantity', 'UnitPrice']].isna().any(axis=1) | ~np.isfinite(frame['Quantity']) | ~np.isfinite(frame['UnitPrice']))
    exclude('Cancelled invoices (C prefix)', frame['InvoiceNo'].str.upper().str.startswith('C'))
    exclude('Non-positive quantities', frame['Quantity'].le(0))
    exclude('Non-positive unit prices', frame['UnitPrice'].le(0))
    exclude('Service, adjustment and gift-voucher codes', frame['StockCode'].str.upper().isin(NON_MERCHANDISE) | frame['StockCode'].str.upper().str.startswith('GIFT'))
    # Store currency as integer pence to make reconciliation exact.
    frame['SalesPence'] = np.rint(frame['Quantity'] * frame['UnitPrice'] * 100).astype('int64')
    frame['Month'] = frame['InvoiceDate'].dt.strftime('%Y-%m')
    frame['CustomerID'] = pd.to_numeric(frame['CustomerID'], errors='coerce').astype('Int64')
    frame['Description'] = frame['Description'].fillna('Unnamed product').astype(str).str.strip()
    audit.append({'step': 'Retained merchandise lines', 'rows': len(frame)})
    return frame, audit


def records(frame):
    return json.loads(frame.to_json(orient='records'))


def customer_snapshot(frame, reference):
    known = frame.dropna(subset=['CustomerID'])
    customers = known.groupby('CustomerID').agg(last=('InvoiceDate', 'max'), frequency=('InvoiceNo', 'nunique'), sales=('SalesPence', 'sum'))
    customers['recency'] = (reference - customers['last'].dt.normalize()).dt.days
    # Assign country of last observed purchase; deterministic tie-break by source order.
    countries = known.sort_values('InvoiceDate', kind='stable').drop_duplicates('CustomerID', keep='last').set_index('CustomerID')['Country']
    customers['country'] = countries
    threshold = int(np.ceil(customers['sales'].quantile(.75)))
    r, f, m = customers['recency'], customers['frequency'], customers['sales']
    customers['segment'] = np.select([
        (r <= 30) & (f >= 3) & (m >= threshold),
        (r <= 90) & (f >= 3), r <= 30, r <= 90, f >= 3,
    ], ['Champions', 'Loyal', 'New & promising', 'Needs attention', 'At risk'], default='Hibernating')
    segments = customers.groupby(['country', 'segment']).agg(customers=('sales', 'size'), sales=('sales', 'sum'), median_recency=('recency', 'median'), median_frequency=('frequency', 'median')).reset_index()
    return customers, segments, threshold


def cohorts(frame, final_month=None):
    # The final calendar month is incomplete and excluded from retention analysis.
    final_month = frame['InvoiceDate'].max().to_period('M') if final_month is None else final_month
    known = frame.dropna(subset=['CustomerID']).copy()
    known['period'] = known['InvoiceDate'].dt.to_period('M')
    first = known.groupby('CustomerID')['period'].min()
    known['cohort'] = known['CustomerID'].map(first)
    known = known.loc[known['period'] < final_month].copy()
    known['age'] = known['period'].astype('int64') - known['cohort'].astype('int64')
    counts = known.groupby(['cohort', 'age'])['CustomerID'].nunique()
    result = []
    for cohort in sorted(known['cohort'].unique()):
        size = int(counts.loc[(cohort, 0)])
        available = final_month.ordinal - cohort.ordinal
        result.append({'month': str(cohort), 'size': size, 'rates': [round(int(counts.get((cohort, age), 0)) / size, 5) for age in range(available)]})
    return result


def build():
    (ROOT / 'data').mkdir(exist_ok=True)
    archive = ROOT / 'data/online-retail.zip'
    if not archive.exists():
        print('Downloading UCI dataset...', flush=True)
        urllib.request.urlretrieve(SOURCE, archive)
    print('Reading original workbook...', flush=True)
    with zipfile.ZipFile(archive) as z:
        with z.open('Online Retail.xlsx') as source:
            raw = pd.read_excel(source, engine='openpyxl')
    frame, audit = clean(raw)
    reference = frame['InvoiceDate'].max().normalize() + pd.Timedelta(days=1)
    customers, segments, threshold = customer_snapshot(frame, reference)
    # Invoice-level sufficient statistics allow filters without shipping customer IDs.
    invoices = frame.groupby(['Country', 'Month', 'InvoiceNo'], sort=True).agg(sales=('SalesPence', 'sum'), units=('Quantity', 'sum'), customer=('CustomerID', 'first')).reset_index()
    # Public payload uses opaque sequential customer keys only for deduplication.
    # They are not original dataset identifiers and have no personal attributes.
    keys = {key: index + 1 for index, key in enumerate(sorted(frame['CustomerID'].dropna().unique()))}
    invoice_rows = [[r.Country, r.Month, int(r.sales), int(r.units), keys.get(r.customer, 0)] for r in invoices.itertuples()]
    names = frame.groupby('StockCode')['Description'].agg(lambda x: x.value_counts().index[0])
    products = frame.groupby(['Country', 'StockCode']).agg(sales=('SalesPence', 'sum'), units=('Quantity', 'sum'), orders=('InvoiceNo', 'nunique')).reset_index()
    products['name'] = products['StockCode'].map(names)
    products = products.rename(columns={'Country': 'country', 'StockCode': 'sku'})
    product_months = frame.groupby(['Country', 'Month', 'StockCode']).agg(sales=('SalesPence', 'sum'), units=('Quantity', 'sum'), orders=('InvoiceNo', 'nunique')).reset_index()
    compact_products = [[r.Country, r.Month, r.StockCode, int(r.sales), int(r.units), int(r.orders)] for r in product_months.itertuples()]
    cohort_markets = {}
    known = frame.dropna(subset=['CustomerID'])
    for country in sorted(customers['country'].unique()):
        members = customers.index[customers['country'].eq(country)]
        cohort_markets[country] = cohorts(known.loc[known['CustomerID'].isin(members)], frame['InvoiceDate'].max().to_period('M'))
    conn = sqlite3.connect(ROOT / 'data/retail.sqlite')
    frame.to_sql('sales', conn, if_exists='replace', index=False)
    conn.execute('CREATE INDEX IF NOT EXISTS ix_sales_invoice ON sales(InvoiceNo)')
    conn.execute('CREATE INDEX IF NOT EXISTS ix_sales_customer ON sales(CustomerID)')
    conn.commit()
    assert conn.execute('SELECT SUM(SalesPence) FROM sales').fetchone()[0] == int(frame['SalesPence'].sum())
    conn.close()
    partial = str(frame['InvoiceDate'].max().to_period('M'))
    monthly = frame.groupby('Month')['SalesPence'].sum()
    complete = monthly.loc[monthly.index != partial]
    uk_sales = int(frame.loc[frame['Country'].eq('United Kingdom'), 'SalesPence'].sum())
    repeat = int(customers['frequency'].gt(1).sum())
    quality = {
        'source_rows': len(raw), 'retained_rows': len(frame), 'audit': audit,
        'missing_customer_rows': int(frame['CustomerID'].isna().sum()),
        'identified_sales': int(frame.loc[frame['CustomerID'].notna(), 'SalesPence'].sum()),
        'sales': int(frame['SalesPence'].sum()), 'orders': int(frame['InvoiceNo'].nunique()),
        'customers': len(customers), 'repeat_customers': repeat,
        'units': int(frame['Quantity'].sum()), 'countries': int(frame['Country'].nunique()),
        'source_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'start': frame['InvoiceDate'].min().isoformat(), 'end': frame['InvoiceDate'].max().isoformat(),
        'reference': reference.strftime('%Y-%m-%d'), 'partial_month': partial,
        'high_value_threshold_pence': threshold,
        'uk_sales_share': round(uk_sales / int(frame['SalesPence'].sum()), 6),
        'best_complete_month': str(complete.idxmax()),
        'best_complete_month_sales': int(complete.max()),
    }
    payload = {'meta': quality, 'invoices': invoice_rows, 'segments': records(segments), 'products': records(products), 'productMonths': compact_products, 'cohorts': cohorts(frame), 'cohortMarkets': cohort_markets}
    assert sum(row[2] for row in invoice_rows) == quality['sales']
    assert len(invoice_rows) == quality['orders'], 'An invoice spans multiple market/month groups'
    assert int(products['sales'].sum()) == quality['sales']
    assert sum(row[3] for row in compact_products) == quality['sales']
    assert int(segments['customers'].sum()) == quality['customers']
    assert sum(s.get('excluded', 0) for s in audit) + len(frame) == len(raw)
    (ROOT / 'dist/data.js').write_text('window.RETAIL_DATA=' + json.dumps(payload, separators=(',', ':'), allow_nan=False) + ';\n', encoding='utf-8')
    (ROOT / 'data/quality.json').write_text(json.dumps(quality, indent=2), encoding='utf-8')
    pd.DataFrame(audit).to_csv(ROOT / 'data/cleaning-audit.csv', index=False)
    segments.to_csv(ROOT / 'data/customer-segments.csv', index=False)
    report = f'''# Retail Intelligence — analysis findings

Generated from the full UCI Online Retail workbook. Currency: GBP.

- Source lines: {len(raw):,}; retained merchandise lines: {len(frame):,}.
- Positive merchandise sales: £{quality['sales']/100:,.2f} across {quality['orders']:,} invoices.
- Identified purchasing customers: {len(customers):,}; {repeat/len(customers):.1%} made more than one purchase during the observed period.
- United Kingdom share of merchandise sales: {quality['uk_sales_share']:.1%}.
- Highest-sales complete month: {quality['best_complete_month']} (£{quality['best_complete_month_sales']/100:,.2f}).
- {quality['missing_customer_rows']:,} retained lines have no customer ID. Their sales are included in sales KPIs but excluded from customer segmentation and cohort analysis.

## Decisions this analysis supports

1. Prioritize UK merchandising experiments, while testing country-level opportunities rather than assuming the same behavior everywhere.
2. Test retention campaigns for the rule-based At risk segment. Measure incremental repeat purchase through a randomized holdout; this analysis does not estimate campaign uplift.
3. Use product rankings as a starting point for stock planning. Sales alone do not establish profitability, and no inventory or cost data is available.

## Limits

This is historical data from one gift retailer, including wholesale buyers, not a picture of today's market. Sales exclude cancellations, non-positive quantities/prices, listed adjustment/service codes and gift vouchers; they are not net revenue or profit. RFM labels are descriptive rules, not predictions. December 2011 ends on December 9 and must not be compared as a full month. First purchase means first observed purchase, not necessarily customer acquisition. Cohorts exclude December 2011 and measure repeat activity in a month, not survival or causal retention. High spenders and large orders are retained. Country is a customer address field, not a shipping destination guarantee.
'''
    (ROOT / 'docs/findings.md').write_text(report, encoding='utf-8')
    print(json.dumps(quality, indent=2), flush=True)


if __name__ == '__main__':
    build()
