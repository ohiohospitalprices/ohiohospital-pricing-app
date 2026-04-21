#!/usr/bin/env python3
import sqlite3

db_path = r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db'
db = sqlite3.connect(db_path)
cursor = db.cursor()

for table in ['hospitals', 'procedures', 'pricing']:
    cursor.execute(f"PRAGMA table_info({table});")
    schema = cursor.fetchall()
    print(f"\n{table}:")
    for col in schema:
        print(f"  {col[1]} ({col[2]})")
    
    # Sample data
    cursor.execute(f"SELECT * FROM {table} LIMIT 2;")
    rows = cursor.fetchall()
    if rows:
        print(f"  Sample: {rows[0]}")

db.close()
