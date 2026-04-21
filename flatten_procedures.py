#!/usr/bin/env python3
import json

# Load nested structure
with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json', 'r') as f:
    hospitals = json.load(f)

# Flatten to array of procedures with hospital name
flat = []
for hospital in hospitals:
    for proc in hospital['procedures']:
        flat.append({
            "hospital": hospital['name'],
            "procedure": proc['name'],
            "cpt": proc['cpt'],
            "price": proc['price'],
            "category": proc.get('category', 'General')
        })

# Save flattened array
with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json', 'w') as f:
    json.dump(flat, f, separators=(',', ':'))

print(f"Flattened to {len(flat)} total procedure records")
print(f"Sample: {flat[0]}")

import os
size = os.path.getsize(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json')
print(f"File size: {size / 1024 / 1024:.1f} MB")
