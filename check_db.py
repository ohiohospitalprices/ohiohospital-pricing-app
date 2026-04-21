import sqlite3

conn = sqlite3.connect('hospital_pricing.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check procedures schema
cursor.execute("PRAGMA table_info(procedures)")
cols = cursor.fetchall()
print("\nProcedures columns:", [(c[1], c[2]) for c in cols])

# Check data
cursor.execute("SELECT COUNT(*) FROM procedures")
print("Procedure count:", cursor.fetchone()[0])

cursor.execute("SELECT * FROM procedures LIMIT 3")
rows = cursor.fetchall()
print("Sample procedures:", rows)

conn.close()
