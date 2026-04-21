#!/usr/bin/env python3
import sqlite3
import json

db_path = r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db'
db = sqlite3.connect(db_path)
cursor = db.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables found: {tables}")

# Get schema for first table
if tables:
    cursor.execute(f"PRAGMA table_info({tables[0][0]});")
    schema = cursor.fetchall()
    print(f"\nSchema of {tables[0][0]}:")
    for col in schema:
        print(f"  {col}")

db.close()
