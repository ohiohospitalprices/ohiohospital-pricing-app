# Hospital Pricing Database API Documentation

## Overview

Production-ready Flask backend for hospital procedure pricing and comparison. Features include:

- **Search procedures** by name and hospital
- **Compare prices** across hospitals
- **Fast indexing** via SQLite with optimized queries
- **CORS enabled** for web integration
- **Render deployment ready** with gunicorn configuration

---

## Base URL

**Local Development:**
```
http://localhost:5000
```

**Production (Render):**
```
https://your-app-name.onrender.com
```

---

## API Endpoints

### 1. Health Check
**GET** `/health`

Simple health check endpoint to verify API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-17T19:41:00.000000"
}
```

---

### 2. Search Procedures
**GET** `/api/search`

Search for hospital procedures by name and optional hospital filter.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Procedure name (min 2 characters, case-insensitive) |
| hospital | string | No | Filter by hospital name (partial match) |
| limit | integer | No | Max results (default: 50, max: 500) |

**Example Requests:**
```
GET /api/search?query=surgery
GET /api/search?query=cardiac&hospital=Riverside
GET /api/search?query=x-ray&limit=20
```

**Response:**
```json
{
  "query": "cardiac surgery",
  "count": 3,
  "results": [
    {
      "procedure_code": "92004",
      "procedure_name": "CARDIAC SURGERY - CORONARY BYPASS",
      "hospitals": [
        {
          "name": "Riverside Methodist Hospital",
          "price": 45000.00
        },
        {
          "name": "Grant Medical Center",
          "price": 48500.00
        }
      ]
    }
  ]
}
```

**Error Response:**
```json
{
  "error": "Query must be at least 2 characters"
}
```

---

### 3. Price Comparison
**GET** `/api/compare`

Compare prices for a specific procedure across all hospitals.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| procedure | string | Yes | Procedure code or name (min 2 characters) |
| hospital | string | No | Primary hospital to highlight in results |

**Example Requests:**
```
GET /api/compare?procedure=92004
GET /api/compare?procedure=cardiac&hospital=Riverside Methodist Hospital
GET /api/compare?procedure=hip replacement
```

**Response:**
```json
{
  "procedure": {
    "code": "92004",
    "name": "CARDIAC SURGERY - CORONARY BYPASS"
  },
  "selected_hospital": "Riverside Methodist Hospital",
  "selected_price": 45000.00,
  "statistics": {
    "average_price": 46250.00,
    "minimum_price": 43500.00,
    "maximum_price": 52000.00,
    "price_range": 8500.00,
    "hospital_count": 12
  },
  "all_hospitals": [
    {
      "name": "Berger Hospital",
      "price": 43500.00,
      "updated": "2026-04-17T19:30:00",
      "is_selected": false
    },
    {
      "name": "Riverside Methodist Hospital",
      "price": 45000.00,
      "updated": "2026-04-17T19:30:00",
      "is_selected": true
    }
  ]
}
```

**Error Response:**
```json
{
  "error": "Procedure not found"
}
```

---

### 4. List Hospitals
**GET** `/api/hospitals`

Get list of all available hospitals in the database.

**Response:**
```json
{
  "hospitals": [
    {
      "id": 1,
      "name": "Berger Hospital",
      "last_updated": "2026-04-17T19:30:00"
    },
    {
      "id": 2,
      "name": "Doctors Hospital",
      "last_updated": "2026-04-17T19:30:00"
    }
  ],
  "count": 15
}
```

---

### 5. Database Statistics
**GET** `/api/stats`

Get current database statistics and last update time.

**Response:**
```json
{
  "statistics": {
    "total_procedures": 3200,
    "total_hospitals": 15,
    "total_pricing_records": 48000,
    "last_updated": "2026-04-17T19:30:00"
  }
}
```

---

### 6. Reload Data (Admin)
**POST** `/api/reload`

Force reload hospital data from all sources. **⚠️ Use with caution - clears existing data.**

**Response:**
```json
{
  "status": "success",
  "message": "Data reloaded"
}
```

---

## Error Responses

All errors follow standard HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (invalid query parameters) |
| 404 | Resource not found |
| 500 | Server error |

**Error Response Format:**
```json
{
  "error": "Description of error"
}
```

---

## Data Structure

### Procedure Object
```json
{
  "procedure_code": "92004",
  "procedure_name": "CARDIAC SURGERY - CORONARY BYPASS",
  "description": "Optional description"
}
```

### Hospital Object
```json
{
  "id": 1,
  "name": "Riverside Methodist Hospital",
  "url": "https://example.com/pricing.json",
  "last_updated": "2026-04-17T19:30:00"
}
```

### Pricing Record
```json
{
  "hospital_id": 1,
  "procedure_id": 100,
  "price": 45000.00,
  "currency": "USD",
  "updated_at": "2026-04-17T19:30:00"
}
```

---

## Query Examples

### Find all cardiac procedures
```bash
curl "http://localhost:5000/api/search?query=cardiac"
```

### Find hip replacement at a specific hospital
```bash
curl "http://localhost:5000/api/search?query=hip%20replacement&hospital=Riverside"
```

### Compare prices for knee replacement across all hospitals
```bash
curl "http://localhost:5000/api/compare?procedure=knee%20replacement"
```

### Compare prices and highlight a specific hospital
```bash
curl "http://localhost:5000/api/compare?procedure=92004&hospital=Grant%20Medical%20Center"
```

### Get database status
```bash
curl "http://localhost:5000/api/stats"
```

---

## Performance Characteristics

- **Search**: O(log n) with indexed procedure names
- **Comparison**: O(m) where m = number of hospitals (~15)
- **Index coverage**: procedure_name, procedure_code, hospital_id, hospital+procedure combo
- **Max query limit**: 500 results (configurable in request)

---

## Deployment to Render

1. **Push to Git repository**
   ```bash
   git add app.py requirements.txt render.yaml
   git commit -m "Add hospital pricing API"
   git push origin main
   ```

2. **Create Render service:**
   - Go to https://dashboard.render.com
   - Connect GitHub repository
   - Select this repository
   - Create new Web Service
   - Build uses `render.yaml` config
   - Deploy!

3. **Environment Variables (set in Render Dashboard):**
   ```
   FLASK_ENV=production
   DATABASE_PATH=/tmp/hospital_pricing.db
   DATA_DIR=/app/hospital_data
   ```

---

## Local Development

**Setup:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Run:**
```bash
export FLASK_ENV=development
python app.py
```

**Test:**
```bash
curl http://localhost:5000/health
curl "http://localhost:5000/api/search?query=cardiac"
```

---

## Data Import

### From CSV Files
Place CSV files in `hospital_data/` directory:
```
hospital_data/
├── Riverside Hospital.csv
├── Grant Medical Center.csv
└── ...
```

CSV format:
```
procedure_code,procedure_name,price
92004,CARDIAC SURGERY - CORONARY BYPASS,45000.00
92005,CARDIAC SURGERY - VALVE REPLACEMENT,52000.00
```

### From URLs
Hospital URLs are configured in `app.py` HOSPITAL_URLS dict and auto-fetched on startup.

### Manual Reload
```bash
curl -X POST http://localhost:5000/api/reload
```

---

## Optimization Notes

- **Indexing**: All search columns are indexed for O(log n) lookups
- **Connection pooling**: SQLite handles concurrent reads efficiently
- **Response compression**: Flask can gzip large responses (enable in production)
- **Caching**: Consider adding Redis cache layer for frequently searched procedures

---

## Support

For issues or questions:
1. Check logs: `docker logs hospital-pricing-api`
2. Verify database: `sqlite3 hospital_pricing.db ".tables"`
3. Test health endpoint: `curl http://localhost:5000/health`

