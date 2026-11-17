"""Export independent analytical figures from SQLite and the cohort payload."""
from pathlib import Path
import json
import sqlite3
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'retail-intelligence-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#53624d','text.color':'#19382d','figure.facecolor':'#f7f8f3','axes.facecolor':'#f7f8f3','savefig.facecolor':'#f7f8f3'})
    with sqlite3.connect(ROOT / 'data/retail.sqlite') as conn:
        monthly = pd.read_sql_query('SELECT Month, SUM(SalesPence)/100.0 AS Sales FROM sales GROUP BY Month ORDER BY Month', conn)
    fig, ax = plt.subplots(figsize=(12,5.2),layout='constrained')
    colors = ['#749d62'] * len(monthly)
    colors[-2]='#254f3b'
    colors[-1]='#d4dcc6'
    bars=ax.bar(monthly['Month'],monthly['Sales'],color=colors,width=.64,zorder=3)
    bars[-1].set_hatch('//')
    bars[-1].set_edgecolor('#83966b')
    ax.set_title('Merchandise sales peak in November; final December is partial',loc='left',pad=18,fontsize=14)
    ax.set_ylabel('Positive merchandise sales (GBP)')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'£{x/1e6:.1f}m'))
    ax.tick_params(axis='x',rotation=45,labelsize=9)
    ax.grid(axis='y',color='#dfe5d7',zorder=0)
    fig.supxlabel('Source: Chen (2015), UCI Online Retail / CC BY 4.0. December 2011 includes December 1–9 only. Not net revenue.',fontsize=8)
    fig.savefig(out/'monthly-sales.png',dpi=180)
    plt.close(fig)
    payload=json.loads((ROOT/'dist/data.js').read_text(encoding='utf-8').removeprefix('window.RETAIL_DATA=').strip().removesuffix(';'))
    cohorts=payload['cohorts']
    heat=np.full((len(cohorts),12),np.nan)
    for index,c in enumerate(cohorts):
        heat[index,:len(c['rates'])]=c['rates']
    fig,ax=plt.subplots(figsize=(12,7),layout='constrained')
    cmap=plt.get_cmap('YlGn').copy()
    cmap.set_bad('#ebeee5')
    im=ax.imshow(heat,cmap=cmap,vmin=0,vmax=1,aspect='auto')
    for i in range(heat.shape[0]):
        for j in range(12):
            if np.isfinite(heat[i,j]):
                ax.text(j,i,f'{heat[i,j]:.0%}',ha='center',va='center',fontsize=8,color='white' if heat[i,j]>.6 else '#244534')
    ax.set_xticks(range(12),[f'M{i}' for i in range(12)])
    ax.set_yticks(range(len(cohorts)),[c['month']+f" (n={c['size']:,})" for c in cohorts])
    ax.set_xlabel('Months after first observed purchase')
    ax.set_title('Repeat purchase activity by first-observed cohort',loc='left',pad=18,fontsize=14)
    fig.colorbar(im,ax=ax,format=FuncFormatter(lambda x,_:f'{x:.0%}'),shrink=.75,label='Share purchasing in month')
    fig.supxlabel('Global identified buyers. Final partial month excluded. Gray cells are unobserved. Source: UCI Online Retail / CC BY 4.0.',fontsize=8)
    fig.savefig(out/'cohort-repeat-activity.png',dpi=180)
    plt.close(fig)
    print('Created reports/monthly-sales.png and reports/cohort-repeat-activity.png')


if __name__ == '__main__':
    main()
