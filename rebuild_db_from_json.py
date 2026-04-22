#!/usr/bin/env python3
"""
Rebuild hospital pricing database from merged procedures.json
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\ohiohospital-pricing-app\hospital_pricing.db"
PROCEDURES_FILE = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\ohiohospital-pricing-app\hospital_data\procedures.json"

def rebuild_database():
    """Rebuild database from merged procedures.json"""
    
    # Load the merged procedures
    print(f"Loading procedures from: {PROCEDURES_FILE}")
    with open(PROCEDURES_FILE, 'r') as f:
        procedures = json.load(f)
    
    print(f"Total procedures: {len(procedures)}")
    
    # Remove old database
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()
        print(f"Removed old database: {DB_PATH}")
    
    # Create new database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating database schema...")
    
    cursor.execute('''
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE procedures (
            id INTEGER PRIMARY KEY,
            hospital_id INTEGER NOT NULL,
            procedure TEXT NOT NULL,
            cpt TEXT,
            price REAL,
            category TEXT,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
    ''')
    
    cursor.execute('CREATE INDEX idx_hospital_id ON procedures(hospital_id)')
    cursor.execute('CREATE INDEX idx_procedure ON procedures(procedure)')
    cursor.execute('CREATE INDEX idx_category ON procedures(category)')
    
    # Get unique hospitals
    hospitals = {}
    for proc in procedures:
        hospital_name = proc['hospital']
        if hospital_name not in hospitals:
            hospitals[hospital_name] = None
    
    # Insert hospitals
    print(f"Inserting {len(hospitals)} hospitals...")
    for hospital_name in sorted(hospitals.keys()):
        cursor.execute('INSERT INTO hospitals (name) VALUES (?)', (hospital_name,))
        hospitals[hospital_name] = cursor.lastrowid
    
    conn.commit()
    
    # Insert procedures
    print("Inserting procedures...")
    batch_size = 10000
    for i, proc in enumerate(procedures):
        hospital_id = hospitals[proc['hospital']]
        cursor.execute('''
            INSERT INTO procedures (hospital_id, procedure, cpt, price, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            hospital_id,
            proc['procedure'],
            proc.get('cpt', ''),
            proc.get('price', 0),
            proc.get('category', 'Other')
        ))
        
        if (i + 1) % batch_size == 0:
            conn.commit()
            print(f"  Inserted {i + 1}/{len(procedures)}")
    
    conn.commit()
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM procedures')
    proc_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM hospitals')
    hosp_count = cursor.fetchone()[0]
    
    print(f"\nDatabase rebuild complete!")
    print(f"  Hospitals: {hosp_count}")
    print(f"  Procedures: {proc_count}")
    
    # Show hospital list
    cursor.execute('SELECT name FROM hospitals ORDER BY name')
    print("\nHospitals in database:")
    for (name,) in cursor.fetchall():
        cursor.execute('SELECT COUNT(*) FROM procedures WHERE hospital_id = (SELECT id FROM hospitals WHERE name = ?)', (name,))
        count = cursor.fetchone()[0]
        print(f"  {name}: {count} procedures")
    
    conn.close()

if __name__ == '__main__':
    rebuild_database()
    print("\n[Done]")
