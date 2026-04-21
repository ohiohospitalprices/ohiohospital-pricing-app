import requests
import json
import csv
import zipfile
import io

# Check OhioHealth JSON structure more carefully
print("=== OhioHealth JSON ===")
url = "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/384105653_berger-hospital_standardcharges.json"
resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(resp.content.decode('utf-8-sig'))
sci = data.get('standard_charge_information', [])
if len(sci) > 0:
    print(f"Total items: {len(sci)}")
    item = sci[0]
    print(f"Item type: {type(item)}")
    print(f"Item keys: {list(item.keys())}")
    print(f"First item: {json.dumps(item, indent=2)[:500]}")

# Check CSV
print("\n=== Morrow County Hospital CSV ===")
url = "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/316402699_morrow-county-hospital-_standardcharges.csv"
resp = requests.get(url, timeout=10)
text = resp.content.decode('utf-8', errors='ignore')
reader = csv.DictReader(io.StringIO(text))
rows = list(reader)
if len(rows) > 0:
    print(f"Total rows: {len(rows)}")
    print(f"Headers: {list(rows[0].keys())}")
    print(f"First row: {rows[0]}")

# Check OSU CSV ZIP
print("\n=== Ohio State ZIP ===")
url = "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip"
resp = requests.get(url, timeout=30)
with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
    print(f"Files in ZIP: {zf.namelist()[:5]}")
    for fname in zf.namelist()[:1]:
        with zf.open(fname) as f:
            text = f.read().decode('latin-1', errors='ignore')
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            if len(rows) > 0:
                print(f"File: {fname}")
                print(f"Rows: {len(rows)}")
                print(f"Headers: {list(rows[0].keys())[:20]}")
                print(f"First row keys with values:")
                for k in list(rows[0].keys())[:10]:
                    print(f"  {k}: {rows[0][k]}")
