#!/usr/bin/env python3
"""
Test Mount Carmel integration - verify categories and procedures
"""

import sqlite3
from pathlib import Path

DB_PATH = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\ohiohospital-pricing-app\hospital_pricing.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 80)
print("MOUNT CARMEL INTEGRATION TEST")
print("=" * 80)

# Test 1: Verify Mount Carmel hospitals exist
print("\n1. Mount Carmel Hospitals in Database:")
cursor.execute('''
    SELECT id, name FROM hospitals 
    WHERE name LIKE '%Mount Carmel%' OR name LIKE '%Diley Ridge%'
    ORDER BY name
''')
hospitals = cursor.fetchall()
for hid, hname in hospitals:
    cursor.execute('SELECT COUNT(*) FROM procedures WHERE hospital_id = ?', (hid,))
    count = cursor.fetchone()[0]
    print(f"   {hname}: {count} procedures")

# Test 2: Check categories for each Mount Carmel hospital
print("\n2. Categories per Mount Carmel Hospital:")
for hid, hname in hospitals:
    cursor.execute('''
        SELECT DISTINCT category, COUNT(*) as count
        FROM procedures
        WHERE hospital_id = ?
        GROUP BY category
        ORDER BY count DESC
    ''', (hid,))
    categories = cursor.fetchall()
    print(f"\n   {hname}:")
    for category, count in categories:
        print(f"     {category}: {count}")

# Test 3: Sample procedures from Mount Carmel East
print("\n3. Sample Procedures from Mount Carmel East:")
cursor.execute('''
    SELECT procedure, cpt, price, category
    FROM procedures
    WHERE hospital_id = (SELECT id FROM hospitals WHERE name = 'Mount Carmel East')
    LIMIT 10
''')
for procedure, cpt, price, category in cursor.fetchall():
    print(f"   {procedure[:50]:<50} | CPT: {cpt:<8} | ${price:>8.2f} | {category}")

# Test 4: Verify all hospitals have multiple categories
print("\n4. Hospital Category Coverage (all hospitals):")
cursor.execute('''
    SELECT h.name, COUNT(DISTINCT p.category) as num_categories
    FROM hospitals h
    LEFT JOIN procedures p ON h.id = p.hospital_id
    GROUP BY h.id, h.name
    ORDER BY num_categories DESC
''')
for hname, num_cats in cursor.fetchall():
    print(f"   {hname:<40} {num_cats} categories")

# Test 5: Overall statistics
print("\n5. Overall Statistics:")
cursor.execute('SELECT COUNT(*) FROM procedures')
total_procs = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM hospitals')
total_hosps = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(DISTINCT category) FROM procedures')
total_cats = cursor.fetchone()[0]

print(f"   Total Procedures: {total_procs:,}")
print(f"   Total Hospitals: {total_hosps}")
print(f"   Total Categories: {total_cats}")

cursor.execute('SELECT DISTINCT category FROM procedures ORDER BY category')
cats = [c[0] for c in cursor.fetchall()]
print(f"   Categories: {', '.join(cats)}")

conn.close()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
