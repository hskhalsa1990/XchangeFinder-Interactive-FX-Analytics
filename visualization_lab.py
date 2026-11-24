"""Generate demonstration charts/tables for XchangeFinder using synthetic data.
Run: python visualization_lab.py
Outputs PNG charts and a CSV comparison table in the current directory.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

rng=np.random.default_rng(42)
df=pd.DataFrame({
 "pair":["USD/EUR","USD/INR","EUR/INR","GBP/USD","JPY/USD"],
 "store_mean":[.91,83.2,91.3,1.27,.0067],
 "user_mean":[.915,83.5,91.0,1.265,.0068],
 "submissions":[124,98,80,61,45]})
df["difference"]=df.user_mean-df.store_mean
df["relative_difference_pct"]=df.difference/df.store_mean*100
df.to_csv("currency_pair_comparison_demo.csv",index=False)
# comparison
x=np.arange(len(df)); w=.36
fig,ax=plt.subplots(figsize=(10,5))
ax.bar(x-w/2,df.store_mean,w,label="Store average")
ax.bar(x+w/2,df.user_mean,w,label="User average")
ax.set_xticks(x,df.pair);ax.set_title("Store vs User averages (synthetic demo)")
ax.legend();ax.grid(axis="y",alpha=.25);fig.tight_layout();fig.savefig("comparison_chart.png",dpi=160);plt.close(fig)
# difference charts
fig,axes=plt.subplots(1,2,figsize=(11,4))
axes[0].bar(df.pair,df.difference);axes[0].set_title("Absolute difference")
axes[1].bar(df.pair,df.relative_difference_pct);axes[1].set_title("Relative difference (%)")
for a in axes:a.tick_params(axis="x",rotation=30);a.grid(axis="y",alpha=.25)
fig.tight_layout();fig.savefig("difference_charts.png",dpi=160);plt.close(fig)
# volume
fig,ax=plt.subplots(figsize=(8,4));ax.barh(df.pair,df.submissions);ax.set_title("Submission volume (demo)")
ax.grid(axis="x",alpha=.25);fig.tight_layout();fig.savefig("submission_volume.png",dpi=160);plt.close(fig)
# 3d grouped
from mpl_toolkits.mplot3d import Axes3D
fig=plt.figure(figsize=(10,6));ax=fig.add_subplot(111,projection="3d")
xs=np.arange(len(df))
ax.bar3d(xs-.15,np.zeros(len(df)),np.zeros(len(df)),.3,np.ones(len(df)),df.store_mean,alpha=.8)
ax.bar3d(xs+.15,np.ones(len(df)),np.zeros(len(df)),.3,np.ones(len(df)),df.user_mean,alpha=.8)
ax.set_xticks(xs,df.pair);ax.set_yticks([.5,1.5],["Store","User"]);ax.set_zlabel("Average rate")
ax.set_title("3D comparison (synthetic demo)");fig.tight_layout();fig.savefig("3d_rate_comparison.png",dpi=160);plt.close(fig)
# 3d scatter
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection="3d")
ax.scatter(df.store_mean,df.user_mean,df.submissions,s=70)
for _,r in df.iterrows():ax.text(r.store_mean,r.user_mean,r.submissions,r.pair)
ax.set_xlabel("Store average");ax.set_ylabel("User average");ax.set_zlabel("Submissions")
ax.set_title("3D scatter (synthetic demo)");fig.tight_layout();fig.savefig("3d_scatter.png",dpi=160);plt.close(fig)
print("Demo charts and CSV generated.")
