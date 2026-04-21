#!/usr/bin/env python3
"""
Hospital Pricing Database Builder - Final Robust Version
Resumes from last checkpoint if interrupted
"""

import sqlite3
import json
import csv
import requests
import zipfile
import io
import logging
from pathlib import Path
from datetime import datetime
import time
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db"
CHECKPOINT_FILE = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\build_checkpoint.txt"

HOSPITALS = {
    # OhioHealth (16)
    "Berger Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/384105653_berger-hospital_standardcharges.json", "format": "json"},
    "Doctors Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_doctors-hospital_standardcharges.json", "format": "json"},
    "Dublin Methodist Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_dublin-methodist-hospital_standardcharges.json", "format": "json"},
    "Grady Memorial Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314379436_grady-memorial-hospital_standardcharges.json", "format": "json"},
    "Grant Medical Center": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grant-medical-center_standardcharges.json", "format": "json"},
    "Grove City Methodist": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grove-city-methodist_standardcharges.json", "format": "json"},
    "Hardin Memorial Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314440479_hardin-memorial-hospital_standardcharges.json", "format": "json"},
    "Mansfield Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/310714456_ohiohealth-mansfield-hospital_standardcharges.json", "format": "json"},
    "Marion General Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/311070887_marion-general-hospital_standardcharges.json", "format": "json"},
    "Morrow County Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/316402699_morrow-county-hospital-_standardcharges.csv", "format": "csv"},
    "O'Bleness Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314446959_ohiohealth-o-_bleness-hospital_standardcharges.json", "format": "json"},
    "Pickerington Methodist Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_pickerington-methodist-hospital_standardcharges.json", "format": "json"},
    "Riverside Methodist Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_riverside-methodist-hospital_standardcharges.json", "format": "json"},
    "Shelby Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/340714456_ohiohealth-shelby-hospital_standardcharges.json", "format": "json"},
    "Southeastern Medical Center": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314391798_southeastern-ohio-regional-medical-center_standardcharges.json", "format": "json"},
    "Van Wert Hospital": {"system": "OhioHealth", "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/344429514_van-wert-county-hospital_standardcharges.json", "format": "json"},
    
    # Ohio State University (2)
    "Ohio State University Medical Center": {"system": "Ohio State University", "url": "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip", "format": "csv_zip", "encoding": "latin-1"},
    "James Cancer Hospital": {"system": "Ohio State University", "url": "https://wexnermedical.osu.edu/files/31-1322863_JAMES-CANCER-HOSPITAL_standardcharges.csv.zip", "format": "csv_zip", "encoding": "latin-1"},
    
    # Mount Carmel (5)
    "Mount Carmel East": {"system": "Mount Carmel", "url": "https://hpt.trinity-health.org/311439334-1982784535_mount-carmel-east_standardcharges.zip", "format": "csv_zip"},
    "Mount Carmel Grove City": {"system": "Mount Carmel", "url": "https://hpt.trinity-health.org/311439334-1710067376_mount-carmel-grove-city_standardcharges.zip", "format": "csv_zip"},
    "Mount Carmel New Albany": {"system": "Mount Carmel", "url": "https://hpt.trinity-health.org/311439334-1770668568_mount-carmel-new-albany_standardcharges.zip", "format": "csv_zip"},
    "Mount Carmel St. Ann's": {"system": "Mount Carmel", "url": "https://hpt.trinity-health.org/311439334-1417037045_mount-carmel-st-anns_standardcharges.zip", "format": "csv_zip"},
    "Mount Carmel Dublin": {"system": "Mount Carmel", "url": "https://hpt.trinity-health.org/311439334-1710752183_Mount-Carmel-Dublin_standardcharges.zip", "format": "csv_zip"},
}


class HospitalDatabaseBuilder:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.processed = self.load_checkpoint()
    
    def load_checkpoint(self):
        """Load list of already processed hospitals"""
        if Path(CHECKPOINT_FILE).exists():
            with open(CHECKPOINT_FILE) as f:
                return set(line.strip() for line in f if line.strip())
        return set()
    
    def save_checkpoint(self, hospital_name):
        """Mark hospital as processed"""
        self.processed.add(hospital_name)
        with open(CHECKPOINT_FILE, 'a') as f:
            f.write(hospital_name + '\n')
    
    def init_db(self):
        """Create database if it doesn't exist"""
        logger.info("Initializing database...")
        
        if not Path(self.db_path).exists():
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create tables
            self.cursor.execute("""
                CREATE TABLE hospitals (
                    hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    system TEXT NOT NULL,
                    data_format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE procedures (
                    procedure_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hospital_id INTEGER NOT NULL,
                    procedure_code TEXT,
                    procedure_name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hospital_id) REFERENCES hospitals (hospital_id),
                    UNIQUE(hospital_id, procedure_code, procedure_name)
                )
            """)
            
            self.cursor.execute("CREATE INDEX idx_procedure_name ON procedures(procedure_name)")
            self.cursor.execute("CREATE INDEX idx_procedure_code ON procedures(procedure_code)")
            self.cursor.execute("CREATE INDEX idx_hospital_id ON procedures(hospital_id)")
            
            self.cursor.execute("""
                CREATE TABLE pricing (
                    pricing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    procedure_id INTEGER NOT NULL,
                    payer_name TEXT,
                    negotiated_rate REAL,
                    gross_charge REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (procedure_id) REFERENCES procedures (procedure_id)
                )
            """)
            
            self.cursor.execute("CREATE INDEX idx_procedure_pricing ON pricing(procedure_id)")
            
            self.conn.commit()
            logger.info("✓ Database created")
        else:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info("✓ Database opened (resuming)")
    
    def add_hospital(self, name, system, data_format):
        """Add hospital"""
        try:
            self.cursor.execute("INSERT INTO hospitals (name, system, data_format) VALUES (?, ?, ?)", (name, system, data_format))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            self.cursor.execute("SELECT hospital_id FROM hospitals WHERE name = ?", (name,))
            return self.cursor.fetchone()[0]
    
    def fetch_hospital_data(self, hospital_name, hospital_info):
        """Fetch hospital data"""
        try:
            url = hospital_info['url']
            data_format = hospital_info['format']
            encoding = hospital_info.get('encoding', 'utf-8')
            
            logger.info(f"Fetching {hospital_name}...")
            
            response = requests.get(url, timeout=120, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            if data_format == "json":
                return self.parse_json(response.content, hospital_name, encoding)
            elif data_format == "csv":
                return self.parse_csv(response.content, hospital_name, encoding)
            elif data_format == "csv_zip":
                return self.parse_csv_zip(response.content, hospital_name, encoding)
            
        except Exception as e:
            logger.error(f"  ✗ Fetch error: {e}")
            return []
    
    def parse_json(self, content, hospital_name, encoding='utf-8'):
        """Parse JSON"""
        try:
            data = json.loads(content.decode('utf-8-sig'))
            procedures = []
            
            sci = data.get('standard_charge_information', [])
            if isinstance(sci, list):
                for item in sci:
                    if not isinstance(item, dict):
                        continue
                    
                    proc_name = item.get('description', '')
                    code_info = item.get('code_information', [])
                    codes = []
                    
                    if isinstance(code_info, list):
                        for code_item in code_info:
                            if isinstance(code_item, dict):
                                code = code_item.get('code', '')
                                if code:
                                    codes.append(code)
                    
                    proc_code = codes[0] if codes else ''
                    
                    std_charges = item.get('standard_charges', [])
                    if isinstance(std_charges, list):
                        for charge in std_charges:
                            if isinstance(charge, dict):
                                payers = charge.get('payers', [])
                                if isinstance(payers, list) and len(payers) > 0:
                                    payer = payers[0]
                                    payer_name = payer.get('payer_name', 'Standard')
                                    rates = payer.get('negotiated_rates', [])
                                    
                                    if isinstance(rates, list) and len(rates) > 0:
                                        rate_rec = rates[0]
                                        negotiated_rate = rate_rec.get('negotiated_rate')
                                    else:
                                        negotiated_rate = None
                                    
                                    gross = charge.get('gross_charge')
                                    
                                    proc_record = {
                                        'name': proc_name,
                                        'code': proc_code,
                                        'payer': payer_name,
                                        'negotiated_rate': negotiated_rate,
                                        'gross_charge': gross
                                    }
                                    procedures.append(proc_record)
            
            logger.info(f"  ✓ Parsed {len(procedures)} records")
            return procedures
        
        except Exception as e:
            logger.error(f"  ✗ JSON error: {e}")
            traceback.print_exc()
            return []
    
    def parse_csv(self, content, hospital_name, encoding='utf-8'):
        """Parse CSV"""
        try:
            text = content.decode(encoding, errors='ignore')
            reader = csv.DictReader(io.StringIO(text))
            procedures = list(reader)
            logger.info(f"  ✓ Parsed {len(procedures)} records")
            return procedures
        except Exception as e:
            logger.error(f"  ✗ CSV error: {e}")
            return []
    
    def parse_csv_zip(self, content, hospital_name, encoding='utf-8'):
        """Parse ZIP with CSV"""
        try:
            procedures = []
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for fname in zf.namelist():
                    if fname.endswith('.csv'):
                        with zf.open(fname) as f:
                            text = f.read().decode(encoding, errors='ignore')
                            reader = csv.DictReader(io.StringIO(text))
                            procedures.extend(list(reader))
            
            logger.info(f"  ✓ Parsed {len(procedures)} records from ZIP")
            return procedures
        except Exception as e:
            logger.error(f"  ✗ ZIP error: {e}")
            traceback.print_exc()
            return []
    
    def insert_procedures(self, hospital_id, procedures):
        """Insert procedures in batches"""
        if not procedures:
            return 0, 0
        
        count = 0
        pricing_count = 0
        
        for i, proc in enumerate(procedures):
            try:
                proc_code = (proc.get('code') or proc.get('procedure_code') or '')[:50]
                proc_name = (proc.get('name') or proc.get('procedure_name') or '')[:500]
                proc_desc = (proc.get('description') or '')[:1000]
                
                if not proc_name:
                    continue
                
                try:
                    self.cursor.execute(
                        "INSERT INTO procedures (hospital_id, procedure_code, procedure_name, description) VALUES (?, ?, ?, ?)",
                        (hospital_id, proc_code if proc_code else None, proc_name, proc_desc)
                    )
                    procedure_id = self.cursor.lastrowid
                except sqlite3.IntegrityError:
                    self.cursor.execute(
                        "SELECT procedure_id FROM procedures WHERE hospital_id = ? AND procedure_name = ?",
                        (hospital_id, proc_name)
                    )
                    result = self.cursor.fetchone()
                    if not result:
                        continue
                    procedure_id = result[0]
                
                count += 1
                
                # Pricing
                negotiated_rate = None
                gross_charge = None
                payer_name = 'Standard'
                
                for key in ['negotiated_rate', 'negotiated', 'insurance_price']:
                    val = proc.get(key)
                    if val:
                        try:
                            negotiated_rate = float(val)
                            break
                        except:
                            pass
                
                for key in ['gross_charge', 'gross', 'standard_price']:
                    val = proc.get(key)
                    if val:
                        try:
                            gross_charge = float(val)
                            break
                        except:
                            pass
                
                pn = proc.get('payer') or proc.get('payer_name')
                if pn:
                    payer_name = str(pn)[:100]
                
                if negotiated_rate or gross_charge:
                    try:
                        self.cursor.execute(
                            "INSERT INTO pricing (procedure_id, payer_name, negotiated_rate, gross_charge) VALUES (?, ?, ?, ?)",
                            (procedure_id, payer_name, negotiated_rate, gross_charge)
                        )
                        pricing_count += 1
                    except:
                        pass
                
                # Batch commit every 1000
                if count % 1000 == 0:
                    self.conn.commit()
            
            except Exception as e:
                pass
        
        self.conn.commit()
        return count, pricing_count
    
    def build_database(self):
        """Main build"""
        logger.info("\n" + "="*80)
        logger.info("HOSPITAL DATABASE BUILDER - FINAL")
        logger.info("="*80 + "\n")
        
        self.init_db()
        
        start_time = time.time()
        total_procs = 0
        total_pricing = 0
        
        for hospital_name, hospital_info in HOSPITALS.items():
            if hospital_name in self.processed:
                logger.info(f"⊘ Skipping {hospital_name} (already processed)")
                continue
            
            logger.info(f"\n[{len(self.processed)+1}/23] Processing {hospital_name}...")
            
            try:
                hospital_id = self.add_hospital(hospital_name, hospital_info['system'], hospital_info['format'])
                procedures = self.fetch_hospital_data(hospital_name, hospital_info)
                
                if procedures:
                    count, pricing = self.insert_procedures(hospital_id, procedures)
                    logger.info(f"  ✓ Inserted {count} procs, {pricing} pricing")
                    total_procs += count
                    total_pricing += pricing
                    self.save_checkpoint(hospital_name)
                else:
                    logger.warning(f"  ✗ No procedures")
                    self.save_checkpoint(hospital_name)
                
                time.sleep(2)
            
            except Exception as e:
                logger.error(f"  ✗ FAILED: {e}")
                traceback.print_exc()
                continue
        
        elapsed = time.time() - start_time
        
        # Stats
        self.cursor.execute("SELECT COUNT(*) FROM hospitals")
        h_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM procedures")
        p_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM pricing")
        pr_count = self.cursor.fetchone()[0]
        
        logger.info("\n" + "="*80)
        logger.info("COMPLETE")
        logger.info("="*80)
        logger.info(f"Time: {elapsed:.0f}s")
        logger.info(f"Hospitals: {h_count}")
        logger.info(f"Procedures: {p_count:,}")
        logger.info(f"Pricing: {pr_count:,}")
        db_mb = Path(self.db_path).stat().st_size / (1024*1024)
        logger.info(f"DB Size: {db_mb:.1f} MB")
        logger.info("="*80 + "\n")
        
        self.conn.close()
        
        # Documentation
        self.generate_docs(h_count, p_count, pr_count)
    
    def generate_docs(self, h, p, pr):
        """Generate documentation"""
        doc_path = Path(self.db_path).parent / "HOSPITAL_DB_SCHEMA.md"
        
        content = f"""# Hospital Pricing Database

**Generated:** {datetime.now().isoformat()}

## Overview
- **Hospitals:** {h}
- **Procedures:** {p:,}
- **Pricing Records:** {pr:,}
- **Size:** {Path(self.db_path).stat().st_size / (1024*1024):.1f} MB
- **Path:** `{self.db_path}`

## Systems
- OhioHealth: 16 hospitals
- Ohio State University: 2 hospitals
- Mount Carmel: 5 hospitals

## Schema

### hospitals
- hospital_id (PK)
- name (TEXT, UNIQUE)
- system (TEXT)
- data_format (TEXT)

### procedures
- procedure_id (PK)
- hospital_id (FK)
- procedure_code (TEXT)
- procedure_name (TEXT, INDEXED)
- description (TEXT)

**Indexes:**
- idx_procedure_name
- idx_procedure_code
- idx_hospital_id

### pricing
- pricing_id (PK)
- procedure_id (FK, INDEXED)
- payer_name (TEXT)
- negotiated_rate (REAL)
- gross_charge (REAL)

## Example Queries

```sql
-- Search by procedure
SELECT p.procedure_name, h.name, pr.negotiated_rate
FROM procedures p
JOIN hospitals h ON p.hospital_id = h.hospital_id
LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
WHERE p.procedure_name LIKE '%CT%'
LIMIT 100;

-- Compare prices
SELECT h.name, AVG(pr.negotiated_rate) as avg_price
FROM procedures p
JOIN hospitals h ON p.hospital_id = h.hospital_id
JOIN pricing pr ON p.procedure_id = pr.procedure_id
WHERE p.procedure_name = 'Hospital Visit'
GROUP BY h.hospital_id;

-- Get all hospitals
SELECT * FROM hospitals WHERE system = 'OhioHealth';
```

## Ready for Flask API
Database is optimized for fast lookups via indexed procedure names and codes.
"""
        
        Path(doc_path).write_text(content)
        logger.info(f"✓ Documentation: {doc_path}")


if __name__ == "__main__":
    builder = HospitalDatabaseBuilder(DB_PATH)
    builder.build_database()
