#!/usr/bin/env python
"""
Initialize SQLite database for Hospital Pricing Application.
This script creates tables and populates them with hospital procedure pricing data.
Designed to run on startup (Render Procfile) and locally for development.
"""

import sqlite3
import json
import os
import sys
from pathlib import Path

DB_PATH = 'hospital_pricing.db'
JSON_DATA_PATH = 'procedures.json'

def create_tables(conn):
    """Create database schema"""
    cursor = conn.cursor()
    
    # Hospitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Procedures table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS procedures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cpt TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, cpt)
        )
    ''')
    
    # Pricing table (junction between hospitals and procedures)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            procedure_id INTEGER NOT NULL,
            price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
            FOREIGN KEY (procedure_id) REFERENCES procedures(id),
            UNIQUE(hospital_id, procedure_id)
        )
    ''')
    
    conn.commit()
    print("[OK] Tables created successfully")

def load_data(conn):
    """Load procedure data from JSON"""
    if not os.path.exists(JSON_DATA_PATH):
        print(f"[WARN] Warning: {JSON_DATA_PATH} not found. Database will be empty.")
        return 0
    
    try:
        with open(JSON_DATA_PATH, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERR] Error reading JSON: {e}")
        return 0
    
    if not isinstance(data, list):
        print("[ERR] JSON data must be a list of records")
        return 0
    
    cursor = conn.cursor()
    inserted_count = 0
    skipped_count = 0
    
    # Get unique hospitals and procedures first
    hospitals_set = set()
    procedures_dict = {}
    
    for record in data:
        hospitals_set.add(record.get('hospital'))
        proc_key = (record.get('procedure'), record.get('cpt'))
        if proc_key not in procedures_dict:
            procedures_dict[proc_key] = record.get('category')
    
    # Insert hospitals
    hospital_map = {}
    for hospital_name in sorted(hospitals_set):
        if hospital_name:
            try:
                cursor.execute(
                    'INSERT INTO hospitals (name) VALUES (?) ON CONFLICT(name) DO NOTHING',
                    (hospital_name,)
                )
                cursor.execute('SELECT id FROM hospitals WHERE name = ?', (hospital_name,))
                result = cursor.fetchone()
                if result:
                    hospital_map[hospital_name] = result[0]
            except sqlite3.Error as e:
                print(f"Error inserting hospital {hospital_name}: {e}")
    
    conn.commit()
    print(f"[OK] Inserted {len(hospital_map)} hospitals")
    
    # Insert procedures
    procedure_map = {}
    for (proc_name, cpt), category in procedures_dict.items():
        if proc_name and cpt:
            try:
                cursor.execute(
                    'INSERT INTO procedures (name, cpt, category) VALUES (?, ?, ?) ON CONFLICT(name, cpt) DO NOTHING',
                    (proc_name, cpt, category)
                )
                cursor.execute(
                    'SELECT id FROM procedures WHERE name = ? AND cpt = ?',
                    (proc_name, cpt)
                )
                result = cursor.fetchone()
                if result:
                    procedure_map[(proc_name, cpt)] = result[0]
            except sqlite3.Error as e:
                print(f"Error inserting procedure {proc_name}: {e}")
    
    conn.commit()
    print(f"[OK] Inserted {len(procedure_map)} procedures")
    
    # Insert pricing records with deduplication
    # Track what we've inserted to avoid duplicate inserts
    pricing_inserted = set()
    
    for record in data:
        hospital_name = record.get('hospital')
        proc_name = record.get('procedure')
        cpt = record.get('cpt')
        price = record.get('price')
        
        # Skip if missing required fields (but allow price=0 or price=None)
        if not all([hospital_name, proc_name, cpt]):
            skipped_count += 1
            continue
        
        # Use 0 if price is None
        if price is None:
            price = 0
        
        hospital_id = hospital_map.get(hospital_name)
        procedure_id = procedure_map.get((proc_name, cpt))
        
        if hospital_id and procedure_id:
            pricing_key = (hospital_id, procedure_id)
            if pricing_key not in pricing_inserted:
                try:
                    cursor.execute(
                        'INSERT INTO pricing (hospital_id, procedure_id, price) VALUES (?, ?, ?)',
                        (hospital_id, procedure_id, price)
                    )
                    inserted_count += 1
                    pricing_inserted.add(pricing_key)
                except sqlite3.IntegrityError:
                    # Skip if already exists (from previous run or duplicates in JSON)
                    skipped_count += 1
                except sqlite3.Error as e:
                    print(f"Error inserting pricing for {hospital_name}/{proc_name}: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
    
    conn.commit()
    print(f"[OK] Inserted {inserted_count} pricing records")
    if skipped_count > 0:
        print(f"[INFO] Skipped {skipped_count} duplicate/invalid records")
    
    return inserted_count

def create_indices(conn):
    """Create indices for fast queries"""
    cursor = conn.cursor()
    
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hospitals_name ON hospitals(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedures_cpt ON procedures(cpt)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedures_category ON procedures(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pricing_hospital ON pricing(hospital_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pricing_procedure ON pricing(procedure_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pricing_price ON pricing(price)')
        conn.commit()
        print("[OK] Indices created successfully")
    except sqlite3.Error as e:
        print(f"[WARN] Error creating indices: {e}")

def get_database_stats(conn):
    """Get and display database statistics"""
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM hospitals')
    hospital_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view' AND name='procedures'")
    has_view = cursor.fetchone()[0] > 0
    if has_view:
        cursor.execute('SELECT COUNT(*) FROM procedures_table')
    else:
        cursor.execute('SELECT COUNT(*) FROM procedures')
    procedure_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM pricing')
    pricing_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(price) FROM pricing')
    avg_price = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(price), MAX(price) FROM pricing')
    min_price, max_price = cursor.fetchone()
    
    print("\n" + "="*50)
    print("Database Statistics:")
    print("="*50)
    print(f"Hospitals:  {hospital_count:,}")
    print(f"Procedures: {procedure_count:,}")
    print(f"Pricing Records: {pricing_count:,}")
    if avg_price:
        print(f"Average Price:   ${avg_price:,.2f}")
    if min_price and max_price:
        print(f"Price Range:     ${min_price:,.2f} - ${max_price:,.2f}")
    print("="*50 + "\n")

def create_flattened_view(conn):
    """
    Create a flattened VIEW 'procedures' for app.py compatibility.
    App.py expects: id, hospital, procedure_name, cpt_code, category, price, updated_date
    The view joins: hospitals + procedures_table + pricing to produce that schema.
    """
    cursor = conn.cursor()

    # Drop old view if exists
    try:
        cursor.execute("DROP VIEW IF EXISTS procedures")
    except sqlite3.OperationalError:
        pass

    # Rename the procedures TABLE to procedures_table (if not already renamed)
    try:
        cursor.execute("ALTER TABLE procedures RENAME TO procedures_table")
        print("[OK] Renamed procedures table -> procedures_table")
    except sqlite3.OperationalError:
        # Already renamed or view exists - that's fine
        pass

    # Create flattened VIEW named 'procedures' (app.py queries this name)
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS procedures AS
        SELECT
            pr.id,
            pr.hospital_id,
            h.name AS hospital,
            p.name AS procedure_name,
            p.cpt AS cpt_code,
            p.category,
            pr.price,
            pr.created_at AS updated_date
        FROM pricing pr
        JOIN hospitals h ON pr.hospital_id = h.id
        JOIN procedures_table p ON pr.procedure_id = p.id
    ''')

    conn.commit()

    # Verify the view works
    cursor.execute("SELECT COUNT(*) FROM procedures")
    count = cursor.fetchone()[0]
    print(f"[OK] Flattened VIEW 'procedures' created with {count} records")

def init_database():
    """Initialize the database"""
    print(f"Initializing Hospital Pricing Database...")
    print(f"Database path: {DB_PATH}")
    
    # Check if database already exists
    db_exists = os.path.exists(DB_PATH)
    if db_exists:
        print(f"Database already exists. Checking status...")
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pricing'")
            if cursor.fetchone():
                # Ensure the flattened VIEW exists (may be missing from prior builds)
                create_flattened_view(conn)
                get_database_stats(conn)
                conn.close()
                return True
            else:
                print("Database incomplete. Rebuilding...")
                conn.close()
                os.remove(DB_PATH)
        except Exception as e:
            print(f"[ERR] Error checking existing database: {e}")
            return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        create_tables(conn)
        load_data(conn)
        create_indices(conn)
        create_flattened_view(conn)
        get_database_stats(conn)
        conn.close()
        print("[OK] Database initialization complete!")
        return True
    except Exception as e:
        print(f"[ERR] Error initializing database: {e}")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
