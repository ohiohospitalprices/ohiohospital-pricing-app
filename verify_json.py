import json

with open('procedures.json', 'r') as f:
    data = json.load(f)

print(f"Total records in JSON: {len(data)}")

# Count by hospital
from collections import Counter
hospitals = Counter([r.get('hospital') for r in data])
print(f"\nRecords by hospital:")
for hospital, count in sorted(hospitals.items(), key=lambda x: x[1], reverse=True):
    print(f"  {hospital}: {count}")

# Check OSU hospitals
osu_records = [r for r in data if r.get('hospital') and 'OSU' in r.get('hospital')]
print(f"\nTotal OSU records: {len(osu_records)}")

arthur_records = [r for r in data if r.get('hospital') and 'Arthur' in r.get('hospital')]
print(f"Total Arthur G James records: {len(arthur_records)}")

# Sample a few OSU records
print("\nSample OSU records:")
for record in osu_records[:3]:
    print(f"  {record}")
