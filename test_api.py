import sys, pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import sqlite3
from fastapi.testclient import TestClient
import api as main
def fixture_db(tmp_path):
 p=tmp_path/'test.db'
 with sqlite3.connect(p) as c:
  for t in ('storeRateSubmissions','userRateSubmissions'): c.execute(f'CREATE TABLE {t} (fromCurrency TEXT,toCurrency TEXT,rate REAL,storeUUID TEXT)')
  c.executemany('INSERT INTO storeRateSubmissions VALUES(?,?,?,?)',[('USD','EUR',.9,'s1'),('USD','EUR',.91,'s2'),('GBP','USD',1.2,'s3')]);c.execute('INSERT INTO userRateSubmissions VALUES(?,?,?,?)',('USD','EUR',.92,'u1'))
 return p
def client(tmp_path,monkeypatch): monkeypatch.setattr(main,'DB_PATH',fixture_db(tmp_path));return TestClient(main.app)
def test_health_tables(tmp_path,monkeypatch):
 c=client(tmp_path,monkeypatch);assert c.get('/health').json()['database_available'];assert 'storeRateSubmissions' in c.get('/tables').json()['tables']
def test_filters_and_pagination(tmp_path,monkeypatch):
 c=client(tmp_path,monkeypatch);r=c.get('/rates',params={'from_currency':'usd','to_currency':'eur','limit':1});assert r.status_code==200 and len(r.json()['items'])==2
def test_analytics_and_comparison(tmp_path,monkeypatch):
 c=client(tmp_path,monkeypatch);assert c.get('/analytics/pairs').json()['count']==3;assert c.get('/analytics/compare',params={'from_currency':'USD','to_currency':'EUR'}).status_code==200
def test_csv(tmp_path,monkeypatch):
 c=client(tmp_path,monkeypatch);assert 'fromCurrency' in c.get('/analytics/export.csv').text;assert 'average' in c.get('/analytics/pairs.csv').text
def test_database_is_read_only(tmp_path,monkeypatch):
 c=client(tmp_path,monkeypatch)
 with main.connect() as con:
  try: con.execute('DELETE FROM storeRateSubmissions');assert False
  except sqlite3.OperationalError: pass


def test_data_quality_and_forecast(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch)
    assert c.get("/analytics/data-quality").status_code==200
    assert c.get("/analytics/ml/forecast",params={"from_currency":"USD","to_currency":"EUR"}).status_code==200
