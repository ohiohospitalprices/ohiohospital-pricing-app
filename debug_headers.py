#!/usr/bin/env python3
import csv
import zipfile
import io
import requests

url = "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip"

response = requests.get(url, timeout=120)

with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
    with zip_ref.open(zip_ref.filelist[0]) as csv_file:
        content = csv_file.read().decode('latin-1')
        
        reader = csv.DictReader(io.StringIO(content))
        
        print("Fieldnames:")
        for i, field in enumerate(reader.fieldnames):
            print(f"  {i}: '{field}'")
        
        print("\n\nFirst 3 actual data rows:")
        for row_idx, row in enumerate(reader):
            if row_idx >= 3:
                break
            print(f"\nRow {row_idx}:")
            for key, val in list(row.items())[:8]:
                v = val[:50] if val else "EMPTY"
                print(f"  '{key}': {v}")
