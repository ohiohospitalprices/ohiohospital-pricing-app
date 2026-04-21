"""
HOSPITAL PRICING INTELLIGENT SEARCH API
=======================================

Production-ready Flask API with:
  - Intelligent fuzzy + synonym search
  - Medical term matching
  - Search history & analytics
  - <100ms response times for 152K procedures
  - RESTful endpoints
  - Built-in caching

Run: python hospital_search_api.py
"""

from flask import Flask, request, jsonify
from intelligent_search_engine_optimized import IntelligentSearchEngine
from datetime import datetime
import json
import os

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize search engine
search_engine = IntelligentSearchEngine()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/v1/search', methods=['GET'])
def search():
    """
    Intelligent procedure search endpoint
    
    Query parameters:
      - query (required): Search term (min 2 chars)
      - limit (optional): Max results (1-20, default 20)
    
    Returns:
      - results: List of matching procedures with scores
      - response_time_ms: How long the search took
      - confidence: 0.0-1.0 confidence in results
    
    Examples:
      GET /api/v1/search?query=knee+replacement&limit=10
      GET /api/v1/search?query=tka
      GET /api/v1/search?query=mri+brain
    """
    start_time = datetime.now()
    
    # Get parameters
    query = request.args.get('query', '').strip()
    limit = request.args.get('limit', '20')
    
    # Validation
    if not query:
        return jsonify({
            'error': 'Missing required parameter: query',
            'example': '/api/v1/search?query=knee+replacement&limit=10'
        }), 400
    
    if len(query) < 2:
        return jsonify({
            'error': 'Query must be at least 2 characters'
        }), 400
    
    try:
        limit = int(limit)
        if limit < 1 or limit > 20:
            limit = 20
    except ValueError:
        limit = 20
    
    # Perform search
    result = search_engine.search(query, limit=limit)
    
    # Response
    return jsonify({
        'query': query,
        'result_count': result['result_count'],
        'results': result['results'],
        'response_time_ms': result['response_time_ms'],
        'confidence': result['confidence'],
        'optimized': result['response_time_ms'] < 100
    }), 200


@app.route('/api/v1/search/suggest', methods=['GET'])
def search_suggest():
    """
    Get search suggestions based on partial input
    
    Query parameters:
      - query (required): Partial search term
      - limit (optional): Max suggestions (1-10, default 5)
    
    Returns:
      - suggestions: List of suggested full queries
    
    Example:
      GET /api/v1/search/suggest?query=knee
    """
    query = request.args.get('query', '').strip()
    limit = int(request.args.get('limit', '5'))
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []}), 200
    
    # Get search results to use as suggestions
    result = search_engine.search(query, limit=min(limit, 10))
    
    suggestions = [r['name'] for r in result['results'][:limit]]
    
    return jsonify({
        'query': query,
        'suggestions': suggestions,
        'count': len(suggestions)
    }), 200


@app.route('/api/v1/health', methods=['GET'])
def health():
    """
    Health check endpoint
    Returns API status and procedure count
    """
    stats = search_engine.get_stats()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'procedures_available': stats['total_procedures'],
        'response_time_ok': stats['avg_response_time_ms'] < 100
    }), 200


@app.route('/api/v1/stats', methods=['GET'])
def stats():
    """
    Get search engine statistics
    Shows performance metrics and usage patterns
    """
    stats_data = search_engine.get_stats()
    
    return jsonify({
        'database': {
            'total_procedures': stats_data['total_procedures'],
            'procedures_cached': stats_data['procedures_cached'],
            'cache_utilization': f"{(stats_data['procedures_cached']/stats_data['total_procedures']*100):.1f}%"
        },
        'performance': {
            'avg_response_time_ms': stats_data['avg_response_time_ms'],
            'max_response_time_ms': stats_data['max_response_time_ms'],
            'target_response_time_ms': 100,
            'compliant': stats_data['avg_response_time_ms'] < 100
        },
        'usage': {
            'total_searches': len(search_engine.search_history),
            'cached_searches': stats_data['cache_size'],
            'last_updated': datetime.now().isoformat()
        }
    }), 200


@app.route('/api/v1/help', methods=['GET'])
def help():
    """
    Get API documentation and usage examples
    """
    return jsonify({
        'title': 'Hospital Pricing Intelligent Search API',
        'version': '1.0',
        'description': 'Search 152K+ procedures with fuzzy matching, synonyms, and smart ranking',
        'endpoints': {
            'search': {
                'method': 'GET',
                'path': '/api/v1/search',
                'parameters': {
                    'query': 'Search term (required, min 2 chars)',
                    'limit': 'Max results (optional, 1-20, default 20)'
                },
                'examples': [
                    '/api/v1/search?query=knee+replacement',
                    '/api/v1/search?query=tka&limit=5',
                    '/api/v1/search?query=mri+brain',
                ]
            },
            'suggest': {
                'method': 'GET',
                'path': '/api/v1/search/suggest',
                'parameters': {
                    'query': 'Partial search term (required, min 2 chars)',
                    'limit': 'Max suggestions (optional, default 5)'
                },
                'examples': [
                    '/api/v1/search/suggest?query=knee',
                    '/api/v1/search/suggest?query=office&limit=10'
                ]
            },
            'health': {
                'method': 'GET',
                'path': '/api/v1/health',
                'description': 'Health check'
            },
            'stats': {
                'method': 'GET',
                'path': '/api/v1/stats',
                'description': 'Performance and usage statistics'
            },
            'help': {
                'method': 'GET',
                'path': '/api/v1/help',
                'description': 'This endpoint'
            }
        },
        'features': [
            'Fuzzy matching for typos',
            'Medical synonyms (knee replacement = TKA)',
            'Tokenized search',
            'Smart ranking by relevance',
            'Search caching',
            '<100ms response time',
            'Handles 152K+ procedures'
        ],
        'response_format': {
            'results': [
                {
                    'id': 'procedure_id',
                    'code': 'procedure_code',
                    'name': 'procedure_name',
                    'match_score': 0.95,
                    'match_type': 'exact|synonym|partial|token|fuzzy'
                }
            ],
            'response_time_ms': 15.23,
            'confidence': 0.95
        }
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'help': 'GET /api/v1/help'
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("HOSPITAL PRICING INTELLIGENT SEARCH API")
    print("="*70)
    print(f"\nDatabase: hospital_pricing.db")
    print(f"Procedures available: {search_engine.total_procedures:,}")
    print(f"\nEndpoints:")
    print("  GET /api/v1/search?query=NAME&limit=20")
    print("  GET /api/v1/search/suggest?query=PARTIAL")
    print("  GET /api/v1/health")
    print("  GET /api/v1/stats")
    print("  GET /api/v1/help")
    print(f"\nTarget response time: <100ms")
    print(f"\nStarting server...\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
