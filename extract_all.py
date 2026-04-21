#!/usr/bin/env python3
import sqlite3
import json

db_path = r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db'
db = sqlite3.connect(db_path)
cursor = db.cursor()

# Get all hospitals
cursor.execute("SELECT hospital_id, name FROM hospitals;")
hospitals = {row[0]: row[1] for row in cursor.fetchall()}
print(f"Found {len(hospitals)} hospitals: {list(hospitals.values())}")

# Get all procedures with their CPT and pricing
cursor.execute("""
SELECT p.procedure_id, p.name, p.cpt_code, p.category, pr.hospital_id, pr.price
FROM procedures p
LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
ORDER BY p.procedure_id, pr.hospital_id;
""")

# Build nested structure
data_by_hospital = {h_id: {"name": h_name, "procedures": []} for h_id, h_name in hospitals.items()}

rows = cursor.fetchall()
current_proc_id = None
current_proc_data = None

for proc_id, proc_name, cpt_code, category, hospital_id, price in rows:
    if proc_id != current_proc_id:
        current_proc_id = proc_id
        current_proc_data = {
            "name": proc_name,
            "cpt": cpt_code,
            "category": category
        }
    
    if hospital_id and price is not None:
        proc_with_price = {
            **current_proc_data,
            "price": float(price)
        }
        data_by_hospital[hospital_id]["procedures"].append(proc_with_price)

# Verify counts
print(f"\nData by hospital:")
for h_id, data in data_by_hospital.items():
    print(f"  {data['name']}: {len(data['procedures'])} procedures")

# Save as JSON
output = [data_by_hospital[h_id] for h_id in sorted(data_by_hospital.keys())]

with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\procedures.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nSaved procedures.json with {len(output)} hospitals")
print(f"Total procedures across all hospitals: {sum(len(h['procedures']) for h in output)}")

# Sample output
print(f"\nSample (first hospital, first 2 procedures):")
if output and output[0]["procedures"]:
    print(json.dumps(output[0:1], indent=2)[:500])

db.close()
