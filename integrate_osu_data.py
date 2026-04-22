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

class OSUIntegrator:
    def __init__(self):
        self.app_dir = Path("C:\\Users\\Owner\\.openclaw\\workspace-openclaw-ai\\ohiohospital-pricing-app")
        self.procedures_file = self.app_dir / "procedures.json"
        self.hospital_data_dir = self.app_dir / "hospital_data"
        self.hospital_data_dir.mkdir(parents=True, exist_ok=True)
        
        # OSU hospitals to integrate
        self.osu_hospitals = {
            "OSU Wexner Medical Center": "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip",
            "Arthur G James Cancer Hospital": "https://wexnermedical.osu.edu/files/31-1322863_JAMES-CANCER-HOSPITAL_standardcharges.csv.zip",
        }
        
        # Category mapping for OSU procedures
        self.category_keywords = {
            "Room": ["room", "bed", "accommodation", "daily"],
            "Surgical": ["operating room", "or", "surgery", "surgical", "procedure room"],
            "ER": ["emergency", "er", "ed", "trauma"],
            "Lab": ["lab", "laboratory", "blood", "pathology", "test"],
            "Imaging": ["imaging", "xray", "ct", "mri", "ultrasound", "radiograph"],
            "Pharmacy": ["pharmacy", "drug", "medication"],
            "Therapy": ["therapy", "physical", "pt", "occupational", "speech"],
            "Other": []  # default fallback
        }
        
        self.osu_procedures = []
        self.stats = {
            "total_osu_rows": 0,
            "parsed_osu": 0,
            "existing_procedures": 0,
            "merged_procedures": 0,
            "new_osu_procedures": 0
        }
    
    def download_and_parse_osu(self, hospital_name, url):
        """Download OSU CSV and parse into procedure list"""
        print(f"\n[*] Processing {hospital_name}...")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            size_mb = len(response.content) / 1024 / 1024
            print(f"    Downloaded: {size_mb:.1f} MB")
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('.csv'):
                        with zip_ref.open(file_info) as csv_file:
                            # Try different encodings
                            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                                try:
                                    content = csv_file.read().decode(encoding)
                                    print(f"    Using encoding: {encoding}")
                                    break
                                except:
                                    csv_file.seek(0)
                                    continue
                            else:
                                print(f"    [WARNING] Could not decode CSV, skipping")
                                return
                            
                            # Parse CSV
                            reader = csv.DictReader(io.StringIO(content))
                            row_count = 0
                            
                            for row in reader:
                                row_count += 1
                                self.stats["total_osu_rows"] += 1
                                
                                # Sample every Nth row to avoid excessive processing
                                # (OSU data is very large; we'll sample smartly)
                                if row_count % 50 == 0 or row_count < 100:
                                    proc = self._parse_osu_row(row, hospital_name)
                                    if proc:
                                        self.osu_procedures.append(proc)
                                        self.stats["parsed_osu"] += 1
                            
                            print(f"    Parsed {row_count:,} rows -> {self.stats['parsed_osu']} procedures")
        
        except Exception as e:
            import traceback
            print(f"    [ERROR] {e}")
            traceback.print_exc()
    
    def _parse_osu_row(self, row, hospital_name):
        """Convert OSU CSV row to standard procedure format"""
        try:
            # OSU CSV typically has: description, code, price
            description = row.get('Description', '').strip() or row.get('description', '').strip()
            code = row.get('Code', '').strip() or row.get('code', '').strip()
            price_str = row.get('Price', '') or row.get('price', '') or row.get('Gross Charge', '')
            
            if not description or not code:
                return None
            
            # Parse price
            try:
                price = float(str(price_str).replace('$', '').replace(',', ''))
            except:
                price = 0.0
            
            # Categorize procedure
            category = self._categorize_procedure(description)
            
            return {
                "hospital": hospital_name,
                "procedure": description[:200],  # Truncate long descriptions
                "cpt": code[:15],  # Standard CPT format
                "price": price,
                "category": category
            }
        
        except Exception as e:
            return None
    
    def _categorize_procedure(self, description):
        """Guess category from procedure description"""
        desc_lower = description.lower()
        
        for category, keywords in self.category_keywords.items():
            if category != "Other":
                for keyword in keywords:
                    if keyword in desc_lower:
                        return category
        
        return "Other"
    
    def merge_with_existing(self):
        """Load existing procedures and merge OSU data"""
        print("\n[*] Loading existing procedures...")
        
        with open(self.procedures_file, 'r') as f:
            existing = json.load(f)
        
        self.stats["existing_procedures"] = len(existing)
        
        # Track existing procedures to avoid duplicates
        existing_set = set()
        for proc in existing:
            key = (proc["hospital"], proc["procedure"], proc["cpt"])
            existing_set.add(key)
        
        # Add OSU procedures, avoiding duplicates
        for proc in self.osu_procedures:
            key = (proc["hospital"], proc["procedure"], proc["cpt"])
            if key not in existing_set:
                existing.append(proc)
                existing_set.add(key)
                self.stats["new_osu_procedures"] += 1
        
        self.stats["merged_procedures"] = len(existing)
        
        return existing
    
    def save_merged_procedures(self, merged_data):
        """Save merged procedures back to JSON"""
        print("\n[*] Saving merged procedures...")
        
        with open(self.procedures_file, 'w') as f:
            json.dump(merged_data, f, indent=2)
        
        print(f"    Saved {len(merged_data)} total procedures")
    
    def update_hospital_list(self, merged_data):
        """Update hospital dropdown selector"""
        print("\n[*] Updating hospital selector...")
        
        hospitals = sorted(set([proc["hospital"] for proc in merged_data]))
        
        selector_file = self.app_dir / "hospital_list.json"
        with open(selector_file, 'w') as f:
            json.dump({"hospitals": hospitals}, f, indent=2)
        
        print(f"    Updated hospital list: {len(hospitals)} hospitals")
        return hospitals
    
    def verify_categories(self, merged_data):
        """Verify each hospital has procedures in all categories"""
        print("\n[*] Verifying category coverage...")
        
        hospitals = set([proc["hospital"] for proc in merged_data])
        categories = set([proc["category"] for proc in merged_data])
        
        issues = []
        for hospital in sorted(hospitals):
            hosp_procs = [p for p in merged_data if p["hospital"] == hospital]
            hosp_cats = set([p["category"] for p in hosp_procs])
            
            missing = categories - hosp_cats
            if missing:
                issues.append(f"{hospital}: missing {missing}")
        
        if issues:
            print("    [WARNING] Some hospitals missing categories:")
            for issue in issues[:5]:
                print(f"      - {issue}")
        else:
            print("    [OK] All hospitals have all categories")
        
        return len(issues) == 0
    
    def run(self):
        """Execute full integration"""
        print("\n" + "="*80)
        print("OSU HOSPITAL DATA INTEGRATION")
        print("="*80)
        
        # Download and parse OSU data
        for hospital_name, url in self.osu_hospitals.items():
            self.download_and_parse_osu(hospital_name, url)
        
        # Merge with existing
        merged = self.merge_with_existing()
        self.save_merged_procedures(merged)
        
        # Update selectors
        hospitals = self.update_hospital_list(merged)
        
        # Verify
        self.verify_categories(merged)
        
        # Report
        print("\n" + "="*80)
        print("INTEGRATION COMPLETE")
        print("="*80)
        print(f"Existing procedures:     {self.stats['existing_procedures']:,}")
        print(f"OSU raw rows processed:  {self.stats['total_osu_rows']:,}")
        print(f"OSU procedures parsed:   {self.stats['parsed_osu']:,}")
        print(f"New OSU procedures:      {self.stats['new_osu_procedures']:,}")
        print(f"Total merged:            {self.stats['merged_procedures']:,}")
        print(f"\nHospitals ({len(hospitals)}):")
        for h in hospitals:
            marker = "🆕" if "OSU" in h or "Arthur" in h else "   "
            print(f"  {marker} {h}")


def main():
    integrator = OSUIntegrator()
    integrator.run()


if __name__ == "__main__":
    main()
