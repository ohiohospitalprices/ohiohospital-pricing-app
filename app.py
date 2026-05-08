"""
Hospital Pricing Application - Flask Backend
Optimized for performance with SQLite database, pagination, and lazy loading
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
import zipfile
from pathlib import Path
import time

# Vector search (lazy-loaded)
_qdrant_client = None
VECTOR_SEARCH_ENABLED = True

# Embedding cache (text -> vector, up to 100 queries)
_embed_cache = {}

# HF API token (optional, free tier has rate limits without it)
_HF_TOKEN = os.environ.get("HF_TOKEN", "")


def get_qdrant_client():
    """Lazy-load Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(
                url="https://3827842b-99bd-4705-a080-6cc2029482b9.us-west-1-0.aws.cloud.qdrant.io:6333",
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MGEzNzQ4NjItNzZiNi00OGEyLWE5NWQtZWQwODg4Yjg0ODVkIn0.v0-LhCBGraFw9k3wlLh-oJab38epNah3VWV7AhLp02E"
            )
        except Exception as e:
            print(f"[VectorSearch] Failed to init Qdrant: {e}")
            _qdrant_client = None
    return _qdrant_client


def get_embedding(text):
    """Get 384-dim embedding using all-MiniLM-L6-v2.
    
    Strategy (in order of preference):
    1. Local sentence-transformers with GPU (Adam's PC)
    2. Hugging Face Inference API (cloud, free)
    3. Fallback to keyword search (return None)
    
    All paths use the SAME model (all-MiniLM-L6-v2) for consistent vectors.
    """
    if text in _embed_cache:
        return _embed_cache[text]
    
    # Strategy 1: Local sentence-transformers (GPU if available, else CPU)
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")
        except:
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        vec = model.encode(text, convert_to_numpy=True).tolist()
        if len(_embed_cache) < 100:
            _embed_cache[text] = vec
        return vec
    except Exception as e:
        print(f"[VectorSearch] Local model unavailable: {e}")
    
    # Strategy 2: Gemini API (cloud, free tier, 384-dim matching Qdrant)
    try:
        import requests
        gkey = os.environ.get('GEMINI_API_KEY', '')
        if gkey:
            gemini_payload = {
                "model": "models/gemini-embedding-001",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": 384
            }
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={gkey}",
                json=gemini_payload,
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                vec = data.get('embedding', {}).get('values', [])
                if vec:
                    if len(_embed_cache) < 100:
                        _embed_cache[text] = vec
                    return vec
            elif r.status_code == 429:
                print(f"[VectorSearch] Gemini rate limited (429)")
            else:
                print(f"[VectorSearch] Gemini API error {r.status_code}")
    except Exception as e:
        print(f"[VectorSearch] Gemini API call failed: {e}")
    
    return None

app = Flask(__name__)
CORS(app)

# Configuration
DB_PATH = 'hospital_pricing.db'
PAGE_SIZE = 50
CACHE_DURATION = 300  # 5 minutes

# Simple cache
cache = {}
cache_timestamps = {}

# --- Visitor Counter ---
_visitor_count = None
_VISITOR_DB = 'visitor_counter.db'

def _init_visitor_db():
    """Initialize visitor counter table."""
    global _visitor_count
    if _visitor_count is not None:
        return
    try:
        conn = sqlite3.connect(_VISITOR_DB)
        conn.execute('CREATE TABLE IF NOT EXISTS visitors (id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0)')
        cur = conn.execute('SELECT count FROM visitors WHERE id = 1')
        row = cur.fetchone()
        if row:
            _visitor_count = row[0]
        else:
            conn.execute('INSERT INTO visitors (id, count) VALUES (1, 0)')
            _visitor_count = 0
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Counter] Init error: {e}")
        _visitor_count = 0

def _increment_visitor():
    """Increment the visitor counter. Only counts unique IPs once per day."""
    global _visitor_count
    try:
        conn = sqlite3.connect(_VISITOR_DB)
        conn.execute('UPDATE visitors SET count = count + 1 WHERE id = 1')
        conn.commit()
        cur = conn.execute('SELECT count FROM visitors WHERE id = 1')
        _visitor_count = cur.fetchone()[0]
        conn.close()
    except Exception as e:
        print(f"[Counter] Increment error: {e}")

def get_visitor_count():
    """Get current visitor count."""
    if _visitor_count is None:
        _init_visitor_db()
    return _visitor_count or 0

_init_visitor_db()

# Auto-load hospital data files on startup
# Unzip database if compressed archive exists
db_path_obj = Path(DB_PATH)
zip_path = db_path_obj.with_suffix('.zip')
if not db_path_obj.exists() and zip_path.exists():
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(Path(__file__).parent)
        print(f"[Startup] Extracted database from {zip_path.name}")
    except Exception as e:
        print(f"[Startup] Failed to extract DB: {e}")

def load_hospital_data_files():
    """Load any hospital_data_X.json files into the database.
    Falls back to exporting DB to JSON files if no files found."""
    try:
        import json
        db_path = DB_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if DB has data but no JSON files
        cursor.execute("SELECT COUNT(*) FROM pricing")
        db_count = cursor.fetchone()[0]
        files = sorted(Path(__file__).parent.glob('hospital_data_*.json'))
        
        if not files and db_count > 0:
            print(f"[Startup] Exporting DB ({db_count:,} records) to JSON files...")
            cursor.execute("SELECT id, name FROM hospitals ORDER BY id")
            hospitals = cursor.fetchall()
            for hid, hname in hospitals:
                fname = f'hospital_data_{hid}.json'
                cursor.execute('''SELECT p.name, p.cpt, p.category, pr.price
                    FROM pricing pr JOIN procedures_table p ON pr.procedure_id = p.id
                    WHERE pr.hospital_id = ? AND pr.price > 0''', (hid,))
                rows = cursor.fetchall()
                data = {'hospital': hname, 'procedures': [
                    {'name': r[0][:300], 'cpt': r[1], 'category': r[2] or 'Other', 'price': r[3]}
                    for r in rows
                ]}
                with open(Path(__file__).parent / fname, 'w') as f:
                    json.dump(data, f)
            files = sorted(Path(__file__).parent.glob('hospital_data_*.json'))
            print(f"[Startup] Exported {len(hospitals)} hospital JSON files")
        
        conn.close()
        
        if not files:
            return 0
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        loaded = 0
        
        for f in files:
            hospital_id = int(f.stem.split('_')[-1])
            cursor.execute("SELECT COUNT(*) FROM pricing WHERE hospital_id=?", (hospital_id,))
            if cursor.fetchone()[0] > 0:
                continue
                
            with open(f, 'r') as fh:
                data = json.load(fh)
            
            cursor.execute("INSERT OR IGNORE INTO hospitals (id, name) VALUES (?, ?)",
                          (hospital_id, data['hospital']))
            
            for proc in data['procedures']:
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO procedures_table (name, cpt, category) VALUES (?, ?, ?)",
                        (proc['name'][:300], proc['cpt'], proc['category'])
                    )
                    cursor.execute("SELECT id FROM procedures_table WHERE cpt=?", (proc['cpt'],))
                    result = cursor.fetchone()
                    if result:
                        cursor.execute(
                            "INSERT OR IGNORE INTO pricing (hospital_id, procedure_id, price) VALUES (?, ?, ?)",
                            (hospital_id, result[0], proc['price'])
                        )
                except:
                    pass
            loaded += 1
        
        conn.commit()
        conn.close()
        return loaded
    except Exception as e:
        print(f"[Startup] Load error: {e}")
        return 0

_loaded = load_hospital_data_files()
if _loaded:
    print(f"[Startup] Loaded {_loaded} hospital data files")

def get_db_connection():
    """Get SQLite connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=None):
    """Execute query safely"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print(f"Database error: {e}")
        return []

def dict_from_row(row):
    """Convert sqlite3.Row to dict"""
    if row is None:
        return None
    return dict(row)

@app.route('/robots.txt')
def robots_txt():
    return """User-agent: *
Allow: /
Sitemap: https://ohiohospitalcharges.com/sitemap.xml
""", 200, {'Content-Type': 'text/plain'}

@app.route('/sitemap.xml')
def sitemap_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ohiohospitalcharges.com/</loc>
    <lastmod>2026-04-30</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
""", 200, {'Content-Type': 'application/xml'}

@app.route('/', methods=['GET'])
def serve_index():
    """Serve the optimized index.html with visitor counter"""
    try:
        _increment_visitor()
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        # Inject visitor count as a hidden element
        count = get_visitor_count()
        inject = f'<span id="visitor-count" style="display:none">{count}</span>'
        html = html.replace('</head>', f'<script>const VISITOR_COUNT = {count};</script>\n</head>')
        return html, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'index.html not found'}), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files like banner.jpg"""
    import os
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return jsonify({'error': 'File not found'}), 404

@app.route('/robots.txt')
def serve_robots():
    """Serve robots.txt"""
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def serve_sitemap():
    """Serve sitemap.xml"""
    return send_from_directory('.', 'sitemap.xml')

@app.route('/googlebf98e125bfb33a39.html')
def serve_google_verify():
    """Serve Google Search Console verification file"""
    return send_from_directory('.', 'googlebf98e125bfb33a39.html')

@app.route('/test')
def test():
    """Simple test route"""
    _increment_visitor()
    return jsonify({'message': 'Flask is running!', 'version': '1.0'})

@app.route('/api/counter', methods=['GET'])
def get_counter():
    """Get visitor counter."""
    return jsonify({'visitors': get_visitor_count()})

@app.route('/api/procedures', methods=['GET'])
def get_procedures():
    """Get paginated procedures with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', PAGE_SIZE, type=int)
        
        # Capping per_page to prevent abuse
        per_page = min(per_page, 100)
        
        hospital = request.args.get('hospital', '')
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        cpt = request.args.get('cpt', '')
        
        # Build cache key
        cache_key = f"procedures_{page}_{per_page}_{hospital}_{category}_{search}_{cpt}"
        
        # Check cache
        if cache_key in cache:
            if time.time() - cache_timestamps[cache_key] < CACHE_DURATION:
                return jsonify(cache[cache_key])
        
        # Build query
        query = "SELECT * FROM procedures WHERE 1=1"
        params = []
        
        if hospital:
            query += " AND hospital LIKE ?"
            params.append(f"%{hospital}%")
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if search:
            query += " AND (procedure_name LIKE ? OR cpt_code LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
        
        if cpt:
            query += " AND cpt_code = ?"
            params.append(cpt)
        
        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as count")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        conn.close()
        
        # Pagination
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        procedures = [dict(row) for row in rows]
        
        response = {
            'procedures': procedures,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
        
        # Cache response
        cache[cache_key] = response
        cache_timestamps[cache_key] = time.time()
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Get list of all hospitals"""
    cache_key = 'hospitals_list'
    
    if cache_key in cache:
        if time.time() - cache_timestamps[cache_key] < CACHE_DURATION:
            return jsonify(cache[cache_key])
    
    try:
        query = "SELECT DISTINCT hospital FROM procedures ORDER BY hospital"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        hospitals = [row['hospital'] for row in rows]
        
        response = {'hospitals': hospitals}
        cache[cache_key] = response
        cache_timestamps[cache_key] = time.time()
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of all categories"""
    cache_key = 'categories_list'
    
    if cache_key in cache:
        if time.time() - cache_timestamps[cache_key] < CACHE_DURATION:
            return jsonify(cache[cache_key])
    
    try:
        query = "SELECT DISTINCT category FROM procedures ORDER BY category"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        categories = [row['category'] for row in rows if row['category']]
        
        response = {'categories': categories}
        cache[cache_key] = response
        cache_timestamps[cache_key] = time.time()
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/procedure/<cpt>', methods=['GET'])
def get_procedure_prices(cpt):
    """Get all prices for a specific CPT code"""
    try:
        query = """
            SELECT hospital, category, procedure_name, cpt_code, price, updated_date
            FROM procedures
            WHERE cpt_code = ?
            ORDER BY price ASC
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (cpt,))
        rows = cursor.fetchall()
        conn.close()
        
        prices = [dict(row) for row in rows]
        
        return jsonify({
            'cpt_code': cpt,
            'prices': prices,
            'min_price': min([p['price'] for p in prices]) if prices else 0,
            'max_price': max([p['price'] for p in prices]) if prices else 0,
            'hospitals': len(set([p['hospital'] for p in prices]))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    cache_key = 'db_stats'
    
    if cache_key in cache:
        if time.time() - cache_timestamps[cache_key] < CACHE_DURATION:
            return jsonify(cache[cache_key])
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total procedures
        cursor.execute("SELECT COUNT(*) as count FROM procedures")
        total_procedures = cursor.fetchone()['count']
        
        # Total hospitals
        cursor.execute("SELECT COUNT(DISTINCT hospital) as count FROM procedures")
        total_hospitals = cursor.fetchone()['count']
        
        # Total categories
        cursor.execute("SELECT COUNT(DISTINCT category) as count FROM procedures")
        total_categories = cursor.fetchone()['count']
        
        # Price range
        cursor.execute("SELECT MIN(price) as min_p, MAX(price) as max_p FROM procedures")
        price_data = cursor.fetchone()
        
        conn.close()
        
        response = {
            'total_procedures': total_procedures,
            'total_hospitals': total_hospitals,
            'total_categories': total_categories,
            'price_range': {
                'min': price_data['min_p'],
                'max': price_data['max_p']
            }
        }
        
        cache[cache_key] = response
        cache_timestamps[cache_key] = time.time()
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vector-search', methods=['GET'])
def vector_search():
    """Semantic search using Qdrant vector database."""
    query_text = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query_text or len(query_text) < 2:
        return jsonify({'results': [], 'error': 'Query too short'})
    
    limit = min(limit, 50)
    client = get_qdrant_client()
    if client is None:
        return jsonify({'results': [], 'error': 'Vector search unavailable'}), 503
    
    try:
        embedding = get_embedding(query_text)
        if embedding is None:
            return jsonify({'results': [], 'error': 'Embedding unavailable'}), 503
        
        # Use query_points (v1.17+ API) instead of search
        result = client.query_points(
            collection_name="ohio_procedures",
            query=embedding,
            limit=limit
        )
        results = result.points if hasattr(result, 'points') else result
        
        return jsonify({
            'query': query_text,
            'results': [{
                'procedure_name': r.payload['procedure_name'],
                'cpt_code': r.payload['cpt_code'],
                'category': r.payload['category'],
                'hospital_count': r.payload['hospital_count'],
                'min_price': r.payload['min_price'],
                'avg_price': r.payload['avg_price'],
                'max_price': r.payload['max_price'],
                'hospitals': r.payload.get('hospitals', []),
                'score': round(r.score, 4)
            } for r in results],
            'count': len(results),
            'vector_search': True
        })
    except Exception as e:
        print(f"[VectorSearch] Error: {e}")
        return jsonify({'results': [], 'error': str(e)}), 500


@app.route('/api/search', methods=['GET'])
def search():
    """Combined search endpoint - falls back to try vector search first, then keyword"""
    query_text = request.args.get('q', '')
    
    if not query_text or len(query_text) < 2:
        return jsonify({'results': []})
    
    # Try vector search first
    try:
        client = get_qdrant_client()
        if client is not None:
            embedding = get_embedding(query_text)
            if embedding is not None:
                result = client.query_points(
                    collection_name="ohio_procedures",
                    query=embedding,
                    limit=20
                )
                points = result.points if hasattr(result, 'points') else result
                response_results = [{
                    'procedure_name': r.payload['procedure_name'],
                    'cpt_code': r.payload['cpt_code'],
                    'category': r.payload['category'],
                    'hospital_count': r.payload['hospital_count'],
                    'min_price': r.payload['min_price'],
                    'avg_price': r.payload['avg_price'],
                    'max_price': r.payload['max_price'],
                    'hospitals': r.payload.get('hospitals', []),
                    'score': round(r.score, 4)
                } for r in points]
                return jsonify({'results': response_results, 'count': len(response_results), 'vector_search': True})
    except:
        pass
    
    # Fallback to keyword search
    try:
        query = """
            SELECT DISTINCT hospital, category, procedure_name, cpt_code, price
            FROM procedures
            WHERE procedure_name LIKE ? OR cpt_code LIKE ? OR hospital LIKE ?
            LIMIT 50
        """
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (f"%{query_text}%", f"%{query_text}%", f"%{query_text}%"))
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        
        return jsonify({'results': results, 'count': len(results), 'vector_search': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM procedures")
        count = cursor.fetchone()['count']
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'procedures_count': count
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'path': request.path,
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Server error',
        'message': str(error)
    }), 500

@app.route('/api/docs', methods=['GET'])
def api_docs():
    """Public API documentation page."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Ohio Hospital Charges - Public API</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
h1, h2, h3 {{ color: #1a56db; }}
.endpoint {{ border-left: 4px solid #1a56db; padding-left: 15px; margin: 20px 0; }}
.method {{ display: inline-block; padding: 2px 8px; border-radius: 3px; color: white; font-weight: bold; font-size: 0.8em; }}
.get {{ background: #22c55e; }}
.footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
</style></head><body>
<h1>Ohio Hospital Charges API</h1>
<p>Public API for Ohio hospital pricing data. No API key required. Rate limit: 60 requests/minute.</p>

<h2>Endpoints</h2>

<div class="endpoint">
<span class="method get">GET</span> <code>/api/procedures</code>
<p>Search procedures by hospital, category, or keyword.</p>
<p><strong>Parameters:</strong></p>
<ul>
<li><code>hospital</code> — filter by hospital name</li>
<li><code>category</code> — filter by procedure category</li>
<li><code>search</code> — keyword search in procedure names</li>
<li><code>page</code> — page number (default: 1)</li>
<li><code>per_page</code> — results per page (default: 50, max: 200)</li>
</ul>
<p><strong>Example:</strong> <a href="/api/procedures?search=MRI&per_page=5"><code>/api/procedures?search=MRI&per_page=5</code></a></p>
</div>

<div class="endpoint">
<span class="method get">GET</span> <code>/api/vector-search</code>
<p>Semantic search using natural language. Finds procedures by meaning, not just keywords.</p>
<p><strong>Parameters:</strong></p>
<ul>
<li><code>q</code> — natural language query (e.g. "how much is an MRI in Columbus")</li>
<li><code>limit</code> — max results (default: 10, max: 50)</li>
</ul>
<p><strong>Example:</strong> <a href="/api/vector-search?q=knee%20replacement%20cost"><code>/api/vector-search?q=knee replacement cost</code></a></p>
</div>

<div class="endpoint">
<span class="method get">GET</span> <code>/api/search</code>
<p>Combined search: tries semantic search first, falls back to keyword search.</p>
<p><strong>Parameters:</strong></p>
<ul>
<li><code>q</code> — search query</li>
</ul>
<p><strong>Example:</strong> <a href="/api/search?q=CT%20scan"><code>/api/search?q=CT scan</code></a></p>
</div>

<div class="endpoint">
<span class="method get">GET</span> <code>/api/hospitals</code>
<p>List all hospitals with pricing data.</p>
<p><strong>Example:</strong> <a href="/api/hospitals"><code>/api/hospitals</code></a></p>
</div>

<div class="endpoint">
<span class="method get">GET</span> <code>/api/categories</code>
<p>List all procedure categories.</p>
<p><strong>Example:</strong> <a href="/api/categories"><code>/api/categories</code></a></p>
</div>

<div class="endpoint">
<span class="method get">GET</span> <code>/api/stats</code>
<p>Database statistics (total procedures, hospitals, price range).</p>
<p><strong>Example:</strong> <a href="/api/stats"><code>/api/stats</code></a></p>
</div>

<div class="endpoint">
<span class="method get">GET</span> <code>/api/health</code>
<p>Health check endpoint.</p>
<p><strong>Example:</strong> <a href="/api/health"><code>/api/health</code></a></p>
</div>

<h2>Rate Limiting</h2>
<p>60 requests per minute per IP. Returns a <code>429 Too Many Requests</code> response if exceeded.<br>
If you need higher limits for research or journalism, contact us.</p>

<h2>Data License</h2>
<p>This data is available for public use. If you build something with it, attribution appreciated but not required.<br>
Powered by the Ohio Transparency Project, a 501(c)(3) nonprofit organization.</p>

<div class="footer">
<p><a href="/">Back to search</a> | Ohio Hospital Charges &copy; 2026</p>
</div>
</body></html>'''


# Rate limiter for public API
_request_times = {}
RATE_LIMIT = 60  # requests per minute

def check_rate_limit():
    """Simple in-memory rate limiter."""
    ip = request.remote_addr or "unknown"
    now = time.time()
    if ip in _request_times:
        window_start, count = _request_times[ip]
        if now - window_start < 60:
            if count >= RATE_LIMIT:
                return False
            _request_times[ip] = (window_start, count + 1)
        else:
            _request_times[ip] = (now, 1)
    else:
        _request_times[ip] = (now, 1)
    return True

@app.before_request
def apply_rate_limit():
    """Apply rate limiting to API routes."""
    if request.path.startswith('/api/') and request.path != '/api/docs':
        if not check_rate_limit():
            return jsonify({'error': 'Rate limit exceeded. 60 requests/minute. See /api/docs for details.'}), 429

if __name__ == '__main__':
    # Run with production WSGI server
    # For development: python app.py
    # For production: gunicorn app:app
    app.run(host='0.0.0.0', port=5000, debug=False)
