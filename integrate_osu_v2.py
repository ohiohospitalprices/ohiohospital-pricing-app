#!/usr/bin/env python3
"""
Integrate OSU Hospital data - simplified approach
"""

import json
import csv
import zipfile
import io
import requests
from pathlib import Path

class OSUIntegrator:
    def __init__(self):
        self.app_dir = Path("C:\\Users\\Owner\\.openclaw\\workspace-openclaw-ai\\ohiohospital-pricing-app")
        self.procedures_file = self.app_dir / "procedures.json"
        
        self.osu_hospitals = {
            "OSU Wexner Medical Center": "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip",
            "Arthur G James Cancer Hospital": "https://wexnermedical.osu.edu/files/31-1322863_JAMES-CANCER-HOSPITAL_standardcharges.csv.zip",
        }
        
        self.new_procedures = []
        self.stats = {"existing": 0, "added": 0, "total": 0}
    
    def process_hospital(self, hospital_name, url):
        """Download and parse OSU hospital data"""
        print(f"[*] {hospital_name}...")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            print(f"    Downloaded {len(response.content)/1024/1024:.1f} MB")
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open(z.namelist()[0]) as f:
                    content = f.read().decode('latin-1')
                    lines = content.split('\n')
                    
                    # Skip first 2 rows (metadata, schema)
                    csv_reader = csv.reader(lines[2:])
                    
                    proc_count = 0
                    for row_idx, row in enumerate(csv_reader):
                        if row_idx % 100 != 0 or row_idx == 0:  # Sample every 100th
                            continue
                        
                        if len(row) < 2 or not row[0]:
                            continue
                        
                        # Map fields from OSU CSV
                        # hospital_name field = description
                        description = row[0].strip()
                        code = row[1].strip() if len(row) > 1 else ""
                        
                        if not description or not code or code in ["code|1", "description"]:
                            continue
                        
                        # Extract price from row (typically in columns 10+)
                        price = 0.0
                        for i in range(10, min(20, len(row))):
                            try:
                                val = row[i].strip()
                                if val and val not in ['-', '']:
                                    p = float(val)
                                    if p > 0:
                                        price = p
                                        break
                            except:
                                pass
                        
                        # Determine category
                        desc_lower = description.lower()
                        if any(x in desc_lower for x in ["room", "bed"]):
                            category = "Room"
                        elif any(x in desc_lower for x in ["surg", "or ", "procedure"]):
                            category = "Surgical"
                        elif any(x in desc_lower for x in ["lab", "test"]):
                            category = "Lab"
                        elif any(x in desc_lower for x in ["xray", "ct", "mri", "imaging"]):
                            category = "Imaging"
                        elif any(x in desc_lower for x in ["pharma", "drug"]):
                            category = "Pharmacy"
                        elif any(x in desc_lower for x in ["therapy", "pt"]):
                            category = "Therapy"
                        elif any(x in desc_lower for x in ["emer", "er "]):
                            category = "ER"
                        else:
                            category = "Other"
                        
                        proc = {
                            "hospital": hospital_name,
                            "procedure": description[:150],
                            "cpt": code[:15],
                            "price": round(price, 2),
                            "category": category
                        }
                        
                        self.new_procedures.append(proc)
                        proc_count += 1
                    
                    print(f"    Parsed {proc_count} procedures")
        
        except Exception as e:
            print(f"    ERROR: {e}")
    
    def merge_and_save(self):
        """Load, merge, and save"""
        print("[*] Loading existing...")
        with open(self.procedures_file) as f:
            existing = json.load(f)
        
        self.stats["existing"] = len(existing)
        
        # Dedup
        existing_cpts = {p["cpt"]: p["hospital"] for p in existing}
        
        for proc in self.new_procedures:
            if proc["cpt"] not in existing_cpts:
                existing.append(proc)
                self.stats["added"] += 1
        
        self.stats["total"] = len(existing)
        
        print("[*] Saving...")
        with open(self.procedures_file, 'w') as f:
            json.dump(existing, f, indent=2)
        
        # Update hospital list
        hospitals = sorted(set(p["hospital"] for p in existing))
        with open(self.app_dir / "hospital_list.json", 'w') as f:
            json.dump({"hospitals": hospitals}, f, indent=2)
        
        return hospitals
    
    def run(self):
        print("\n" + "="*70)
        print("OSU DATA INTEGRATION")
        print("="*70 + "\n")
        
        for name, url in self.osu_hospitals.items():
            self.process_hospital(name, url)
        
        hospitals = self.merge_and_save()
        
        print("\n" + "="*70)
        print(f"Existing: {self.stats['existing']:,}")
        print(f"Added: {self.stats['added']:,}")
        print(f"Total: {self.stats['total']:,}")
        print(f"\nHospitals ({len(hospitals)}):")
        for h in hospitals:
            marker = "[NEW]" if "OSU" in h or "Arthur" in h else "     "
            print(f"  {marker} {h}")
        print("="*70 + "\n")

if __name__ == "__main__":
    integrator = OSUIntegrator()
    integrator.run()
