"""Generate an interactive HTML analytics dashboard with synthetic demo data.
Usage: python dashboard_generator.py
"""
from pathlib import Path
import numpy as np, pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

rng=np.random.default_rng(2026)
pairs=['USD/EUR','USD/INR','EUR/INR','GBP/USD','JPY/USD']
demo=pd.DataFrame({'pair':pairs,'store_mean':[.91,83.2,91.3,1.27,.0067],
'user_mean':[.915,83.5,91.0,1.265,.0068],'submissions':[124,98,80,61,45]})
demo['difference']=demo.user_mean-demo.store_mean
demo['relative_difference_pct']=demo.difference/demo.store_mean*100
corr=demo[['store_mean','user_mean','submissions','difference','relative_difference_pct']].corr()
dates=pd.date_range('2025-01-01',periods=180,freq='D')
series=pd.DataFrame({'date':dates,'rate':1.08+np.linspace(0,.025,len(dates))+rng.normal(0,.008,len(dates))})
series['rolling_mean_14']=series.rate.rolling(14).mean()
md=series.copy();md['lag1']=md.rate.shift(1);md['lag7']=md.rate.shift(7);md=md.dropna()
X=md[['lag1','lag7']];y=md.rate;split=int(len(md)*.8)
scores=[]
for name,m in [('Linear Regression',LinearRegression()),('Random Forest',RandomForestRegressor(n_estimators=100,random_state=42))]:
 m.fit(X.iloc[:split],y.iloc[:split]);p=m.predict(X.iloc[split:])
 scores.append({'model':name,'MAE':mean_absolute_error(y.iloc[split:],p),'RMSE':mean_squared_error(y.iloc[split:],p)**.5})
score=pd.DataFrame(scores)
figs=[
 px.bar(demo,x='pair',y=['store_mean','user_mean'],barmode='group',title='Store vs User rate comparison'),
 px.imshow(corr,text_auto='.2f',aspect='auto',title='Correlation heatmap'),
 px.line(series,x='date',y=['rate','rolling_mean_14'],title='Time series & 14-day rolling mean'),
 px.bar(score,x='model',y=['MAE','RMSE'],barmode='group',title='Demo model error comparison (lower is better)'),
 px.scatter_3d(demo,x='store_mean',y='user_mean',z='submissions',color='pair',size='submissions',title='Interactive 3D comparison')
]
html=['<h1>XchangeFinder Interactive Dashboard</h1><p>Illustrative synthetic data only; replace with verified historical observations.</p>']
for fig in figs: html.append(fig.to_html(full_html=False,include_plotlyjs='cdn'))
Path('XchangeFinder_analytics_dashboard.html').write_text('<html><head><meta charset="utf-8"></head><body>'+''.join(html)+'</body></html>',encoding='utf-8')
demo.to_csv('currency_pair_dashboard_demo.csv',index=False)
score.to_csv('model_accuracy_demo.csv',index=False)
print('Generated HTML dashboard and CSV summaries.')
