#!/usr/bin/env python3
import json

with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json', 'r') as f:
    data = json.load(f)

print(f"Valid JSON with {len(data)} hospitals\n")

for hospital in data[:5]:
    proc_count = len(hospital['procedures'])
    if proc_count > 0:
        sample = hospital['procedures'][0]
        print(f"Hospital: {hospital['name']}")
        print(f"  Procedures: {proc_count}")
        print(f"  Sample: {sample['name']}")
        print(f"           CPT: {sample['cpt']}, Price: ${sample['price']:.2f}\n")
