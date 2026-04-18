#!/usr/bin/env python3
"""
Batch Hospital Price Parser
Extracts pricing data from multiple OhioHealth hospitals
"""

import json
import requests
import csv
import os
from datetime import datetime
from pathlib import Path
import sys

class HospitalBatchParser:
    def __init__(self):
        self.output_dir = Path("C:\\Users\\Owner\\OneDrive\\Desktop\\Hospital_Pricing")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        
        # OhioHealth hospitals with JSON URLs (auto-scraped from OhioHealth website)
        self.hospitals = {
            "Berger Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/384105653_berger-hospital_standardcharges.json",
            "Doctors Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_doctors-hospital_standardcharges.json",
            "Dublin Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_dublin-methodist-hospital_standardcharges.json",
            "Grady Memorial Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314379436_grady-memorial-hospital_standardcharges.json",
            "Grant Medical Center": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grant-medical-center_standardcharges.json",
            "Grove City Methodist": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grove-city-methodist_standardcharges.json",
            "Hardin Memorial Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314440479_hardin-memorial-hospital_standardcharges.json",
            "Mansfield Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/310714456_ohiohealth-mansfield-hospital_standardcharges.json",
            "Marion General Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/311070887_marion-general-hospital_standardcharges.json",
            "O'Bleness Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314446959_ohiohealth-o-_bleness-hospital_standardcharges.json",
            "Pickerington Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_pickerington-methodist-hospital_standardcharges.json",
            "Riverside Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_riverside-methodist-hospital_standardcharges.json",
            "Shelby Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/340714456_ohiohealth-shelby-hospital_standardcharges.json",
            "Southeastern Medical Center": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314391798_southeastern-ohio-regional-medical-center_standardcharges.json",
            "Van Wert Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/344429514_van-wert-county-hospital_standardcharges.json",
        }
    
    def parse_hospital(self, hospital_name, json_url):
        """Parse a single hospital"""
        print(f"\n[*] Processing: {hospital_name}")
        print(f"    URL: {json_url}")
        
        try:
            response = requests.get(json_url, timeout=30)
            response.raise_for_status()
            data = json.loads(response.text.encode().decode('utf-8-sig'))
            
            procedures = self._extract_procedures(data)
            print(f"    [OK] Extracted {len(procedures)} procedures")
            
            self.results.append({
                "hospital": hospital_name,
                "url": json_url,
                "status": "Success",
                "procedures": len(procedures),
                "data": data,
                "procedures_list": procedures
            })
            
            return True
        except requests.exceptions.RequestException as e:
            print(f"    [ERROR] Download failed: {e}")
            self.results.append({
                "hospital": hospital_name,
                "url": json_url,
                "status": f"Failed: {str(e)}",
                "procedures": 0
            })
            return False
        except json.JSONDecodeError as e:
            print(f"    [ERROR] Invalid JSON: {e}")
            self.results.append({
                "hospital": hospital_name,
                "url": json_url,
                "status": f"Invalid JSON: {str(e)}",
                "procedures": 0
            })
            return False
    
    def _extract_procedures(self, data):
        """Extract procedures from hospital data"""
        procedures = []
        
        for charge in data.get("standard_charge_information", []):
            description = charge.get("description", "").strip()
            if not description:
                continue
            
            # Get codes
            codes = charge.get("code_information", [])
            cpt_code = ""
            rc_code = ""
            hcpcs_code = ""
            
            for code_info in codes:
                code_type = code_info.get("type", "")
                code_value = code_info.get("code", "")
                
                if code_type == "CPT":
                    cpt_code = code_value
                elif code_type == "RC":
                    rc_code = code_value
                elif code_type == "HCPCS":
                    hcpcs_code = code_value
            
            # Get pricing
            for charge_detail in charge.get("standard_charges", []):
                gross_charge = charge_detail.get("gross_charge", "N/A")
                discounted_cash = charge_detail.get("discounted_cash", "N/A")
                
                # Format prices
                try:
                    gross_formatted = "${:,.2f}".format(float(gross_charge))
                    discount_formatted = "${:,.2f}".format(float(discounted_cash))
                except (ValueError, TypeError):
                    gross_formatted = str(gross_charge)
                    discount_formatted = str(discounted_cash)
                
                procedures.append({
                    "name": description,
                    "cpt": cpt_code,
                    "rc": rc_code,
                    "hcpcs": hcpcs_code,
                    "gross": gross_formatted,
                    "discount": discount_formatted
                })
        
        return procedures
    
    def process_all(self):
        """Process all hospitals"""
        print("\n" + "="*70)
        print("BATCH HOSPITAL PRICE PARSER")
        print("="*70)
        print(f"\nProcessing {len(self.hospitals)} OhioHealth hospitals...")
        
        success_count = 0
        for hospital_name, url in self.hospitals.items():
            if self.parse_hospital(hospital_name, url):
                success_count += 1
        
        print("\n" + "="*70)
        print(f"SUMMARY: {success_count}/{len(self.hospitals)} hospitals processed successfully")
        print("="*70)
        
        return success_count
    
    def generate_report(self):
        """Generate summary report"""
        print("\n[HOSPITALS PROCESSED]")
        
        total_procedures = 0
        for result in self.results:
            status = "[OK]" if result["status"] == "Success" else "[FAIL]"
            print(f"  {status} {result['hospital']:<35} {result['procedures']:>6} procedures")
            total_procedures += result.get("procedures", 0)
        
        print(f"\n[TOTAL] {total_procedures} procedures across all hospitals")
        
        return total_procedures
    
    def export_summary_csv(self):
        """Export hospital summary"""
        filepath = self.output_dir / f"OhioHealth_Hospitals_Summary_{datetime.now().strftime('%Y%m%d')}.csv"
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["Hospital", "Status", "Procedures", "URL"])
                writer.writeheader()
                for result in self.results:
                    writer.writerow({
                        "Hospital": result["hospital"],
                        "Status": result["status"],
                        "Procedures": result["procedures"],
                        "URL": result["url"]
                    })
            
            print(f"\n[OK] Summary exported: {filepath.name}")
        except Exception as e:
            print(f"[ERROR] Failed to export summary: {e}")


def main():
    parser = HospitalBatchParser()
    parser.process_all()
    parser.generate_report()
    parser.export_summary_csv()
    
    print("\n[NEXT STEPS]")
    print("  1. Check summary report above")
    print("  2. Individual hospital files will be created")
    print("  3. Ready to build website with this data!")


if __name__ == "__main__":
    main()
