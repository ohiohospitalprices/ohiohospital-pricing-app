#!/usr/bin/env python3
import sqlite3
import json

db_path = r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db'
db = sqlite3.connect(db_path)
cursor = db.cursor()

# Get all hospitals
cursor.execute("SELECT hospital_id, name FROM hospitals ORDER BY hospital_id;")
hospitals = {row[0]: row[1] for row in cursor.fetchall()}
print(f"Found {len(hospitals)} hospitals: {list(hospitals.values())}")

# Get all procedures with pricing
cursor.execute("""
SELECT 
  p.procedure_id,
  p.hospital_id,
  p.procedure_code,
  p.procedure_name,
  p.description,
  pr.negotiated_rate,
  pr.gross_charge
FROM procedures p
LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
ORDER BY p.hospital_id, p.procedure_id;
""")

# Build nested structure
data_by_hospital = {h_id: {"name": h_name, "procedures": []} for h_id, h_name in hospitals.items()}

for proc_id, hospital_id, cpt_code, proc_name, description, neg_rate, gross_charge in cursor.fetchall():
    if hospital_id not in data_by_hospital:
        continue
    
    # Use gross_charge as price, fallback to negotiated_rate
    price = gross_charge if gross_charge is not None else neg_rate
    
    procedure_entry = {
        "name": proc_name,
        "cpt": cpt_code,
        "category": description or "General",
        "price": float(price) if price else None
    }
    data_by_hospital[hospital_id]["procedures"].append(procedure_entry)

# Verify counts
print(f"\nData by hospital:")
for h_id in sorted(data_by_hospital.keys()):
    data = data_by_hospital[h_id]
    proc_count = len(data['procedures'])
    priced_count = sum(1 for p in data['procedures'] if p['price'] is not None)
    print(f"  {data['name']}: {proc_count} procedures ({priced_count} with prices)")

# Save as JSON
output = [data_by_hospital[h_id] for h_id in sorted(data_by_hospital.keys())]

with open(r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\procedures.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nSaved procedures.json with {len(output)} hospitals")
total_procs = sum(len(h['procedures']) for h in output)
print(f"Total procedures across all hospitals: {total_procs}")

# Sample output
print(f"\nSample (first hospital, first 3 procedures):")
if output and output[0]["procedures"]:
    sample = {"name": output[0]["name"], "procedures": output[0]["procedures"][:3]}
    print(json.dumps(sample, indent=2))

db.close()
