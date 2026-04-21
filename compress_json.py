#!/usr/bin/env python3
import json

# Read the pretty JSON
with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json', 'r') as f:
    data = json.load(f)

# Write compressed JSON (no whitespace)
with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json', 'w') as f:
    json.dump(data, f, separators=(',', ':'))

import os
size = os.path.getsize(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing\procedures.json')
print(f"Compressed size: {size / 1024 / 1024:.1f} MB")
