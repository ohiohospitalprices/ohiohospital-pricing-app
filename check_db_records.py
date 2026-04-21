import sqlite3
import os

db_path = r'C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("=== DATABASE TABLES ===")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\nTable: {table_name}")
        print(f"Records: {count:,}")
        
        # Show schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"Columns: {', '.join([col[1] for col in columns])}")
    
    # Check file size
    file_size = os.path.getsize(db_path)
    print(f"\n=== DATABASE FILE ===")
    print(f"Path: {db_path}")
    print(f"Size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
