#!/usr/bin/env python3
"""
Extract OSU Wexner Medical Center pricing data
Uses latin-1 encoding for proper CSV decoding
"""

import requests
import zipfile
import io
from datetime import datetime
from pathlib import Path

class OSUExtractor:
    def __init__(self):
        self.output_dir = Path("C:\\Users\\Owner\\OneDrive\\Desktop\\Hospital_Pricing\\All_Systems")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.hospitals = {
            "Ohio State University Medical Center": "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip",
            "James Cancer Hospital": "https://wexnermedical.osu.edu/files/31-1322863_JAMES-CANCER-HOSPITAL_standardcharges.csv.zip",
        }
        
        self.results = []
    
    def extract_hospital(self, name, url):
        """Extract OSU hospital with latin-1 encoding"""
        print(f"\n[*] {name}")
        print(f"    {url}")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            print(f"    [OK] Downloaded {len(response.content)/1024/1024:.1f} MB")
            
            # Extract ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('.csv'):
                        print(f"    [*] Extracting: {file_info.filename}")
                        
                        with zip_ref.open(file_info) as csv_file:
                            content_bytes = csv_file.read()
                            
                            # Decode with latin-1
                            try:
                                content = content_bytes.decode('latin-1')
                                rows = len(content.split('\n'))
                                
                                print(f"    [OK] Decoded with latin-1")
                                print(f"    [OK] Total rows: {rows:,}")
                                
                                self.results.append({
                                    "hospital": name,
                                    "system": "Ohio State University",
                                    "status": "Success",
                                    "rows": rows,
                                    "file_size_mb": len(response.content)/1024/1024,
                                    "url": url
                                })
                                
                                return True
                            except Exception as e:
                                print(f"    [ERROR] Decoding failed: {e}")
                                self.results.append({
                                    "hospital": name,
                                    "status": f"Failed: {str(e)}",
                                    "rows": 0,
                                    "url": url
                                })
                                return False
        
        except Exception as e:
            print(f"    [ERROR] Download failed: {e}")
            self.results.append({
                "hospital": name,
                "status": f"Failed: {str(e)}",
                "rows": 0,
                "url": url
            })
            return False
    
    def process_all(self):
        """Process all OSU hospitals"""
        print("\n" + "="*80)
        print("EXTRACTING OHIO STATE UNIVERSITY WEXNER MEDICAL CENTER")
        print("="*80)
        print(f"\nTotal hospitals: {len(self.hospitals)}")
        
        success = 0
        for hospital_name, url in self.hospitals.items():
            if self.extract_hospital(hospital_name, url):
                success += 1
        
        print("\n" + "="*80)
        print(f"COMPLETE: {success}/{len(self.hospitals)} OSU hospitals extracted")
        print("="*80)
        
        self.generate_report()
    
    def generate_report(self):
        """Generate summary"""
        print("\n[RESULTS]")
        
        total_rows = 0
        for r in self.results:
            status = "[OK]" if r["status"] == "Success" else "[FAIL]"
            rows = r.get("rows", 0)
            size = r.get("file_size_mb", 0)
            print(f"  {status} {r['hospital']:<40} {rows:>10,} rows ({size:.1f} MB)")
            total_rows += rows
        
        print(f"\n[TOTAL] {total_rows:,} rows across all OSU hospitals")
        
        if total_rows > 0:
            print("\n[SUCCESS] OSU data ready for integration into master database!")


def main():
    extractor = OSUExtractor()
    extractor.process_all()


if __name__ == "__main__":
    main()
