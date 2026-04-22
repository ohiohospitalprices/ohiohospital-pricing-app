#!/usr/bin/env python3
"""
Integrate OSU Hospital pricing data into OhioHealth procedures.json
Parses raw OSU CSVs and merges with existing OhioHealth data
"""

import json
import csv
import zipfile
import io
import requests
from pathlib import Path
from collections import defaultdict
import sys

class OSUIntegrator:
    def __init__(self):
        self.app_dir = Path("C:\\Users\\Owner\\.openclaw\\workspace-openclaw-ai\\ohiohospital-pricing-app")
        self.procedures_file = self.app_dir / "procedures.json"
        
        # OSU hospitals to integrate
        self.osu_hospitals = {
            "OSU Wexner Medical Center": "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip",
            "Arthur G James Cancer Hospital": "https://wexnermedical.osu.edu/files/31-1322863_JAMES-CANCER-HOSPITAL_standardcharges.csv.zip",
        }
        
        # Category mapping
        self.category_keywords = {
            "Room": ["room", "bed", "accommodation", "daily"],
            "Surgical": ["operating", "or ", "surgery", "surgical", "procedure"],
            "ER": ["emergency", "er", "ed", "trauma"],
            "Lab": ["lab", "test", "pathology", "culture"],
            "Imaging": ["imaging", "xray", "ct", "mri", "ultrasound", "radiograph"],
            "Pharmacy": ["pharmacy", "drug", "medication", "dose"],
            "Therapy": ["therapy", "physical", "pt", "occupational", "speech"],
        }
        
        self.osu_procedures = []
        self.stats = {
            "existing": 0,
            "osu_processed": 0,
            "osu_added": 0,
            "merged_total": 0
        }
    
    def download_and_parse_osu(self, hospital_name, url):
        """Download OSU CSV and parse"""
        print(f"[*] {hospital_name}...")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            size_mb = len(response.content) / 1024 / 1024
            print(f"    Downloaded {size_mb:.1f} MB")
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('.csv'):
                        with zip_ref.open(file_info) as csv_file:
                            content = csv_file.read().decode('latin-1')
                            
                            # Parse CSV
                            reader = csv.DictReader(io.StringIO(content))
                            row_count = 0
                            proc_count = 0
                            
                            for row in reader:
                                row_count += 1
                                
                                # Skip header rows and empty rows
                                if row_count <= 2 or not row.get('description'):
                                    continue
                                
                                # Sample: process every Nth row (OSU data is large)
                                if row_count % 100 == 0:
                                    proc = self._parse_row(row, hospital_name)
                                    if proc:
                                        self.osu_procedures.append(proc)
                                        proc_count += 1
                            
                            print(f"    Sampled {row_count:,} rows -> {proc_count} procedures")
                            self.stats["osu_processed"] += proc_count
        
        except Exception as e:
            print(f"    ERROR: {e}")
    
    def _parse_row(self, row, hospital_name):
        """Convert CSV row to standard format"""
        try:
            desc = row.get('description', '').strip()
            code = row.get('code|1', '').strip()
            
            # Try to find a price column
            price = 0.0
            for key in row:
                if 'price' in key.lower() or 'charge' in key.lower() or 'cost' in key.lower():
                    try:
                        val = row[key].strip()
                        if val and val not in ['', 'NULL', '-']:
                            price = float(val)
                            break
                    except:
                        pass
            
            # If still no price, try parsing numbers from common patterns
            if price == 0:
                for key in list(row.values())[10:20]:  # Later columns often have prices
                    try:
                        if key and key.replace('.', '').replace('-', '').isdigit():
                            price = float(key)
                            if price > 10:  # Reasonable price threshold
                                break
                    except:
                        pass
            
            if not desc or not code:
                return None
            
            category = self._categorize(desc)
            
            return {
                "hospital": hospital_name,
                "procedure": desc[:150],
                "cpt": code[:15],
                "price": round(price, 2) if price > 0 else 0.0,
                "category": category
            }
        
        except:
            return None
    
    def _categorize(self, desc):
        """Categorize procedure"""
        desc_lower = desc.lower()
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return category
        
        return "Other"
    
    def merge(self):
        """Load existing and merge"""
        print("[*] Loading existing procedures...")
        
        with open(self.procedures_file, 'r') as f:
            existing = json.load(f)
        
        self.stats["existing"] = len(existing)
        
        # Dedup set
        existing_set = set()
        for p in existing:
            key = (p["hospital"], p["cpt"])
            existing_set.add(key)
        
        # Add new OSU procedures
        for p in self.osu_procedures:
            key = (p["hospital"], p["cpt"])
            if key not in existing_set:
                existing.append(p)
                existing_set.add(key)
                self.stats["osu_added"] += 1
        
        self.stats["merged_total"] = len(existing)
        return existing
    
    def save(self, data):
        """Save merged data"""
        print("[*] Saving merged procedures...")
        
        with open(self.procedures_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also update hospital list
        hospitals = sorted(set([p["hospital"] for p in data]))
        list_file = self.app_dir / "hospital_list.json"
        with open(list_file, 'w') as f:
            json.dump({"hospitals": hospitals}, f, indent=2)
        
        return hospitals
    
    def run(self):
        """Execute integration"""
        print("\n" + "="*70)
        print("OSU HOSPITAL DATA INTEGRATION")
        print("="*70 + "\n")
        
        # Download and parse
        for name, url in self.osu_hospitals.items():
            self.download_and_parse_osu(name, url)
        
        # Merge
        merged = self.merge()
        hospitals = self.save(merged)
        
        # Report
        print("\n" + "="*70)
        print("INTEGRATION COMPLETE")
        print("="*70)
        print(f"Existing procedures:  {self.stats['existing']:,}")
        print(f"OSU procedures found: {self.stats['osu_processed']:,}")
        print(f"OSU procedures added: {self.stats['osu_added']:,}")
        print(f"Total procedures:     {self.stats['merged_total']:,}")
        print(f"\nHospitals ({len(hospitals)}):")
        for h in hospitals:
            marker = "[NEW]" if "OSU" in h or "Arthur" in h else "     "
            print(f"  {marker} {h}")
        print()


if __name__ == "__main__":
    integrator = OSUIntegrator()
    integrator.run()
