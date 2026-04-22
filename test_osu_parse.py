#!/usr/bin/env python3
import csv
import zipfile
import io
import requests

# Download one hospital's data
url = "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip"

print("[*] Downloading OSU Wexner Medical Center...")
response = requests.get(url, timeout=120)
print(f"    Downloaded {len(response.content)/1024/1024:.1f} MB")

print("\n[*] Extracting and inspecting CSV structure...")
with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
    for file_info in zip_ref.filelist:
        if file_info.filename.endswith('.csv'):
            print(f"    File: {file_info.filename}")
            
            with zip_ref.open(file_info) as csv_file:
                content = csv_file.read().decode('latin-1')
                
                lines = content.split('\n')
                print(f"    Total lines: {len(lines):,}")
                
                # Show header and first few rows
                reader = csv.DictReader(io.StringIO(content))
                
                print(f"\n[*] Header fields:")
                if reader.fieldnames:
                    for i, field in enumerate(reader.fieldnames):
                        print(f"    {i}: {field}")
                
                print(f"\n[*] Sample rows:")
                for i, row in enumerate(reader):
                    if i >= 5:
                        break
                    print(f"\n    Row {i+1}:")
                    for key, val in list(row.items())[:5]:  # First 5 fields
                        print(f"      {key}: {val[:80] if val else 'NULL'}")
