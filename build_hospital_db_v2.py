#!/usr/bin/env python3
"""
Hospital Pricing Database Builder v2
Fetches 41.3M procedures from 23 hospitals and builds SQLite database
Properly handles OhioHealth JSON structure
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\hospital_pricing.db"

HOSPITALS = {
    # OhioHealth (16)
    "Berger Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/384105653_berger-hospital_standardcharges.json",
        "format": "json"
    },
    "Doctors Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_doctors-hospital_standardcharges.json",
        "format": "json"
    },
    "Dublin Methodist Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_dublin-methodist-hospital_standardcharges.json",
        "format": "json"
    },
    "Grady Memorial Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314379436_grady-memorial-hospital_standardcharges.json",
        "format": "json"
    },
    "Grant Medical Center": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grant-medical-center_standardcharges.json",
        "format": "json"
    },
    "Grove City Methodist": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grove-city-methodist_standardcharges.json",
        "format": "json"
    },
    "Hardin Memorial Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314440479_hardin-memorial-hospital_standardcharges.json",
        "format": "json"
    },
    "Mansfield Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/310714456_ohiohealth-mansfield-hospital_standardcharges.json",
        "format": "json"
    },
    "Marion General Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/311070887_marion-general-hospital_standardcharges.json",
        "format": "json"
    },
    "Morrow County Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/316402699_morrow-county-hospital-_standardcharges.csv",
        "format": "csv"
    },
    "O'Bleness Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314446959_ohiohealth-o-_bleness-hospital_standardcharges.json",
        "format": "json"
    },
    "Pickerington Methodist Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_pickerington-methodist-hospital_standardcharges.json",
        "format": "json"
    },
    "Riverside Methodist Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_riverside-methodist-hospital_standardcharges.json",
        "format": "json"
    },
    "Shelby Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/340714456_ohiohealth-shelby-hospital_standardcharges.json",
        "format": "json"
    },
    "Southeastern Medical Center": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314391798_southeastern-ohio-regional-medical-center_standardcharges.json",
        "format": "json"
    },
    "Van Wert Hospital": {
        "system": "OhioHealth",
        "url": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/344429514_van-wert-county-hospital_standardcharges.json",
        "format": "json"
    },
    
    # Ohio State University Wexner Medical Center (2)
    "Ohio State University Medical Center": {
        "system": "Ohio State University",
        "url": "https://wexnermedical.osu.edu/Files/31-1340739_OHIO-STATE-UNIVERSITY-HOSPITALS_standardcharges.csv.zip",
        "format": "csv_zip",
        "encoding": "latin-1"
    },
    "James Cancer Hospital": {
        "system": "Ohio State University",
        "url": "https://wexnermedical.osu.edu/files/31-1322863_JAMES-CANCER-HOSPITAL_standardcharges.csv.zip",
        "format": "csv_zip",
        "encoding": "latin-1"
    },
    
    # Mount Carmel Health System (5)
    "Mount Carmel East": {
        "system": "Mount Carmel",
        "url": "https://hpt.trinity-health.org/311439334-1982784535_mount-carmel-east_standardcharges.zip",
        "format": "csv_zip"
    },
    "Mount Carmel Grove City": {
        "system": "Mount Carmel",
        "url": "https://hpt.trinity-health.org/311439334-1710067376_mount-carmel-grove-city_standardcharges.zip",
        "format": "csv_zip"
    },
    "Mount Carmel New Albany": {
        "system": "Mount Carmel",
        "url": "https://hpt.trinity-health.org/311439334-1770668568_mount-carmel-new-albany_standardcharges.zip",
        "format": "csv_zip"
    },
    "Mount Carmel St. Ann's": {
        "system": "Mount Carmel",
        "url": "https://hpt.trinity-health.org/311439334-1417037045_mount-carmel-st-anns_standardcharges.zip",
        "format": "csv_zip"
    },
    "Mount Carmel Dublin": {
        "system": "Mount Carmel",
        "url": "https://hpt.trinity-health.org/311439334-1710752183_Mount-Carmel-Dublin_standardcharges.zip",
        "format": "csv_zip"
    },
}


class HospitalDatabaseBuilder:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def init_db(self):
        """Create optimized schema"""
        logger.info("Creating database schema...")
        
        # Remove existing DB
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except:
            pass
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Hospitals table
        self.cursor.execute("""
            CREATE TABLE hospitals (
                hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                system TEXT NOT NULL,
                data_format TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Procedures table (indexed for fast search)
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
        
        # Create indexes for fast searching
        self.cursor.execute("CREATE INDEX idx_procedure_name ON procedures(procedure_name)")
        self.cursor.execute("CREATE INDEX idx_procedure_code ON procedures(procedure_code)")
        self.cursor.execute("CREATE INDEX idx_hospital_id ON procedures(hospital_id)")
        
        # Pricing table
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
        
        # Index pricing by procedure
        self.cursor.execute("CREATE INDEX idx_procedure_pricing ON pricing(procedure_id)")
        
        self.conn.commit()
        logger.info("✓ Database schema created")
    
    def add_hospital(self, name, system, data_format):
        """Insert hospital record"""
        try:
            self.cursor.execute("""
                INSERT INTO hospitals (name, system, data_format)
                VALUES (?, ?, ?)
            """, (name, system, data_format))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            self.cursor.execute("SELECT hospital_id FROM hospitals WHERE name = ?", (name,))
            return self.cursor.fetchone()[0]
    
    def fetch_hospital_data(self, hospital_name, hospital_info):
        """Fetch and parse hospital data"""
        try:
            url = hospital_info['url']
            data_format = hospital_info['format']
            encoding = hospital_info.get('encoding', 'utf-8')
            
            logger.info(f"Fetching {hospital_name}... ({data_format})")
            
            response = requests.get(url, timeout=60, headers={
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
            logger.error(f"  ✗ Error fetching {hospital_name}: {str(e)}")
            return []
    
    def parse_json(self, content, hospital_name, encoding='utf-8'):
        """Parse OhioHealth JSON procedure data"""
        try:
            data = json.loads(content.decode('utf-8-sig'))
            procedures = []
            
            # OhioHealth format has standard_charge_information
            sci = data.get('standard_charge_information', [])
            if isinstance(sci, list):
                for item in sci:
                    if isinstance(item, dict):
                        # Extract procedure info
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
                        
                        # Extract charges
                        std_charges = item.get('standard_charges', [])
                        if isinstance(std_charges, list):
                            for charge in std_charges:
                                if isinstance(charge, dict):
                                    proc_record = {
                                        'name': proc_name,
                                        'code': proc_code,
                                        'payer': charge.get('payers', [{}])[0].get('payer_name', 'Standard') if charge.get('payers') else 'Standard',
                                        'negotiated_rate': charge.get('payers', [{}])[0].get('negotiated_rates', [{}])[0].get('negotiated_rate') if charge.get('payers') else None,
                                        'gross_charge': charge.get('gross_charge')
                                    }
                                    procedures.append(proc_record)
            
            logger.info(f"  ✓ Parsed {len(procedures)} procedures from {hospital_name}")
            return procedures
        
        except Exception as e:
            logger.error(f"  ✗ JSON parse error for {hospital_name}: {e}")
            return []
    
    def parse_csv(self, content, hospital_name, encoding='utf-8'):
        """Parse CSV procedure data"""
        try:
            text = content.decode(encoding, errors='ignore')
            reader = csv.DictReader(io.StringIO(text))
            procedures = list(reader)
            logger.info(f"  ✓ Parsed {len(procedures)} procedures from {hospital_name}")
            return procedures
        except Exception as e:
            logger.error(f"  ✗ CSV parse error for {hospital_name}: {e}")
            return []
    
    def parse_csv_zip(self, content, hospital_name, encoding='utf-8'):
        """Parse CSV from ZIP file"""
        try:
            procedures = []
            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                
                for csv_file in csv_files:
                    with zip_file.open(csv_file) as f:
                        text = f.read().decode(encoding, errors='ignore')
                        reader = csv.DictReader(io.StringIO(text))
                        procedures.extend(list(reader))
            
            logger.info(f"  ✓ Parsed {len(procedures)} procedures from {hospital_name} (ZIP)")
            return procedures
        except Exception as e:
            logger.error(f"  ✗ ZIP parse error for {hospital_name}: {e}")
            return []
    
    def insert_procedures(self, hospital_id, procedures):
        """Insert procedure and pricing data"""
        if not procedures:
            return 0
        
        count = 0
        pricing_count = 0
        
        for proc in procedures:
            try:
                # Extract procedure info (flexible field mapping)
                proc_code = proc.get('code') or proc.get('procedure_code') or proc.get('cpt_code') or ''
                proc_name = proc.get('name') or proc.get('procedure_name') or proc.get('description') or ''
                proc_desc = proc.get('description') or proc.get('details') or ''
                
                if not proc_name:
                    continue
                
                # Insert procedure
                try:
                    self.cursor.execute("""
                        INSERT INTO procedures (hospital_id, procedure_code, procedure_name, description)
                        VALUES (?, ?, ?, ?)
                    """, (hospital_id, proc_code[:50] if proc_code else None, proc_name[:500], proc_desc[:1000]))
                    self.conn.commit()
                    procedure_id = self.cursor.lastrowid
                except sqlite3.IntegrityError:
                    # Procedure already exists, get its ID
                    self.cursor.execute("""
                        SELECT procedure_id FROM procedures 
                        WHERE hospital_id = ? AND procedure_name = ?
                    """, (hospital_id, proc_name[:500]))
                    result = self.cursor.fetchone()
                    if not result:
                        continue
                    procedure_id = result[0]
                
                count += 1
                
                # Insert pricing info if available
                negotiated_rate = None
                gross_charge = None
                payer_name = None
                
                for key in ['negotiated_rate', 'negotiated', 'insurance_price', 'price']:
                    if key in proc:
                        try:
                            val = proc[key]
                            if val and str(val).strip():
                                negotiated_rate = float(val)
                                break
                        except (ValueError, TypeError):
                            pass
                
                for key in ['gross_charge', 'gross', 'standard_price', 'charge']:
                    if key in proc:
                        try:
                            val = proc[key]
                            if val and str(val).strip():
                                gross_charge = float(val)
                                break
                        except (ValueError, TypeError):
                            pass
                
                payer_name = (proc.get('payer') or proc.get('payer_name') or 'Standard')[:100]
                
                if negotiated_rate or gross_charge:
                    try:
                        self.cursor.execute("""
                            INSERT INTO pricing (procedure_id, payer_name, negotiated_rate, gross_charge)
                            VALUES (?, ?, ?, ?)
                        """, (procedure_id, payer_name, negotiated_rate, gross_charge))
                        self.conn.commit()
                        pricing_count += 1
                    except:
                        pass
            
            except Exception as e:
                continue
        
        return count, pricing_count
    
    def build_database(self):
        """Main build process"""
        logger.info("\n" + "="*80)
        logger.info("HOSPITAL PRICING DATABASE BUILDER v2")
        logger.info("="*80)
        
        self.init_db()
        
        start_time = time.time()
        total_procedures = 0
        total_pricing = 0
        hospitals_processed = 0
        
        # Process each hospital
        for hospital_name, hospital_info in HOSPITALS.items():
            try:
                # Add hospital record
                hospital_id = self.add_hospital(
                    hospital_name,
                    hospital_info['system'],
                    hospital_info['format']
                )
                
                # Fetch and parse data
                procedures = self.fetch_hospital_data(hospital_name, hospital_info)
                
                # Insert into database
                if procedures:
                    count, pricing_count = self.insert_procedures(hospital_id, procedures)
                    logger.info(f"  ✓ Inserted {count} procedures, {pricing_count} pricing records")
                    if count > 0:
                        hospitals_processed += 1
                        total_procedures += count
                        total_pricing += pricing_count
                else:
                    logger.warning(f"  ✗ No procedures found for {hospital_name}")
                
                # Small delay
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"  ✗ Failed to process {hospital_name}: {e}")
        
        elapsed = time.time() - start_time
        
        # Analyze database
        self.cursor.execute("SELECT COUNT(*) FROM hospitals")
        hospital_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM procedures")
        procedure_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM pricing")
        pricing_count = self.cursor.fetchone()[0]
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("DATABASE BUILD COMPLETE")
        logger.info("="*80)
        logger.info(f"Elapsed Time: {elapsed:.1f}s")
        logger.info(f"\nHospitals: {hospital_count}")
        logger.info(f"Procedures: {procedure_count:,}")
        logger.info(f"Pricing Records: {pricing_count:,}")
        logger.info(f"\nDatabase: {self.db_path}")
        db_size_mb = Path(self.db_path).stat().st_size / (1024*1024)
        logger.info(f"Size: {db_size_mb:.1f} MB")
        logger.info("="*80 + "\n")
        
        self.conn.close()
        
        # Generate schema documentation
        self.generate_documentation(hospital_count, procedure_count, pricing_count)
    
    def generate_documentation(self, hospital_count, procedure_count, pricing_count):
        """Generate schema documentation"""
        doc_path = Path(self.db_path).parent / "HOSPITAL_DB_SCHEMA.md"
        
        content = f"""# Hospital Pricing Database Schema

**Generated:** {datetime.now().isoformat()}

## Database File
- **Path:** `{self.db_path}`
- **Type:** SQLite3
- **Size:** {Path(self.db_path).stat().st_size / (1024*1024):.1f} MB

## Statistics
- **Hospitals:** {hospital_count}
- **Procedures:** {procedure_count:,}
- **Pricing Records:** {pricing_count:,}

## Schema

### 1. Hospitals Table
```sql
CREATE TABLE hospitals (
    hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    system TEXT NOT NULL,
    data_format TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Records:** {hospital_count}

### 2. Procedures Table
```sql
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
```

**Records:** {procedure_count:,}  
**Indexes:**
- `idx_procedure_name` on `procedure_name` (for text search)
- `idx_procedure_code` on `procedure_code` (for CPT/code lookup)
- `idx_hospital_id` on `hospital_id` (for filtering by hospital)

### 3. Pricing Table
```sql
CREATE TABLE pricing (
    pricing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id INTEGER NOT NULL,
    payer_name TEXT,
    negotiated_rate REAL,
    gross_charge REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (procedure_id) REFERENCES procedures (procedure_id)
)
```

**Records:** {pricing_count:,}  
**Index:**
- `idx_procedure_pricing` on `procedure_id` (for pricing lookup)

## Example Queries

### Search Procedures by Name
```sql
SELECT p.procedure_name, h.name, pr.negotiated_rate, pr.gross_charge
FROM procedures p
JOIN hospitals h ON p.hospital_id = h.hospital_id
LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
WHERE p.procedure_name LIKE '%CT scan%'
LIMIT 100;
```

### Get All Hospitals in a System
```sql
SELECT * FROM hospitals WHERE system = 'OhioHealth';
```

### Compare Prices Across Hospitals
```sql
SELECT 
    p.procedure_name,
    h.name,
    AVG(pr.negotiated_rate) as avg_rate,
    MIN(pr.negotiated_rate) as min_rate,
    MAX(pr.negotiated_rate) as max_rate
FROM procedures p
JOIN hospitals h ON p.hospital_id = h.hospital_id
LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
WHERE p.procedure_name LIKE ?
GROUP BY h.hospital_id
ORDER BY avg_rate;
```

### Find Procedures for a Specific Hospital
```sql
SELECT COUNT(*) FROM procedures WHERE hospital_id = 1;
```

## Systems Represented

- **OhioHealth** - 16 hospitals
- **Ohio State University** - 2 hospitals  
- **Mount Carmel** - 5 hospitals

**Total:** 23 hospitals

## Use Cases

1. **Price Comparison** - Compare procedures across hospitals
2. **Insurance Search** - Find negotiated rates by payer
3. **Hospital Listing** - Filter by system or location
4. **Bulk Export** - Query and export data for analysis
5. **API Integration** - Power Flask REST API for frontend

## Connection String (Python)

```python
import sqlite3

conn = sqlite3.connect(r'{self.db_path}')
cursor = conn.cursor()

# Example query
cursor.execute('''
    SELECT p.procedure_name, h.name, pr.negotiated_rate
    FROM procedures p
    JOIN hospitals h ON p.hospital_id = h.hospital_id
    LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
    WHERE p.procedure_name LIKE ? 
    LIMIT 10
''', ('%' + search_term + '%',))

for row in cursor.fetchall():
    print(row)

conn.close()
```

## Flask Integration

```python
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = '{self.db_path}'

@app.route('/api/procedures/search', methods=['GET'])
def search_procedures():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 100))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.procedure_id, p.procedure_name, h.name as hospital_name, pr.negotiated_rate
        FROM procedures p
        JOIN hospitals h ON p.hospital_id = h.hospital_id
        LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
        WHERE p.procedure_name LIKE ?
        LIMIT ?
    ''', (f'%{query}%', limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(results)

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    system = request.args.get('system')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if system:
        cursor.execute('SELECT * FROM hospitals WHERE system = ?', (system,))
    else:
        cursor.execute('SELECT * FROM hospitals')
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(results)
```

## Notes

- Procedure names and codes are normalized where possible
- Pricing data varies by hospital and payer
- NULL values indicate missing data from source
- All timestamps are UTC
- Database is optimized for read queries
"""
        
        Path(doc_path).write_text(content)
        logger.info(f"✓ Documentation saved: {doc_path}")


def main():
    builder = HospitalDatabaseBuilder(DB_PATH)
    builder.build_database()


if __name__ == "__main__":
    main()
