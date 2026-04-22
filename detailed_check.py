import sqlite3

conn = sqlite3.connect('hospital_pricing.db')
cursor = conn.cursor()

# Get OSU hospital IDs
cursor.execute("SELECT id FROM hospitals WHERE name LIKE '%OSU%'")
osu_ids = [row[0] for row in cursor.fetchall()]
print(f"OSU Hospital IDs: {osu_ids}")

# Count by each OSU hospital
for hid in osu_ids:
    cursor.execute("SELECT name FROM hospitals WHERE id = ?", (hid,))
    name = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pricing WHERE hospital_id = ?", (hid,))
    count = cursor.fetchone()[0]
    print(f"  {name}: {count} procedures")

# Check procedure types for OSU
cursor.execute("""
    SELECT pr.category, COUNT(*) as count
    FROM pricing p
    JOIN procedures pr ON p.procedure_id = pr.id
    WHERE p.hospital_id IN (SELECT id FROM hospitals WHERE name LIKE '%OSU%')
    GROUP BY pr.category
    ORDER BY count DESC
""")
print("\nProcedure categories for OSU hospitals:")
for category, count in cursor.fetchall():
    print(f"  {category}: {count}")

# Check Arthur G James
cursor.execute("SELECT id FROM hospitals WHERE name = 'Arthur G James Cancer Hospital'")
arthur_id = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM pricing WHERE hospital_id = ?", (arthur_id,))
arthur_count = cursor.fetchone()[0]
print(f"\nArthur G James Cancer Hospital: {arthur_count} procedures")

conn.close()
