#!/usr/bin/env python3
import csv
import zipfile
import io
import requests

url = "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip"

print("[*] Downloading OSU Wexner Medical Center...")
response = requests.get(url, timeout=120)

with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
    with zip_ref.open(zip_ref.filelist[0]) as csv_file:
        content = csv_file.read().decode('latin-1')
        lines = content.split('\n')
        
        # Look at header and first real data rows
        print("\n[*] First 20 lines (raw):")
        for i, line in enumerate(lines[:20]):
            preview = line[:120] if len(line) > 120 else line
            print(f"{i:2d}: {preview}")
        
        # Count columns in a data row
        print("\n[*] Column analysis:")
        data_line = lines[4]  # A real data row
        fields = data_line.split(',')
        print(f"    Row has {len(fields)} fields")
        print(f"\n    First 10 fields:")
        for i, field in enumerate(fields[:10]):
            preview = field[:80] if len(field) > 80 else field
            print(f"    {i}: {preview}")
