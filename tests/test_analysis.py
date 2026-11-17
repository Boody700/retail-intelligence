"""Behavior and real-data reconciliation tests; no network required."""
from pathlib import Path
import json
import sqlite3
import sys
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_data import clean, cohorts, customer_snapshot


def line(invoice='100001', date='2011-01-01', customer=1, quantity=2, price=1.25, sku='12345'):
    return dict(InvoiceNo=invoice, InvoiceDate=date, CustomerID=customer, Quantity=quantity, UnitPrice=price, StockCode=sku, Country='United Kingdom', Description='Test product')


class CleaningTests(unittest.TestCase):
    def test_waterfall_and_anonymous_sales(self):
        valid = line()
        rows = [valid, valid.copy(), line(invoice='C100002'), line(quantity=-1), line(price=0), line(sku='POST'), line(customer=None, invoice='100003'), line(date='invalid')]
        cleaned, audit = clean(pd.DataFrame(rows))
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(cleaned['SalesPence'].sum(), 500)
        self.assertEqual(cleaned['CustomerID'].isna().sum(), 1)
        self.assertEqual(sum(a.get('excluded', 0) for a in audit)+len(cleaned), len(rows))

    def test_quantity_not_line_count_drives_sales(self):
        cleaned, _ = clean(pd.DataFrame([line(quantity=3, price=1.99)]))
        self.assertEqual(cleaned['SalesPence'].iloc[0], 597)

    def test_frequency_counts_invoices_not_line_items(self):
        frame, _ = clean(pd.DataFrame([line(sku='12345'), line(sku='12346')]))
        customers, _, _ = customer_snapshot(frame, pd.Timestamp('2011-01-02'))
        self.assertEqual(customers['frequency'].iloc[0], 1)
        self.assertEqual(customers['recency'].iloc[0], 1)

    def test_cohorts_keep_zero_and_unobserved_distinct(self):
        frame, _ = clean(pd.DataFrame([line(date='2011-01-01'), line(invoice='100002',date='2011-03-01'),line(invoice='100003',date='2011-04-02')]))
        result = cohorts(frame)
        self.assertEqual(result, [{'month':'2011-01','size':1,'rates':[1.0,0.0,1.0]}])

    def test_rfm_boundary_priority_and_exhaustiveness(self):
        rows=[]
        for customer, age, frequency in [(1,30,3),(2,90,3),(3,91,3),(4,30,1),(5,90,1),(6,91,1)]:
            for order in range(frequency):
                rows.append(line(invoice=str(customer*100+order), date=str((pd.Timestamp('2011-12-10')-pd.Timedelta(days=age)).date()),customer=customer))
        frame,_=clean(pd.DataFrame(rows))
        customers,segments,_=customer_snapshot(frame,pd.Timestamp('2011-12-10'))
        self.assertEqual(customers['segment'].tolist(),['Champions','Loyal','At risk','New & promising','Needs attention','Hibernating'])
        self.assertEqual(segments['customers'].sum(),6)


class FullDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / 'dist/data.js').exists():
            raise unittest.SkipTest('Run scripts/build_data.py to enable full-dataset checks')
        cls.data=json.loads((ROOT / 'dist/data.js').read_text(encoding='utf-8').removeprefix('window.RETAIL_DATA=').strip().removesuffix(';'))

    def test_waterfall_reconciles(self):
        q=self.data['meta']
        self.assertEqual(q['source_rows'],541909)
        self.assertEqual(q['retained_rows']+sum(a.get('excluded',0) for a in q['audit']),q['source_rows'])

    def test_all_sales_views_reconcile_to_pence(self):
        d=self.data
        self.assertEqual(sum(r[2] for r in d['invoices']),d['meta']['sales'])
        self.assertEqual(sum(r['sales'] for r in d['products']),d['meta']['sales'])
        self.assertEqual(len(d['invoices']),d['meta']['orders'])

    def test_customer_coverage_and_segments(self):
        d=self.data
        ids={r[4] for r in d['invoices'] if r[4]}
        self.assertEqual(len(ids),d['meta']['customers'])
        self.assertEqual(sum(r['customers'] for r in d['segments']),len(ids))
        self.assertEqual(sum(r['sales'] for r in d['segments']),d['meta']['identified_sales'])
        self.assertEqual(sum(r[2] for r in d['invoices'] if r[4]),d['meta']['identified_sales'])

    def test_sql_agrees_and_queries_execute(self):
        database=ROOT/'data/retail.sqlite'
        self.assertTrue(database.exists(),'Build local SQLite database first')
        with sqlite3.connect(database) as conn:
            self.assertEqual(conn.execute('SELECT SUM(SalesPence), COUNT(*) FROM sales').fetchone(),(self.data['meta']['sales'],self.data['meta']['retained_rows']))
            conn.executescript((ROOT/'sql/analysis.sql').read_text(encoding='utf-8'))

    def test_no_original_customer_ids_in_payload(self):
        self.assertNotIn('CustomerID',json.dumps(self.data))
        self.assertEqual(min(r[4] for r in self.data['invoices']),0)

    def test_cohort_bounds_and_observation_window(self):
        for cohort in self.data['cohorts']:
            self.assertLess(cohort['month'],self.data['meta']['partial_month'])
            self.assertEqual(cohort['rates'][0],1)
            self.assertTrue(all(0<=r<=1 for r in cohort['rates']))

    def test_monthly_products_follow_invoice_filters(self):
        for country,start,end in [('France','2011-02','2011-04'),('United Kingdom','2010-12','2011-11')]:
            invoices=sum(r[2] for r in self.data['invoices'] if r[0]==country and start<=r[1]<=end)
            products=sum(r[3] for r in self.data['productMonths'] if r[0]==country and start<=r[1]<=end)
            self.assertEqual(invoices,products)

    def test_market_cohort_sizes_reconcile(self):
        for cohort in self.data['cohorts']:
            market_total=sum(c['size'] for rows in self.data['cohortMarkets'].values() for c in rows if c['month']==cohort['month'])
            self.assertEqual(market_total,cohort['size'])

if __name__=='__main__':
    unittest.main()
