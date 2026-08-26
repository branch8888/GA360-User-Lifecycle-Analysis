import pandas as pd
import numpy as np
import os

RAW = 'data/raw/ga360/ga360_sessions.csv'
OUT = 'outputs/tables/user_day_kpi.csv'

cols = ['fullVisitorId', 'date', 'visitId', 'transactions', 'transactionRevenue', 'bounces']

print('loading raw sessions (selected columns)...')
df = pd.read_csv(RAW, usecols=cols,
                 dtype={'fullVisitorId': 'str', 'date': 'str'},
                 encoding='utf-8-sig', low_memory=False)
print('raw rows:', len(df))

# --- replicate notebook caliber ---
df['analysis_date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce').dt.normalize()
df['transactions'] = pd.to_numeric(df['transactions'], errors='coerce').fillna(0.0)
df['revenue_usd'] = pd.to_numeric(df['transactionRevenue'], errors='coerce').fillna(0.0) / 1_000_000.0
df['is_bounce'] = (pd.to_numeric(df['bounces'], errors='coerce').fillna(0.0) == 1).astype(int)
df['has_transaction'] = (df['transactions'] > 0).astype(int)

# --- user x date grain ---
g = df.groupby(['analysis_date', 'fullVisitorId'], as_index=False).agg(
    sessions=('visitId', 'size'),
    purchase_sessions=('has_transaction', 'sum'),
    transactions=('transactions', 'sum'),
    revenue_usd=('revenue_usd', 'sum'),
    bounce_sessions=('is_bounce', 'sum'),
)
# ensure transaction fields are integral-looking but keep as numeric for SUM
g['purchase_sessions'] = g['purchase_sessions'].astype(int)
g['transactions'] = g['transactions'].astype(int)
g['bounce_sessions'] = g['bounce_sessions'].astype(int)

# sort by date then user
g = g.sort_values(['analysis_date', 'fullVisitorId']).reset_index(drop=True)

# write with clean YYYY-MM-DD date string (Tableau-friendly)
g['analysis_date'] = g['analysis_date'].dt.strftime('%Y-%m-%d')
g.to_csv(OUT, index=False, encoding='utf-8-sig')
print('\nsaved:', OUT, '| rows:', len(g))

# --- verification against overall_metrics / daily_performance ---
print('\n=== calibration check vs overall_metrics.csv ===')
print('distinct users (UV)      :', g['fullVisitorId'].nunique(),   '(expect 714167)')
print('total sessions (SUM)     :', g['sessions'].sum(),            '(expect 903653)')
print('purchase sessions        :', g['purchase_sessions'].sum(),   '(expect 11552)')
print('transactions             :', g['transactions'].sum(),        '(expect 12115)')
print('revenue_usd              :', round(g['revenue_usd'].sum(), 2), '(expect 1540071.24)')
print('bounce sessions          :', g['bounce_sessions'].sum(),      '(expect 450630)')
print('bounce rate              :', round(g['bounce_sessions'].sum()/g['sessions'].sum(), 5), '(expect 0.49868)')
print('distinct dates           :', g['analysis_date'].nunique(),    '(expect 366/367)')
print('\nhead of user_day_kpi.csv:')
print(g.head(5).to_string(index=False))
