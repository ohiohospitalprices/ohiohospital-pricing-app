import sqlite3
conn = sqlite3.connect('hospital_pricing.db')
cursor = conn.cursor()

# Check hospital count
cursor.execute('SELECT COUNT(*) FROM hospitals')
print(f'Total hospitals: {cursor.fetchone()[0]}')

# Check hospitals
cursor.execute('SELECT name FROM hospitals ORDER BY name')
hospitals = cursor.fetchall()
for row in hospitals:
    print(f'  - {row[0]}')

# Check OSU count
cursor.execute('SELECT COUNT(*) FROM pricing WHERE hospital_id IN (SELECT id FROM hospitals WHERE name LIKE "%OSU%")')
osu_count = cursor.fetchone()[0]
print(f'\nOSU pricing records: {osu_count}')

# Check specific hospitals
cursor.execute("SELECT id, name FROM hospitals WHERE name LIKE '%OSU%' OR name LIKE '%Arthur%'")
osu_hospitals = cursor.fetchall()
print(f'\nOSU-related hospitals in DB:')
for hid, hname in osu_hospitals:
    print(f'  ID {hid}: {hname}')

conn.close()
