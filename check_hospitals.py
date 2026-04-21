#!/usr/bin/env python3
import json

with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json', 'r') as f:
    data = json.load(f)

print(f"Total hospitals: {len(data)}\n")
for i, hospital in enumerate(data, 1):
    proc_count = len(hospital['procedures'])
    print(f"{i}. {hospital['name']}: {proc_count} procedures")
    if proc_count > 0 and i <= 3:  # Show sample procs for first 3 hospitals
        print(f"   Sample procedures:")
        for proc in hospital['procedures'][:2]:
            print(f"     - {proc['name']} (CPT: {proc['cpt']}, Price: ${proc['price']:.2f})")
