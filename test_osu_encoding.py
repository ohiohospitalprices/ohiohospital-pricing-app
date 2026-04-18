#!/usr/bin/env python3
"""
Test OSU CSV encoding and extract data
"""

import requests
import zipfile
import io

url = "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip"

print("[*] Downloading OSU Medical Center pricing data...")
try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    print(f"[OK] Downloaded {len(response.content)/1024/1024:.1f} MB")
    
    # Extract ZIP
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        for file_info in zip_ref.filelist:
            print(f"\n[*] Found: {file_info.filename}")
            print(f"    Size: {file_info.file_size:,} bytes")
            
            if file_info.filename.endswith('.csv'):
                with zip_ref.open(file_info) as csv_file:
                    content_bytes = csv_file.read()
                    
                    # Try common encodings
                    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16', 'utf-8-sig']
                    decoded = False
                    
                    for enc in encodings:
                        try:
                            content = content_bytes.decode(enc)
                            rows = len(content.split('\n'))
                            print(f"[OK] Successfully decoded with {enc}")
                            print(f"    Total rows: {rows:,}")
                            print(f"\n    First 500 chars of data:")
                            print(f"    {content[:500]}")
                            decoded = True
                            break
                        except Exception as e:
                            print(f"    [{enc}] Failed: {str(e)[:50]}")
                            continue
                    
                    if not decoded:
                        print("[ERROR] Could not decode with any standard encoding")
                        print(f"[INFO] First 100 bytes (hex): {content_bytes[:100].hex()}")

except Exception as e:
    print(f"[ERROR] {e}")
