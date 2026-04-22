import sqlite3
import json

conn = sqlite3.connect('hospital_pricing.db')
cursor = conn.cursor()

# Test 1: Search for MRI at OSU Wexner Medical Center
print("=" * 60)
print("Test 1: MRI at OSU Wexner Medical Center")
print("=" * 60)
cursor.execute("""
    SELECT pr.name, pr.cpt, p.price
    FROM pricing p
    JOIN procedures pr ON p.procedure_id = pr.id
    JOIN hospitals h ON p.hospital_id = h.id
    WHERE h.name = 'OSU Wexner Medical Center'
    AND pr.name LIKE '%MRI%'
    LIMIT 5
""")
results = cursor.fetchall()
print(f"Found {len(results)} MRI procedures at OSU Wexner Medical Center")
for name, cpt, price in results:
    print(f"  - {name} (CPT: {cpt}) - ${price:,.2f}")

# Test 2: Search for CT at OSU Wexner Medical Center
print("\n" + "=" * 60)
print("Test 2: CT at OSU Wexner Medical Center")
print("=" * 60)
cursor.execute("""
    SELECT pr.name, pr.cpt, p.price
    FROM pricing p
    JOIN procedures pr ON p.procedure_id = pr.id
    JOIN hospitals h ON p.hospital_id = h.id
    WHERE h.name = 'OSU Wexner Medical Center'
    AND pr.name LIKE '%CT%'
    LIMIT 5
""")
results = cursor.fetchall()
print(f"Found {len(results)} CT procedures at OSU Wexner Medical Center")
for name, cpt, price in results:
    print(f"  - {name} (CPT: {cpt}) - ${price:,.2f}")

# Test 3: Arthur G James search
print("\n" + "=" * 60)
print("Test 3: All hospitals with OSU in name")
print("=" * 60)
cursor.execute("""
    SELECT h.name, COUNT(*) as procedure_count
    FROM pricing p
    JOIN hospitals h ON p.hospital_id = h.id
    WHERE h.name LIKE '%OSU%' OR h.name LIKE '%Arthur%'
    GROUP BY h.name
""")
results = cursor.fetchall()
for name, count in results:
    print(f"  - {name}: {count} procedures")

# Test 4: Database summary
print("\n" + "=" * 60)
print("Database Summary")
print("=" * 60)
cursor.execute('SELECT COUNT(*) FROM hospitals')
print(f"Total hospitals: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM procedures')
print(f"Total procedures: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM pricing')
print(f"Total pricing records: {cursor.fetchone()[0]}")

conn.close()
