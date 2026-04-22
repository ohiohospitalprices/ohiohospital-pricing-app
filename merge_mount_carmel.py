#!/usr/bin/env python3
"""
Merge Mount Carmel hospital data with existing combined procedures.json
Converts Mount Carmel format to match existing format and merges.
"""

import json
import sys
from pathlib import Path

def categorize_procedure(procedure_name, cpt_code=None):
    """Categorize procedure based on name and CPT code"""
    name_lower = procedure_name.lower()
    
    # Check for specific categories
    if any(word in name_lower for word in ['room', 'bed', 'board']):
        return 'Room'
    elif any(word in name_lower for word in ['implant', 'device', 'prosth']):
        return 'Implants'
    elif any(word in name_lower for word in ['anesthesia', 'anesthes']):
        return 'Anesthesia'
    elif any(word in name_lower for word in ['imaging', 'xray', 'x-ray', 'ct scan', 'mri', 'ultrasound', 'imaging']):
        return 'Imaging'
    elif any(word in name_lower for word in ['lab', 'test', 'pathology', 'blood', 'culture']):
        return 'Lab'
    elif any(word in name_lower for word in ['therapy', 'physical', 'rehab', 'rehabilitation']):
        return 'Therapy'
    elif any(word in name_lower for word in ['physician', 'professional', 'surgeon', 'doctor']):
        return 'Professional'
    else:
        return 'Surgery'

def convert_mount_carmel_data(input_file, output_procedures, existing_procedures_file):
    """
    Convert Mount Carmel data to combined format and merge
    """
    print(f"Reading Mount Carmel data: {input_file}")
    with open(input_file, 'r') as f:
        mc_data = json.load(f)
    
    print(f"Mount Carmel procedures count: {len(mc_data['procedures'])}")
    
    # Read existing procedures
    print(f"Reading existing procedures: {existing_procedures_file}")
    with open(existing_procedures_file, 'r') as f:
        existing_procedures = json.load(f)
    
    print(f"Existing procedures count: {len(existing_procedures)}")
    
    # Convert Mount Carmel procedures to match existing format
    converted = []
    hospital_map = {
        "Mount Carmel East": "Mount Carmel East",
        "Mount Carmel Grove City": "Mount Carmel Grove City",
        "Mount Carmel New Albany": "Mount Carmel New Albany",
        "Mount Carmel St. Ann's": "Mount Carmel St. Ann's",
        "Diley Ridge Medical Center": "Diley Ridge Medical Center",
        "Mount Carmel Dublin Hospital": "Mount Carmel Dublin",
        "Mount Carmel Dublin": "Mount Carmel Dublin"
    }
    
    for proc in mc_data['procedures']:
        hospital_name = proc.get('hospital_name', '')
        
        # Skip if hospital name not recognized
        if hospital_name not in hospital_map:
            continue
        
        # Use gross_charge as primary price, fallback to discounted or negotiated
        price = proc.get('gross_charge')
        if price is None or price == 0:
            price = proc.get('discounted_cash_price', 0)
        if price is None or price == 0:
            price = proc.get('negotiated_rate', 0)
        
        if price is None:
            price = 0
        
        # Use CPT code, fallback to code if available
        cpt = proc.get('cpt_code', '')
        if not cpt:
            cpt = proc.get('code', '')
        
        category = categorize_procedure(proc.get('procedure_name', ''), cpt)
        
        converted_proc = {
            "hospital": hospital_map[hospital_name],
            "procedure": proc.get('procedure_name', ''),
            "cpt": str(cpt),
            "price": float(price),
            "category": category
        }
        
        converted.append(converted_proc)
    
    print(f"Converted Mount Carmel procedures: {len(converted)}")
    
    # Merge with existing data
    merged = existing_procedures + converted
    
    # Write merged data
    print(f"Writing merged data: {output_procedures}")
    with open(output_procedures, 'w') as f:
        json.dump(merged, f)
    
    print(f"Total procedures after merge: {len(merged)}")
    
    # Print hospital summary
    hospitals = {}
    for proc in merged:
        h = proc['hospital']
        hospitals[h] = hospitals.get(h, 0) + 1
    
    print("\nHospital Summary:")
    for hospital, count in sorted(hospitals.items()):
        print(f"  {hospital}: {count}")
    
    return merged

if __name__ == '__main__':
    mount_carmel_file = r"C:\Users\Owner\OneDrive\Desktop\Hospital_Pricing\Mount_Carmel_Hospital_Data\mount_carmel_procedures.json"
    existing_file = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\ohiohospital-pricing-app\hospital_data\procedures.json"
    output_file = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\ohiohospital-pricing-app\hospital_data\procedures.json"
    
    convert_mount_carmel_data(mount_carmel_file, output_file, existing_file)
    print("✓ Merge complete!")
