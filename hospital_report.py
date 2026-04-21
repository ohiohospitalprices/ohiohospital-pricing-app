#!/usr/bin/env python3
import json

# Load procedures
with open('procedures.json', 'r') as f:
    procedures = json.load(f)

# Group by hospital and category
hospital_categories = {}
for proc in procedures:
    hospital = proc.get('hospital', 'Unknown')
    category = proc.get('category', 'Unknown')
    
    if hospital not in hospital_categories:
        hospital_categories[hospital] = {}
    
    hospital_categories[hospital][category] = hospital_categories[hospital].get(category, 0) + 1

# Print report
print("=== PROCEDURE COUNT PER HOSPITAL & CATEGORY ===\n")

# Overall stats first
print("OVERALL STATISTICS:")
category_totals = {}
for hospital, cats in hospital_categories.items():
    for cat, count in cats.items():
        category_totals[cat] = category_totals.get(cat, 0) + count

for cat in sorted(category_totals.keys()):
    print(f"  {cat}: {category_totals[cat]:,}")
print(f"  TOTAL: {len(procedures):,}\n")

# Per hospital
print("BY HOSPITAL:")
for hospital in sorted(hospital_categories.keys()):
    cats = hospital_categories[hospital]
    total = sum(cats.values())
    print(f"\n{hospital} ({total:,} total)")
    for cat in sorted(cats.keys()):
        print(f"  {cat}: {cats[cat]:,}")

print(f"\n=== {len(hospital_categories)} HOSPITALS TOTAL ===")
