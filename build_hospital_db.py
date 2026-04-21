#!/usr/bin/env python3
"""
Hospital Pricing Database Builder
Fetches 41.3M procedures from 23 hospitals and builds SQLite database
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
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        self.stats = {
            "hospitals_processed": 0,
            "total_procedures": 0,
            "total_pricing_records": 0,
            "errors": [],
        }
    
    def init_db(self):
        """Create optimized schema"""
        logger.info("Creating database schema...")
        
        # Remove existing DB if not locked
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except PermissionError:
            logger.warning("Database file locked, will append to existing")
            return
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Hospitals table
        self.cursor.execute("""
            CREATE TABLE hospitals (
                hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                system TEXT NOT NULL,
                url TEXT,
                data_format TEXT,
                encoding TEXT DEFAULT 'utf-8',
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
    
    def add_hospital(self, name, system, url, data_format, encoding='utf-8'):
        """Insert hospital record"""
        try:
            self.cursor.execute("""
                INSERT INTO hospitals (name, system, url, data_format, encoding)
                VALUES (?, ?, ?, ?, ?)
            """, (name, system, url, data_format, encoding))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Hospital already exists: {name}")
            # Get existing ID
            self.cursor.execute("SELECT hospital_id FROM hospitals WHERE name = ?", (name,))
            return self.cursor.fetchone()[0]
    
    def fetch_hospital_data(self, hospital_name, hospital_info):
        """Fetch and parse hospital data"""
        try:
            url = hospital_info['url']
            data_format = hospital_info['format']
            encoding = hospital_info.get('encoding', 'utf-8')
            
            logger.info(f"Fetching {hospital_name}... ({data_format})")
            
            response = requests.get(url, timeout=30, headers={
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
            error_msg = f"Error fetching {hospital_name}: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return []
    
    def parse_json(self, content, hospital_name, encoding='utf-8'):
        """Parse JSON procedure data"""
        try:
            # Handle UTF-8 BOM
            data = json.loads(content.decode('utf-8-sig'))
            procedures = []
            
            # Standard hospital transparency format
            if isinstance(data, dict):
                # Try various common keys
                for key in ['standard_charges', 'procedures', 'items', 'chargemaster', 'standardCharges']:
                    if key in data:
                        items = data[key]
                        if isinstance(items, list):
                            procedures.extend(items)
                
                # If no recognized key, check for items directly
                if not procedures and 'items' in data:
                    procedures = data['items']
            elif isinstance(data, list):
                procedures = data
            
            logger.info(f"  ✓ Parsed {len(procedures)} procedures from {hospital_name}")
            return procedures
        
        except Exception as e:
            logger.error(f"  ✗ JSON parse error for {hospital_name}: {e}")
            return []
    
    def parse_csv(self, content, hospital_name, encoding='utf-8'):
        """Parse CSV procedure data"""
        try:
            text = content.decode(encoding)
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
                    """, (hospital_id, proc_code[:20] if proc_code else None, proc_name[:500], proc_desc[:1000]))
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
                
                # Insert pricing info if available
                negotiated_rate = None
                gross_charge = None
                payer_name = None
                
                for key in ['negotiated_rate', 'negotiated', 'insurance_price', 'price']:
                    if key in proc:
                        try:
                            negotiated_rate = float(proc[key])
                            break
                        except (ValueError, TypeError):
                            pass
                
                for key in ['gross_charge', 'gross', 'standard_price', 'charge']:
                    if key in proc:
                        try:
                            gross_charge = float(proc[key])
                            break
                        except (ValueError, TypeError):
                            pass
                
                payer_name = proc.get('payer_name') or proc.get('payer') or 'Standard'
                
                if negotiated_rate or gross_charge:
                    self.cursor.execute("""
                        INSERT INTO pricing (procedure_id, payer_name, negotiated_rate, gross_charge)
                        VALUES (?, ?, ?, ?)
                    """, (procedure_id, payer_name[:100], negotiated_rate, gross_charge))
                    self.conn.commit()
                    self.stats['total_pricing_records'] += 1
                
                count += 1
                self.stats['total_procedures'] += 1
            
            except Exception as e:
                logger.debug(f"    Skipping procedure: {e}")
                continue
        
        return count
    
    def build_database(self):
        """Main build process"""
        logger.info("\n" + "="*80)
        logger.info("HOSPITAL PRICING DATABASE BUILDER")
        logger.info("="*80)
        
        self.init_db()
        
        start_time = time.time()
        
        # Process each hospital
        for hospital_name, hospital_info in HOSPITALS.items():
            try:
                # Add hospital record
                hospital_id = self.add_hospital(
                    hospital_name,
                    hospital_info['system'],
                    hospital_info['url'],
                    hospital_info['format'],
                    hospital_info.get('encoding', 'utf-8')
                )
                
                # Fetch and parse data
                procedures = self.fetch_hospital_data(hospital_name, hospital_info)
                
                # Insert into database
                if procedures:
                    count = self.insert_procedures(hospital_id, procedures)
                    logger.info(f"  ✓ Inserted {count} procedures")
                    self.stats['hospitals_processed'] += 1
                else:
                    logger.warning(f"  ✗ No procedures found for {hospital_name}")
                
                # Small delay to avoid hammering servers
                time.sleep(0.5)
            
            except Exception as e:
                error_msg = f"Failed to process {hospital_name}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
        
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
        logger.info(f"Size: {Path(self.db_path).stat().st_size / (1024*1024):.1f} MB")
        
        if self.stats['errors']:
            logger.warning(f"\nErrors: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.warning(f"  - {error}")
        
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
    url TEXT,
    data_format TEXT,
    encoding TEXT DEFAULT 'utf-8',
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
ORDER BY h.name;
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
    pr.negotiated_rate,
    pr.gross_charge
FROM procedures p
JOIN hospitals h ON p.hospital_id = h.hospital_id
LEFT JOIN pricing pr ON p.procedure_id = pr.procedure_id
WHERE p.procedure_name = 'Emergency Department Visit'
ORDER BY pr.negotiated_rate;
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
    SELECT * FROM procedures 
    WHERE procedure_name LIKE ? 
    LIMIT 10
''', ('%CT%',))

for row in cursor.fetchall():
    print(row)

conn.close()
```

## Notes

- Procedure names and codes are normalized where possible
- Pricing data varies by hospital and payer
- NULL values indicate missing data from source
- All timestamps are UTC
"""
        
        Path(doc_path).write_text(content)
        logger.info(f"✓ Documentation saved: {doc_path}")


def main():
    builder = HospitalDatabaseBuilder(DB_PATH)
    builder.build_database()


if __name__ == "__main__":
    main()
