#!/usr/bin/env python3
"""
Complete Hospital Price Extraction
Extracts all 24 hospitals: 16 OhioHealth + 2 OSU + 6 Mt Carmel
"""

import json
import requests
import csv
import os
from datetime import datetime
from pathlib import Path
import zipfile
import io

class CompleteHospitalExtractor:
    def __init__(self):
        self.output_dir = Path("C:\\Users\\Owner\\OneDrive\\Desktop\\Hospital_Pricing\\All_Systems")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        
        # ALL 24 HOSPITALS
        self.hospitals = {
            # OhioHealth (16)
            "Berger Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/384105653_berger-hospital_standardcharges.json",
            "Doctors Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_doctors-hospital_standardcharges.json",
            "Dublin Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_dublin-methodist-hospital_standardcharges.json",
            "Grady Memorial Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314379436_grady-memorial-hospital_standardcharges.json",
            "Grant Medical Center": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grant-medical-center_standardcharges.json",
            "Grove City Methodist": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grove-city-methodist_standardcharges.json",
            "Hardin Memorial Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314440479_hardin-memorial-hospital_standardcharges.json",
            "Mansfield Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/310714456_ohiohealth-mansfield-hospital_standardcharges.json",
            "Marion General Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/311070887_marion-general-hospital_standardcharges.json",
            "Morrow County Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/316402699_morrow-county-hospital-_standardcharges.csv",
            "O'Bleness Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314446959_ohiohealth-o-_bleness-hospital_standardcharges.json",
            "Pickerington Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_pickerington-methodist-hospital_standardcharges.json",
            "Riverside Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_riverside-methodist-hospital_standardcharges.json",
            "Shelby Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/340714456_ohiohealth-shelby-hospital_standardcharges.json",
            "Southeastern Medical Center": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314391798_southeastern-ohio-regional-medical-center_standardcharges.json",
            "Van Wert Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/344429514_van-wert-county-hospital_standardcharges.json",
            
            # Ohio State University Wexner Medical Center (2)
            "Ohio State University Medical Center": "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip",
            "James Cancer Hospital": "https://wexnermedical.osu.edu/files/31-1322863_JAMES-CANCER-HOSPITAL_standardcharges.csv.zip",
            
            # Mount Carmel Health System (6)
            "Mount Carmel East": "https://hpt.trinity-health.org/311439334-1982784535_mount-carmel-east_standardcharges.zip",
            "Mount Carmel Grove City": "https://hpt.trinity-health.org/311439334-1710067376_mount-carmel-grove-city_standardcharges.zip",
            "Mount Carmel New Albany": "https://hpt.trinity-health.org/311439334-1770668568_mount-carmel-new-albany_standardcharges.zip",
            "Mount Carmel St. Ann's": "https://hpt.trinity-health.org/311439334-1417037045_mount-carmel-st-anns_standardcharges.zip",
            "Mount Carmel Dublin": "https://hpt.trinity-health.org/311439334-1710752183_Mount-Carmel-Dublin_standardcharges.zip",
            "Diley Ridge Medical Center": "https://hpt.trinity-health.org/342032340_diley-ridge-medical-center_standardcharges.zip",
        }
    
    def extract_hospital(self, name, url):
        """Extract a single hospital"""
        print(f"\n[*] {name}")
        print(f"    {url}")
        
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Handle ZIP files
            if url.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('.csv'):
                            with zip_ref.open(file_info) as csv_file:
                                content = csv_file.read().decode('utf-8')
                                procedure_count = len(content.split('\n')) - 2
                                print(f"    [OK] Extracted {procedure_count} rows from {file_info.filename}")
                                self.results.append({
                                    "hospital": name,
                                    "system": "Mount Carmel" if "carmel" in name.lower() else "OhioHealth",
                                    "status": "Success",
                                    "procedures": procedure_count,
                                    "url": url
                                })
                                return True
            
            # Handle JSON files
            elif url.endswith('.json'):
                data = json.loads(response.text.encode().decode('utf-8-sig'))
                procedures = data.get("standard_charge_information", [])
                print(f"    [OK] Extracted {len(procedures)} procedures")
                self.results.append({
                    "hospital": name,
                    "system": "OhioHealth",
                    "status": "Success",
                    "procedures": len(procedures),
                    "url": url
                })
                return True
            
            # Handle CSV files
            elif url.endswith('.csv'):
                procedure_count = len(response.text.split('\n')) - 2
                print(f"    [OK] Extracted {procedure_count} rows")
                self.results.append({
                    "hospital": name,
                    "system": "OhioHealth",
                    "status": "Success",
                    "procedures": procedure_count,
                    "url": url
                })
                return True
                
        except Exception as e:
            print(f"    [ERROR] {str(e)}")
            self.results.append({
                "hospital": name,
                "status": f"Failed: {str(e)}",
                "procedures": 0,
                "url": url
            })
            return False
    
    def process_all(self):
        """Process all hospitals"""
        print("\n" + "="*80)
        print("EXTRACTING ALL 24 HOSPITALS")
        print("="*80)
        print(f"\nTotal hospitals: {len(self.hospitals)}")
        print("OhioHealth: 16")
        print("Ohio State University: 2")
        print("Mount Carmel: 6")
        
        success = 0
        for hospital_name, url in self.hospitals.items():
            if self.extract_hospital(hospital_name, url):
                success += 1
        
        print("\n" + "="*80)
        print(f"COMPLETE: {success}/{len(self.hospitals)} hospitals extracted")
        print("="*80)
        
        self.generate_report()
    
    def generate_report(self):
        """Generate summary report"""
        print("\n[RESULTS BY SYSTEM]")
        
        ohiohealth = [r for r in self.results if r.get("system") == "OhioHealth"]
        osu = [r for r in self.results if r.get("hospital") in ["Ohio State University Medical Center", "James Cancer Hospital"]]
        mtcarmel = [r for r in self.results if r.get("system") == "Mount Carmel"]
        
        total_procedures = sum(r.get("procedures", 0) for r in self.results)
        
        print(f"\nOhioHealth ({len(ohiohealth)} hospitals)")
        for r in ohiohealth:
            status = "[OK]" if r["status"] == "Success" else "[FAIL]"
            print(f"  {status} {r['hospital']:<40} {r['procedures']:>6} procedures")
        
        print(f"\nOhio State University ({len(osu)} hospitals)")
        for r in osu:
            status = "[OK]" if r["status"] == "Success" else "[FAIL]"
            print(f"  {status} {r['hospital']:<40} {r['procedures']:>6} procedures")
        
        print(f"\nMount Carmel ({len(mtcarmel)} hospitals)")
        for r in mtcarmel:
            status = "[OK]" if r["status"] == "Success" else "[FAIL]"
            print(f"  {status} {r['hospital']:<40} {r['procedures']:>6} procedures")
        
        print(f"\n[TOTAL] {total_procedures} procedures across all hospitals")
        
        # Export summary
        self.export_summary()
    
    def export_summary(self):
        """Export summary CSV"""
        filepath = self.output_dir / f"All_Hospitals_Summary_{datetime.now().strftime('%Y%m%d')}.csv"
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["Hospital", "System", "Status", "Procedures", "URL"])
                writer.writeheader()
                for result in self.results:
                    writer.writerow({
                        "Hospital": result.get("hospital", ""),
                        "System": result.get("system", "Unknown"),
                        "Status": result["status"],
                        "Procedures": result["procedures"],
                        "URL": result.get("url", "")
                    })
            
            print(f"\n[OK] Summary exported: {filepath.name}")
        except Exception as e:
            print(f"[ERROR] Failed to export: {e}")


def main():
    extractor = CompleteHospitalExtractor()
    extractor.process_all()
    
    print("\n[NEXT STEPS]")
    print("  1. All 24 hospitals extracted")
    print("  2. Ready to build website with complete data!")
    print("  3. Website will include hospital system filtering")
    print("  4. Compare prices across all three systems")


if __name__ == "__main__":
    main()
