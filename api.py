from __future__ import annotations
import csv, io, os, sqlite3
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
DB_PATH=Path(os.getenv('XCHANGEFINDER_DB','db/XchangeFinder.db')).expanduser().resolve()
TABLES={'storeRateSubmissions':'store','userRateSubmissions':'user'}
FIELDS=('fromCurrency','toCurrency','rate','storeUUID')
app=FastAPI(title='XchangeFinder Analytics API',version='2.0.0',description='Read-only historical submission analytics; not live exchange rates.')
def connect():
    if not DB_PATH.is_file(): raise HTTPException(503,detail='Database unavailable')
    try:
        con=sqlite3.connect(f'file:{DB_PATH.as_posix()}?mode=ro',uri=True,timeout=5); con.row_factory=sqlite3.Row; con.execute('PRAGMA query_only=ON'); return con
    except sqlite3.Error as exc: raise HTTPException(503,detail='Database connection failed') from exc
def existing_tables(con): return {r['name'] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
def valid_schema(con,table): return set(FIELDS).issubset({r['name'] for r in con.execute(f'PRAGMA table_info("{table}")')})
@app.get('/')
def root(): return {'service':'XchangeFinder Analytics API','docs':'/docs','version':'2.0.0'}
@app.get('/health')
def health(): return {'status':'ok' if DB_PATH.is_file() else 'degraded','database_available':DB_PATH.is_file()}
@app.get('/tables')
def tables():
    with connect() as con: return {'tables':sorted(existing_tables(con))}
@app.get('/rates')
def rates(source:Literal['all','store','user']='all',from_currency:str|None=Query(None,min_length=3,max_length=3),to_currency:str|None=Query(None,min_length=3,max_length=3),limit:int=Query(200,ge=1,le=5000),offset:int=Query(0,ge=0)):
    items=[]
    with connect() as con:
        available=existing_tables(con)
        for table,tag in TABLES.items():
            if table not in available or (source!='all' and source!=tag) or not valid_schema(con,table): continue
            clauses=[]; params=[]
            if from_currency: clauses.append('"fromCurrency"=?'); params.append(from_currency.upper())
            if to_currency: clauses.append('"toCurrency"=?'); params.append(to_currency.upper())
            where=' WHERE '+' AND '.join(clauses) if clauses else ''
            sql=f'SELECT "fromCurrency","toCurrency","rate","storeUUID" FROM "{table}"{where} ORDER BY rowid DESC LIMIT ? OFFSET ?'
            params.extend([limit,offset]); items.extend([dict(row)|{'source':tag} for row in con.execute(sql,params)])
    return {'count':len(items),'limit':limit,'offset':offset,'items':items}
@app.get('/analytics/pairs')
def pair_comparison(source:Literal['all','store','user']='all'):
    output=[]
    with connect() as con:
        available=existing_tables(con)
        for table,tag in TABLES.items():
            if table not in available or (source!='all' and source!=tag) or not valid_schema(con,table): continue
            sql=f'''SELECT "fromCurrency" AS from_currency,"toCurrency" AS to_currency,COUNT(*) AS submissions,AVG(CAST("rate" AS REAL)) AS average,MIN(CAST("rate" AS REAL)) AS minimum,MAX(CAST("rate" AS REAL)) AS maximum FROM "{table}" WHERE "rate" IS NOT NULL GROUP BY "fromCurrency","toCurrency" ORDER BY 1,2'''
            output.extend([dict(row)|{'source':tag} for row in con.execute(sql)])
    return {'count':len(output),'pairs':output}
@app.get('/analytics/compare')
def compare_sources(from_currency:str=Query(...,min_length=3,max_length=3),to_currency:str=Query(...,min_length=3,max_length=3)):
    pair=(from_currency.upper(),to_currency.upper()); summary={}
    with connect() as con:
        available=existing_tables(con)
        for table,tag in TABLES.items():
            if table not in available or not valid_schema(con,table): continue
            row=con.execute(f'''SELECT COUNT(*) AS n,AVG(CAST("rate" AS REAL)) AS avg_rate,MIN(CAST("rate" AS REAL)) AS min_rate,MAX(CAST("rate" AS REAL)) AS max_rate FROM "{table}" WHERE upper("fromCurrency")=? AND upper("toCurrency")=?''',pair).fetchone(); summary[tag]=dict(row)
    return {'pair':{'from':pair[0],'to':pair[1]},'sources':summary,'note':'Historical submitted rates; not guaranteed to reflect live market pricing.'}
def csv_response(rows,fields,filename):
    buf=io.StringIO(); writer=csv.DictWriter(buf,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    return StreamingResponse(iter([buf.getvalue()]),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename={filename}'})
@app.get('/analytics/export.csv')
def export_csv(source:Literal['all','store','user']='all',limit:int=Query(5000,ge=1,le=5000)):
    rows=rates(source=source,from_currency=None,to_currency=None,limit=limit,offset=0)['items']; return csv_response(rows,['source','fromCurrency','toCurrency','rate','storeUUID'],'xchangefinder_rates.csv')
@app.get('/analytics/pairs.csv')
def export_pairs(source:Literal['all','store','user']='all'):
    return csv_response(pair_comparison(source)['pairs'],['source','from_currency','to_currency','submissions','average','minimum','maximum'],'xchangefinder_pairs.csv')


@app.get("/analytics/data-quality")
def data_quality():
    report=[]
    with connect() as con:
        available=existing_tables(con)
        for table,tag in TABLES.items():
            if table not in available or not valid_schema(con,table): continue
            total=con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            nulls=con.execute(f'''SELECT SUM(CASE WHEN "fromCurrency" IS NULL OR "toCurrency" IS NULL OR "rate" IS NULL THEN 1 ELSE 0 END) FROM "{table}"''').fetchone()[0] or 0
            invalid=con.execute(f'''SELECT SUM(CASE WHEN CAST("rate" AS REAL)<=0 THEN 1 ELSE 0 END) FROM "{table}" WHERE "rate" IS NOT NULL''').fetchone()[0] or 0
            report.append({"source":tag,"rows":total,"incomplete_rows":nulls,"nonpositive_rates":invalid})
    return {"sources":report}

@app.get("/analytics/ml/forecast")
def forecast(from_currency:str=Query(...,min_length=3,max_length=3),
            to_currency:str=Query(...,min_length=3,max_length=3),steps:int=Query(3,ge=1,le=12)):
    'Experimental trend-line estimate from sequential stored submissions, not financial advice.'
    records=[]
    with connect() as con:
        available=existing_tables(con)
        for table,tag in TABLES.items():
            if table not in available or not valid_schema(con,table): continue
            rows=con.execute(f'''SELECT CAST("rate" AS REAL) AS rate FROM "{table}"
              WHERE upper("fromCurrency")=? AND upper("toCurrency")=? AND "rate" IS NOT NULL
              ORDER BY rowid ASC''',(from_currency.upper(),to_currency.upper())).fetchall()
            records.extend([r["rate"] for r in rows if r["rate"]>0])
    if len(records)<3:
        raise HTTPException(status_code=422,detail="At least three positive historical submissions for this pair are required")
    # Lightweight trend fit; no third-party ML package required.
    n=len(records); xmean=(n-1)/2; ymean=sum(records)/n
    denom=sum((i-xmean)**2 for i in range(n))
    slope=sum((i-xmean)*(y-ymean) for i,y in enumerate(records))/denom if denom else 0.0
    intercept=ymean-slope*xmean
    return {"pair":{"from":from_currency.upper(),"to":to_currency.upper()},
            "observations":n,"method":"simple linear trend regression",
            "forecast":[{"step":i,"estimated_rate":round(intercept+slope*(n-1+i),8)} for i in range(1,steps+1)],
            "warning":"Experimental estimate from submission order only; not market forecasting or financial advice."}
