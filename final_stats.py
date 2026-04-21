import sqlite3
from pathlib import Path
from datetime import datetime

db_path = r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count stats
cursor.execute('SELECT COUNT(*) FROM hospitals')
h_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM procedures')
p_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM pricing')
pr_count = cursor.fetchone()[0]

# Get breakdown
cursor.execute('''
SELECT h.name, h.system, COUNT(DISTINCT p.procedure_id) as proc_count
FROM hospitals h
LEFT JOIN procedures p ON h.hospital_id = p.hospital_id
GROUP BY h.hospital_id
ORDER BY proc_count DESC
''')
breakdown = cursor.fetchall()

print("\n" + "="*80)
print("HOSPITAL PRICING DATABASE - FINAL STATISTICS")
print("="*80)
print(f"\nDatabase: {db_path}")
print(f"Size: {Path(db_path).stat().st_size / (1024*1024):.1f} MB")
print(f"Generated: {datetime.now().isoformat()}")
print(f"\nTotal Hospitals: {h_count}")
print(f"Total Procedures: {p_count:,}")
print(f"Total Pricing Records: {pr_count:,}")

print("\n" + "-"*80)
print(f"{'Hospital':<40} {'System':<20} {'Procedures':>15}")
print("-" * 80)

total_check = 0
for name, system, count in breakdown:
    print(f"{name:<40} {system:<20} {count:>15,}")
    total_check += count

print("-" * 80)

# System totals
cursor.execute('''
SELECT h.system, COUNT(DISTINCT p.procedure_id) as proc_count
FROM hospitals h
LEFT JOIN procedures p ON h.hospital_id = p.hospital_id
GROUP BY h.system
ORDER BY proc_count DESC
''')
systems = cursor.fetchall()

print("\nBy System:")
for system, count in systems:
    pct = (count / p_count * 100) if p_count > 0 else 0
    print(f"  {system:<30} {count:>15,}  ({pct:>5.1f}%)")

print("\n" + "="*80)
print("\nDatabase is ready for Flask API integration.")
print("Use HOSPITAL_DB_SCHEMA.md for connection details.")
print("="*80 + "\n")

conn.close()
