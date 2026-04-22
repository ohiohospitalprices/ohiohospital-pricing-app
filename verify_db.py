#!/usr/bin/env python
"""Verify database contents after rebuild"""

import sqlite3

conn = sqlite3.connect('hospital_pricing.db')
cursor = conn.cursor()

# Verify all 23 hospitals are there
cursor.execute('SELECT COUNT(*) FROM hospitals')
print(f'Total hospitals: {cursor.fetchone()[0]}')

# List hospitals
cursor.execute('SELECT name FROM hospitals ORDER BY name')
hospitals = [h[0] for h in cursor.fetchall()]
print(f'\nHospitals ({len(hospitals)}):')
for h in hospitals:
    print(f'  - {h}')

# Check OSU and Mount Carmel specifically
cursor.execute('''
    SELECT COUNT(*) FROM pricing p 
    JOIN hospitals h ON p.hospital_id = h.id 
    WHERE h.name = ?
''', ['OSU Wexner Medical Center'])
osu_count = cursor.fetchone()[0]
print(f'\nOSU Wexner Medical Center procedures: {osu_count}')

cursor.execute('''
    SELECT COUNT(*) FROM pricing p 
    JOIN hospitals h ON p.hospital_id = h.id 
    WHERE h.name = ?
''', ['Mount Carmel Delaware'])
mount_carmel_delaware = cursor.fetchone()[0]
print(f'Mount Carmel Delaware procedures: {mount_carmel_delaware}')

# Test search for MRI at OSU
cursor.execute('''
    SELECT DISTINCT p.name, p.cpt, pr.price 
    FROM procedures p
    JOIN pricing pr ON p.id = pr.procedure_id
    JOIN hospitals h ON pr.hospital_id = h.id
    WHERE h.name = ? AND p.name LIKE ?
    LIMIT 5
''', ['OSU Wexner Medical Center', '%MRI%'])
mri_results = cursor.fetchall()
print(f'\nMRI procedures at OSU Wexner (sample):')
if mri_results:
    for name, cpt, price in mri_results:
        print(f'  - {name} ({cpt}): ${price}')
else:
    print('  (No MRI procedures found)')

# Check categories
cursor.execute('SELECT DISTINCT category FROM procedures ORDER BY category')
categories = [c[0] for c in cursor.fetchall()]
print(f'\nCategories ({len(categories)}):')
for cat in categories:
    cursor.execute('SELECT COUNT(*) FROM procedures WHERE category = ?', [cat])
    count = cursor.fetchone()[0]
    print(f'  - {cat}: {count} procedures')

conn.close()
