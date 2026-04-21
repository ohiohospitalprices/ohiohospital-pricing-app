#!/usr/bin/env python3
import json
import re

# Load procedures
with open('procedures.json', 'r') as f:
    procedures = json.load(f)

print(f"Total procedures: {len(procedures)}")

# Check current categories
category_counts = {}
for proc in procedures:
    cat = proc.get('category', 'MISSING')
    category_counts[cat] = category_counts.get(cat, 0) + 1

print("\n=== BEFORE FIX ===")
for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
    print(f"{cat}: {count}")

def assign_category(procedure):
    """Assign category based on CPT code and procedure name."""
    cpt = procedure.get('cpt', '')
    name = procedure.get('procedure', '').lower()
    
    # Extract numeric part of CPT (handles custom formats)
    cpt_numeric = re.sub(r'\D', '', cpt)
    
    # Name-based keywords (highest priority)
    if any(x in name for x in ['mri', 'ct scan', 'x-ray', 'ultrasound', 'imaging', 'scan']):
        return 'Imaging'
    if any(x in name for x in ['lab', 'blood', 'test', 'specimen', 'culture']):
        return 'Lab'
    if any(x in name for x in ['therapy', 'pt ', 'physical therapy', 'occupational', 'rehabilitation']):
        return 'Therapy'
    if any(x in name for x in ['pharmacy', 'drug', 'medication', 'injection']):
        return 'Pharmacy'
    if any(x in name for x in ['room', 'bed', 'hc room', 'inpatient', 'hospital room']):
        return 'Room'
    if any(x in name for x in ['surgery', 'surgical', 'operating', 'procedure room']):
        return 'Surgical'
    if any(x in name for x in ['emergency', 'er ', 'ed visit', 'urgent']):
        return 'ER'
    
    # CPT code ranges
    if cpt_numeric:
        code = int(cpt_numeric)
        if 10000 <= code <= 69999:
            return 'Surgical'
        elif 70000 <= code <= 79999:
            return 'Imaging'
        elif 80000 <= code <= 89999:
            return 'Lab'
        elif 90000 <= code <= 99999:
            if 99200 <= code <= 99499:
                return 'ER'
            else:
                return 'Pharmacy'
        elif 97000 <= code <= 97999:
            return 'Therapy'
    
    return 'Other'

# Fix categories
for proc in procedures:
    proc['category'] = assign_category(proc)

# Check new categories
category_counts_fixed = {}
for proc in procedures:
    cat = proc.get('category', 'MISSING')
    category_counts_fixed[cat] = category_counts_fixed.get(cat, 0) + 1

print("\n=== AFTER FIX ===")
for cat, count in sorted(category_counts_fixed.items(), key=lambda x: -x[1]):
    print(f"{cat}: {count}")

# Check if all categories have 10+
print("\n=== VALIDATION ===")
all_valid = True
for cat, count in category_counts_fixed.items():
    status = "OK" if count >= 10 else "FAIL"
    print(f"[{status}] {cat}: {count} (need 10+)")
    if count < 10:
        all_valid = False

# Save fixed procedures
with open('procedures.json', 'w') as f:
    json.dump(procedures, f, indent=2)

print(f"\n[OK] Saved {len(procedures)} procedures to procedures.json")
if all_valid:
    print("[OK] All categories have 10+ procedures")
else:
    print("[WARN] Some categories have <10 procedures")
