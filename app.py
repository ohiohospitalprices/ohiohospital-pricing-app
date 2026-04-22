"""
Hospital Pricing Application - Flask Backend
Optimized for performance with SQLite database, pagination, and lazy loading
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from pathlib import Path
import time

app = Flask(__name__)
CORS(app)

# Configuration
DB_PATH = 'hospital_pricing.db'
PAGE_SIZE = 50
CACHE_DURATION = 300  # 5 minutes

# Simple cache
cache = {}
cache_timestamps = {}

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

@app.route('/', methods=['GET'])
def serve_index():
    """Serve the optimized index.html"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'index.html not found'}), 404

@app.route('/test')
def test():
    """Simple test route"""
    return jsonify({'message': 'Flask is running!', 'version': '1.0'})

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

@app.route('/api/search', methods=['GET'])
def search():
    """Combined search endpoint"""
    query_text = request.args.get('q', '')
    
    if not query_text or len(query_text) < 2:
        return jsonify({'results': []})
    
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
        
        return jsonify({'results': results, 'count': len(results)})
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

if __name__ == '__main__':
    # Run with production WSGI server
    # For development: python app.py
    # For production: gunicorn app:app
    app.run(host='0.0.0.0', port=5000, debug=False)
