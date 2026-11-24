# Python data analyst starter
import csv
from statistics import mean
with open("rates.csv", newline="", encoding="utf-8") as f:
    rows=list(csv.DictReader(f))
values=[float(r["rate"]) for r in rows if r.get("rate")]
print({"rows":len(rows),"mean":mean(values) if values else None})
