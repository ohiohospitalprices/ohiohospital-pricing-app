"""
Hospital Pricing Database Backend - Flask Application
Production-ready API for hospital procedure pricing and comparison
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from functools import lru_cache
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

app = Flask(__name__, static_folder='hospital-pricing-frontend', static_url_path='')
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', 'hospital_pricing.db')
DATA_DIR = os.getenv('DATA_DIR', './hospital_data')
os.makedirs(DATA_DIR, exist_ok=True)

# Hospital data URLs
HOSPITAL_URLS = {
    "Berger Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/384105653_berger-hospital_standardcharges.json",
    "Doctors Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_doctors-hospital_standardcharges.json",
    "Dublin Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_dublin-methodist-hospital_standardcharges.json",
    "Grady Memorial Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314379436_grady-memorial-hospital_standardcharges.json",
    "Grant Medical Center": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grant-medical-center_standardcharges.json",
    "Grove City Methodist": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_grove-city-methodist_standardcharges.json",
    "Hardin Memorial Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314440479_hardin-memorial-hospital_standardcharges.json",
    "Mansfield Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/310714456_ohiohealth-mansfield-hospital_standardcharges.json",
    "Marion General Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/311070887_marion-general-hospital_standardcharges.json",
    "O'Bleness Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314446959_ohiohealth-o-_bleness-hospital_standardcharges.json",
    "Pickerington Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_pickerington-methodist-hospital_standardcharges.json",
    "Riverside Methodist Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314394942_riverside-methodist-hospital_standardcharges.json",
    "Shelby Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/340714456_ohiohealth-shelby-hospital_standardcharges.json",
    "Southeastern Medical Center": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/314391798_southeastern-ohio-regional-medical-center_standardcharges.json",
    "Van Wert Hospital": "https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/344429514_van-wert-county-hospital_standardcharges.json"
}

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize SQLite database with optimized schema"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Procedures table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS procedures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procedure_code TEXT NOT NULL,
            procedure_name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(procedure_code)
        )
    ''')
    
    # Hospital pricing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            procedure_id INTEGER NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (procedure_id) REFERENCES procedures(id),
            UNIQUE(hospital_id, procedure_id)
        )
    ''')
    
    # Hospitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            url TEXT,
            last_updated TIMESTAMP
        )
    ''')
    
    # Create indexes for fast queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedure_name ON procedures(procedure_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedure_code ON procedures(procedure_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hospital_id ON hospital_pricing(hospital_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hospital_procedure ON hospital_pricing(hospital_id, procedure_id)')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# DATA LOADING & PARSING
# ============================================================================

def load_hospital_from_url(hospital_name: str, url: str) -> Optional[List[Dict]]:
    """Fetch and parse hospital pricing data from URL"""
    try:
        logger.info(f"Fetching data for {hospital_name}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Parse standard charge format
        procedures = []
        if isinstance(data, dict):
            # Handle different JSON structures
            items = data.get('standard_charges', data.get('procedures', []))
            if isinstance(items, list):
                for item in items:
                    procedures.append({
                        'code': item.get('code', item.get('procedure_code', '')),
                        'name': item.get('description', item.get('procedure_name', '')),
                        'price': item.get('price', item.get('gross_charge', 0)),
                        'hospital': hospital_name
                    })
        
        logger.info(f"Loaded {len(procedures)} procedures for {hospital_name}")
        return procedures
    except Exception as e:
        logger.error(f"Error loading data for {hospital_name}: {str(e)}")
        return None


def load_hospital_from_csv(csv_path: str, hospital_name: str) -> Optional[List[Dict]]:
    """Load hospital pricing from CSV file"""
    try:
        import csv
        procedures = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                procedures.append({
                    'code': row.get('procedure_code', ''),
                    'name': row.get('procedure_name', ''),
                    'price': float(row.get('price', 0)),
                    'hospital': hospital_name
                })
        logger.info(f"Loaded {len(procedures)} procedures from {csv_path}")
        return procedures
    except Exception as e:
        logger.error(f"Error loading CSV {csv_path}: {str(e)}")
        return None


def load_all_hospitals():
    """Load all hospital data into database"""
    conn = get_db()
    cursor = conn.cursor()
    
    total_procedures = 0
    
    for hospital_name, url in HOSPITAL_URLS.items():
        # Insert hospital record
        cursor.execute(
            'INSERT OR IGNORE INTO hospitals (name, url, last_updated) VALUES (?, ?, ?)',
            (hospital_name, url, datetime.now())
        )
        conn.commit()
        
        # Get hospital ID
        cursor.execute('SELECT id FROM hospitals WHERE name = ?', (hospital_name,))
        hospital_id = cursor.fetchone()[0]
        
        # Try loading from URL or CSV
        procedures = load_hospital_from_url(hospital_name, url)
        
        if not procedures:
            csv_path = os.path.join(DATA_DIR, f"{hospital_name}.csv")
            if os.path.exists(csv_path):
                procedures = load_hospital_from_csv(csv_path, hospital_name)
        
        if procedures:
            for proc in procedures:
                # Insert or update procedure
                cursor.execute(
                    'INSERT OR IGNORE INTO procedures (procedure_code, procedure_name) VALUES (?, ?)',
                    (proc['code'], proc['name'])
                )
                
                cursor.execute('SELECT id FROM procedures WHERE procedure_code = ?', (proc['code'],))
                proc_row = cursor.fetchone()
                if proc_row:
                    procedure_id = proc_row[0]
                    # Insert or update pricing
                    cursor.execute('''
                        INSERT OR REPLACE INTO hospital_pricing 
                        (hospital_id, procedure_id, price, updated_at)
                        VALUES (?, ?, ?, ?)
                    ''', (hospital_id, procedure_id, proc['price'], datetime.now()))
                    total_procedures += 1
            
            conn.commit()
    
    conn.close()
    logger.info(f"Loaded {total_procedures} total procedure prices")


# ============================================================================
# API ENDPOINTS
# ============================================================================
# ROUTES
# ============================================================================

@app.route('/', methods=['GET'])
def serve_homepage():
    """Serve the main search interface"""
    html_file = os.path.join(os.path.dirname(__file__), 'hospital-pricing-frontend', 'index.html')
    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return '<h1>Hospital Pricing Database</h1><p>Homepage loading...</p>', 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


@app.route('/api/search', methods=['GET'])
def search_procedures():
    """
    Search procedures by name and/or hospital
    
    Query Parameters:
    - query: procedure name (partial match, case-insensitive)
    - hospital: hospital name (optional)
    - limit: max results (default 50)
    
    Returns: List of matching procedures with hospitals and prices
    """
    query = request.args.get('query', '').strip()
    hospital = request.args.get('hospital', '').strip()
    limit = min(int(request.args.get('limit', 50)), 500)
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Query must be at least 2 characters'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Build dynamic SQL
    sql = '''
        SELECT DISTINCT
            p.id,
            p.procedure_code,
            p.procedure_name,
            h.id as hospital_id,
            h.name as hospital_name,
            hp.price
        FROM procedures p
        LEFT JOIN hospital_pricing hp ON p.id = hp.procedure_id
        LEFT JOIN hospitals h ON hp.hospital_id = h.id
        WHERE LOWER(p.procedure_name) LIKE LOWER(?)
    '''
    params = [f'%{query}%']
    
    if hospital:
        sql += ' AND LOWER(h.name) LIKE LOWER(?)'
        params.append(f'%{hospital}%')
    
    sql += ' ORDER BY p.procedure_name, h.name LIMIT ?'
    params.append(limit)
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Group by procedure
    results = {}
    for row in rows:
        proc_key = row['procedure_code']
        if proc_key not in results:
            results[proc_key] = {
                'procedure_code': row['procedure_code'],
                'procedure_name': row['procedure_name'],
                'hospitals': []
            }
        
        if row['hospital_name']:
            results[proc_key]['hospitals'].append({
                'name': row['hospital_name'],
                'price': row['price']
            })
    
    return jsonify({
        'query': query,
        'results': list(results.values()),
        'count': len(results)
    }), 200


@app.route('/api/compare', methods=['GET'])
def price_comparison():
    """
    Compare prices for a procedure across hospitals
    
    Query Parameters:
    - procedure: procedure code or name (required)
    - hospital: primary hospital name (optional, for highlighting)
    
    Returns: Selected hospital price + all other hospitals' prices
    """
    procedure = request.args.get('procedure', '').strip()
    hospital = request.args.get('hospital', '').strip()
    
    if not procedure or len(procedure) < 2:
        return jsonify({'error': 'Procedure parameter required (min 2 chars)'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Find procedure
    cursor.execute(
        'SELECT id, procedure_code, procedure_name FROM procedures WHERE procedure_code LIKE ? OR procedure_name LIKE ? LIMIT 1',
        (f'%{procedure}%', f'%{procedure}%')
    )
    proc = cursor.fetchone()
    
    if not proc:
        conn.close()
        return jsonify({'error': 'Procedure not found'}), 404
    
    procedure_id = proc['id']
    
    # Get all prices for this procedure
    cursor.execute('''
        SELECT
            h.name as hospital_name,
            hp.price,
            hp.updated_at
        FROM hospital_pricing hp
        JOIN hospitals h ON hp.hospital_id = h.id
        WHERE hp.procedure_id = ?
        ORDER BY hp.price ASC
    ''', (procedure_id,))
    
    pricing = cursor.fetchall()
    conn.close()
    
    if not pricing:
        return jsonify({'error': 'No pricing data found for this procedure'}), 404
    
    # Find selected hospital
    selected_hospital = None
    if hospital:
        selected_hospital = next(
            (p for p in pricing if hospital.lower() in p['hospital_name'].lower()),
            None
        )
    
    # Calculate statistics
    prices = [p['price'] for p in pricing]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    return jsonify({
        'procedure': {
            'code': proc['procedure_code'],
            'name': proc['procedure_name']
        },
        'selected_hospital': selected_hospital['hospital_name'] if selected_hospital else None,
        'selected_price': selected_hospital['price'] if selected_hospital else None,
        'statistics': {
            'average_price': round(avg_price, 2),
            'minimum_price': round(min_price, 2),
            'maximum_price': round(max_price, 2),
            'price_range': round(max_price - min_price, 2),
            'hospital_count': len(pricing)
        },
        'all_hospitals': [
            {
                'name': p['hospital_name'],
                'price': round(p['price'], 2),
                'updated': p['updated_at'],
                'is_selected': p['hospital_name'] == selected_hospital['hospital_name'] if selected_hospital else False
            }
            for p in pricing
        ]
    }), 200


@app.route('/api/hospitals', methods=['GET'])
def list_hospitals():
    """List all available hospitals"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, last_updated FROM hospitals ORDER BY name')
    hospitals = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'hospitals': [
            {
                'id': h['id'],
                'name': h['name'],
                'last_updated': h['last_updated']
            }
            for h in hospitals
        ],
        'count': len(hospitals)
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get database statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM procedures')
    proc_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM hospitals')
    hosp_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM hospital_pricing')
    pricing_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT MAX(updated_at) as last_update FROM hospital_pricing')
    last_update = cursor.fetchone()['last_update']
    
    conn.close()
    
    return jsonify({
        'statistics': {
            'total_procedures': proc_count,
            'total_hospitals': hosp_count,
            'total_pricing_records': pricing_count,
            'last_updated': last_update
        }
    }), 200


@app.route('/api/reload', methods=['POST'])
def reload_data():
    """Reload hospital data from sources (admin endpoint)"""
    try:
        # Clear existing data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM hospital_pricing')
        cursor.execute('DELETE FROM procedures')
        cursor.execute('DELETE FROM hospitals')
        conn.commit()
        conn.close()
        
        # Reload
        load_all_hospitals()
        
        return jsonify({'status': 'success', 'message': 'Data reloaded'}), 200
    except Exception as e:
        logger.error(f"Error reloading data: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# STARTUP
# ============================================================================

@app.before_request
def before_request():
    """Ensure DB is initialized"""
    if not os.path.exists(DATABASE_PATH):
        init_db()


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Load hospital data
    logger.info("Loading hospital data...")
    load_all_hospitals()
    
    # Start Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Starting Flask app on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
