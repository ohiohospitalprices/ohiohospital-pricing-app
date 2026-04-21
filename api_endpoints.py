"""
Hospital Pricing Search API Endpoints
Provides: /api/search, /api/hospitals, /api/pricing with <100ms response times
Uses fuzzy matching for procedure names and SQLite for optimization
"""

from flask import Flask, request, jsonify
from difflib import SequenceMatcher
import sqlite3
import json
import time
from contextlib import contextmanager
from typing import List, Dict, Tuple, Optional
import os

app = Flask(__name__)

# Database configuration
DB_PATH = "hospital_pricing.db"
PROCEDURE_CACHE = {}  # In-memory cache for procedure names (for fuzzy matching)
HOSPITAL_CACHE = {}   # In-memory cache for hospitals
CACHE_TIME = {}       # Track cache age

# Configuration
FUZZY_MATCH_THRESHOLD = 0.6  # Minimum similarity score for fuzzy matching
MAX_SEARCH_RESULTS = 50
RESPONSE_TIMEOUT_MS = 100


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize database schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Hospitals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                system TEXT NOT NULL,
                state TEXT DEFAULT 'OH',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Procedures table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS procedures (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for procedure names (for search)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedure_name ON procedures(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedure_code ON procedures(code)')
        
        # Pricing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pricing (
                id INTEGER PRIMARY KEY,
                hospital_id INTEGER NOT NULL,
                procedure_id INTEGER NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                source TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
                FOREIGN KEY (procedure_id) REFERENCES procedures(id),
                UNIQUE(hospital_id, procedure_id)
            )
        ''')
        
        # Create composite index for pricing queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pricing_lookup 
            ON pricing(hospital_id, procedure_id)
        ''')
        
        conn.commit()


def load_cache():
    """Load procedures and hospitals into memory cache"""
    global PROCEDURE_CACHE, HOSPITAL_CACHE, CACHE_TIME
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Load procedures
            cursor.execute('SELECT id, code, name FROM procedures')
            PROCEDURE_CACHE = {row['id']: {
                'code': row['code'],
                'name': row['name'],
                'name_lower': row['name'].lower()
            } for row in cursor.fetchall()}
            
            # Load hospitals
            cursor.execute('SELECT id, name, system FROM hospitals ORDER BY name')
            HOSPITAL_CACHE = {row['id']: {
                'name': row['name'],
                'system': row['system']
            } for row in cursor.fetchall()}
            
            CACHE_TIME['loaded_at'] = time.time()
    except Exception as e:
        print(f"Cache load error: {str(e)}")


def fuzzy_match(query: str, target: str, threshold: float = FUZZY_MATCH_THRESHOLD) -> Tuple[bool, float]:
    """
    Fuzzy match query against target string
    Returns (matches, similarity_score)
    """
    query_lower = query.lower()
    target_lower = target.lower()
    
    # Exact match (best)
    if query_lower == target_lower:
        return True, 1.0
    
    # Substring match (good)
    if query_lower in target_lower:
        return True, 0.95
    
    # Fuzzy match
    ratio = SequenceMatcher(None, query_lower, target_lower).ratio()
    return ratio >= threshold, ratio


def search_procedures(query: str, limit: int = MAX_SEARCH_RESULTS) -> List[Dict]:
    """
    Search procedures with fuzzy matching
    Optimized for <100ms response time
    """
    if not query or len(query) < 2:
        return []
    
    results = []
    
    # Use in-memory cache for fast fuzzy matching
    for proc_id, proc_data in PROCEDURE_CACHE.items():
        matches, score = fuzzy_match(query, proc_data['name'])
        if matches:
            results.append({
                'id': proc_id,
                'code': proc_data['code'],
                'name': proc_data['name'],
                'match_score': score
            })
    
    # Sort by match score (descending) and limit results
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return results[:limit]


@app.route('/api/search', methods=['GET'])
def search():
    """
    Search for procedures with auto-complete
    Query: ?query=PROCEDURE_NAME&limit=20
    Returns: matching procedures with scores
    """
    start_time = time.time()
    
    query = request.args.get('query', '').strip()
    limit = min(int(request.args.get('limit', MAX_SEARCH_RESULTS)), MAX_SEARCH_RESULTS)
    
    # Validation
    if not query:
        return jsonify({'error': 'query parameter required'}), 400
    
    if len(query) < 2:
        return jsonify({'error': 'query must be at least 2 characters'}), 400
    
    # Search
    results = search_procedures(query, limit)
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    return jsonify({
        'query': query,
        'count': len(results),
        'results': results,
        'response_time_ms': round(response_time_ms, 2),
        'optimized': response_time_ms < RESPONSE_TIMEOUT_MS
    }), 200


@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """
    Get all hospitals
    Returns: list of all 23 hospitals with IDs and systems
    """
    start_time = time.time()
    
    hospitals = [
        {
            'id': hosp_id,
            'name': hosp_data['name'],
            'system': hosp_data['system']
        }
        for hosp_id, hosp_data in HOSPITAL_CACHE.items()
    ]
    
    response_time_ms = (time.time() - start_time) * 1000
    
    return jsonify({
        'count': len(hospitals),
        'hospitals': hospitals,
        'response_time_ms': round(response_time_ms, 2)
    }), 200


@app.route('/api/pricing', methods=['GET'])
def get_pricing():
    """
    Get pricing for a procedure with comparison
    Query: ?procedure=NAME&hospital=ID
    Returns: specific hospital price + all other hospitals for comparison
    """
    start_time = time.time()
    
    procedure_name = request.args.get('procedure', '').strip()
    hospital_id = request.args.get('hospital', '').strip()
    
    # Validation
    if not procedure_name:
        return jsonify({'error': 'procedure parameter required'}), 400
    
    if not hospital_id:
        return jsonify({'error': 'hospital parameter required'}), 400
    
    try:
        hospital_id = int(hospital_id)
    except ValueError:
        return jsonify({'error': 'hospital must be a valid ID'}), 400
    
    # Find procedure by name (fuzzy match)
    matching_procs = search_procedures(procedure_name, 1)
    if not matching_procs:
        return jsonify({
            'error': f'procedure not found: {procedure_name}',
            'suggestions': search_procedures(procedure_name, 5)
        }), 404
    
    procedure_id = matching_procs[0]['id']
    procedure_data = PROCEDURE_CACHE.get(procedure_id)
    
    # Check hospital exists
    if hospital_id not in HOSPITAL_CACHE:
        return jsonify({'error': f'hospital not found: {hospital_id}'}), 404
    
    hospital_data = HOSPITAL_CACHE[hospital_id]
    
    # Get pricing data from database
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get price for selected hospital
        cursor.execute('''
            SELECT price FROM pricing 
            WHERE hospital_id = ? AND procedure_id = ?
        ''', (hospital_id, procedure_id))
        
        selected_price_row = cursor.fetchone()
        selected_price = float(selected_price_row['price']) if selected_price_row else None
        
        # Get prices for all hospitals (for comparison)
        cursor.execute('''
            SELECT 
                h.id, h.name, h.system, p.price
            FROM pricing p
            JOIN hospitals h ON p.hospital_id = h.id
            WHERE p.procedure_id = ?
            ORDER BY p.price ASC
        ''', (procedure_id,))
        
        comparisons = [{
            'hospital_id': row['id'],
            'hospital_name': row['name'],
            'system': row['system'],
            'price': float(row['price'])
        } for row in cursor.fetchall()]
    
    response_time_ms = (time.time() - start_time) * 1000
    
    result = {
        'procedure': {
            'id': procedure_id,
            'code': procedure_data['code'],
            'name': procedure_data['name']
        },
        'selected_hospital': {
            'id': hospital_id,
            'name': hospital_data['name'],
            'system': hospital_data['system'],
            'price': selected_price
        },
        'comparison': {
            'count': len(comparisons),
            'hospitals': comparisons,
            'statistics': {
                'average_price': round(sum(c['price'] for c in comparisons) / len(comparisons), 2) if comparisons else None,
                'min_price': min(c['price'] for c in comparisons) if comparisons else None,
                'max_price': max(c['price'] for c in comparisons) if comparisons else None,
                'price_difference_from_min': round(selected_price - min(c['price'] for c in comparisons), 2) if selected_price and comparisons else None,
                'price_rank': next((i + 1 for i, c in enumerate(comparisons) if c['hospital_id'] == hospital_id), None)
            }
        },
        'response_time_ms': round(response_time_ms, 2),
        'optimized': response_time_ms < RESPONSE_TIMEOUT_MS
    }
    
    return jsonify(result), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get database statistics
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM hospitals')
        hospital_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM procedures')
        procedure_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM pricing')
        pricing_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT MAX(updated_at) as last_update FROM pricing')
        last_update = cursor.fetchone()['last_update']
    
    return jsonify({
        'statistics': {
            'total_hospitals': hospital_count,
            'total_procedures': procedure_count,
            'total_pricing_records': pricing_count,
            'last_updated': last_update,
            'cache_loaded': CACHE_TIME.get('loaded_at')
        }
    }), 200


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'hospital-pricing-api'}), 200


@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return jsonify({'error': 'endpoint not found'}), 404


@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    return jsonify({'error': 'internal server error', 'details': str(e)}), 500


def seed_database_with_sample_data():
    """
    Seed database with sample hospital and procedure data for testing
    This should be replaced with real data loading
    """
    hospitals_data = [
        ("Berger Hospital", "OhioHealth"),
        ("Doctors Hospital", "OhioHealth"),
        ("Dublin Methodist Hospital", "OhioHealth"),
        ("Grady Memorial Hospital", "OhioHealth"),
        ("Grant Medical Center", "OhioHealth"),
        ("Grove City Methodist", "OhioHealth"),
        ("Hardin Memorial Hospital", "OhioHealth"),
        ("Mansfield Hospital", "OhioHealth"),
        ("Marion General Hospital", "OhioHealth"),
        ("Morrow County Hospital", "OhioHealth"),
        ("O'Bleness Hospital", "OhioHealth"),
        ("Pickerington Methodist Hospital", "OhioHealth"),
        ("Riverside Methodist Hospital", "OhioHealth"),
        ("Shelby Hospital", "OhioHealth"),
        ("Southeastern Medical Center", "OhioHealth"),
        ("Van Wert Hospital", "OhioHealth"),
        ("Ohio State University Medical Center", "Ohio State University"),
        ("James Cancer Hospital", "Ohio State University"),
        ("Mount Carmel East", "Mount Carmel"),
        ("Mount Carmel Grove City", "Mount Carmel"),
        ("Mount Carmel New Albany", "Mount Carmel"),
        ("Mount Carmel St. Ann's", "Mount Carmel"),
        ("Mount Carmel Dublin", "Mount Carmel"),
    ]
    
    procedures_data = [
        ("99213", "Office Visit - Established Patient"),
        ("99214", "Office Visit - Established Patient (Complex)"),
        ("70450", "CT Head/Brain without Contrast"),
        ("70553", "MRI Brain with Contrast"),
        ("93000", "12-Lead Electrocardiogram"),
        ("78452", "Myocardial Perfusion Imaging"),
        ("27447", "Total Knee Arthroplasty"),
        ("22630", "Spinal Fusion - Lumbar"),
        ("99285", "Emergency Department - High Complexity"),
        ("43239", "Upper Endoscopy with Biopsy"),
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute('DELETE FROM pricing')
        cursor.execute('DELETE FROM procedures')
        cursor.execute('DELETE FROM hospitals')
        
        # Insert hospitals
        hospital_ids = {}
        for name, system in hospitals_data:
            cursor.execute('INSERT OR IGNORE INTO hospitals (name, system) VALUES (?, ?)', 
                         (name, system))
            cursor.execute('SELECT id FROM hospitals WHERE name = ?', (name,))
            hospital_ids[name] = cursor.fetchone()['id']
        
        # Insert procedures
        procedure_ids = {}
        for code, name in procedures_data:
            cursor.execute('INSERT OR IGNORE INTO procedures (code, name) VALUES (?, ?)', 
                         (code, name))
            cursor.execute('SELECT id FROM procedures WHERE code = ?', (code,))
            procedure_ids[name] = cursor.fetchone()['id']
        
        # Insert sample pricing (random prices for testing)
        import random
        random.seed(42)  # For reproducible pricing
        
        price_ranges = {
            "Office Visit": (100, 300),
            "CT Head": (1200, 2500),
            "MRI Brain": (2000, 4500),
            "Electrocardiogram": (50, 150),
            "Myocardial": (2000, 5000),
            "Knee Arthroplasty": (35000, 65000),
            "Spinal Fusion": (50000, 120000),
            "Emergency": (500, 2000),
            "Endoscopy": (2000, 5000),
        }
        
        for hosp_name, hosp_id in hospital_ids.items():
            for proc_name, proc_id in procedure_ids.items():
                # Find price range based on procedure
                price_range = None
                for key, range_val in price_ranges.items():
                    if key in proc_name:
                        price_range = range_val
                        break
                
                if not price_range:
                    price_range = (500, 5000)
                
                # Generate price with slight variation by hospital
                base_price = random.uniform(*price_range)
                variation = random.uniform(0.85, 1.15)
                price = round(base_price * variation, 2)
                
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO pricing 
                        (hospital_id, procedure_id, price) 
                        VALUES (?, ?, ?)
                    ''', (hosp_id, proc_id, price))
                except sqlite3.IntegrityError:
                    pass
        
        conn.commit()
        print(f"[OK] Database seeded with {len(hospitals_data)} hospitals and {len(procedures_data)} procedures")


if __name__ == '__main__':
    # Initialize
    init_database()
    seed_database_with_sample_data()
    load_cache()
    
    print(f"\n{'='*60}")
    print("HOSPITAL PRICING SEARCH API")
    print(f"{'='*60}")
    print(f"Database: {DB_PATH}")
    print(f"Hospitals cached: {len(HOSPITAL_CACHE)}")
    print(f"Procedures cached: {len(PROCEDURE_CACHE)}")
    print(f"\nEndpoints:")
    print("  GET /api/search?query=NAME&limit=20")
    print("  GET /api/hospitals")
    print("  GET /api/pricing?procedure=NAME&hospital=ID")
    print("  GET /api/stats")
    print(f"\nTarget response time: <{RESPONSE_TIMEOUT_MS}ms\n")
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
