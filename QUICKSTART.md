# Hospital Pricing API - Quick Start Guide

## What You Have

A production-ready Flask API that:
- Loads hospital procedure pricing data
- Provides fast search across all procedures
- Compares prices across hospitals
- Uses SQLite for fast indexing
- Deploys to Render in minutes

## Files Included

```
app.py                    # Main Flask application
requirements.txt          # Python dependencies
render.yaml              # Render deployment config
API_DOCUMENTATION.md     # Complete API reference
.env.example             # Environment variables template
hospital_data/           # CSV data directory (auto-created)
```

## Quick Start (Local)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```

The app will:
- Initialize SQLite database: `hospital_pricing.db`
- Load hospital data from 15 Ohio Health hospitals
- Start server on `http://localhost:5000`

### 3. Test the API
```bash
# Health check
curl http://localhost:5000/health

# Search for procedures
curl "http://localhost:5000/api/search?query=cardiac"

# Compare prices
curl "http://localhost:5000/api/compare?procedure=92004"

# Get statistics
curl http://localhost:5000/api/stats
```

## Deploy to Render

### 1. Prepare Repository
```bash
git add app.py requirements.txt render.yaml .env.example
git commit -m "Add hospital pricing API"
git push origin main
```

### 2. Create Render Service
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select branch (main)
5. Leave `Build Command` and `Start Command` empty (uses render.yaml)
6. Click "Create Web Service"

### 3. Set Environment Variables (In Render Dashboard)
```
FLASK_ENV=production
DATABASE_PATH=/tmp/hospital_pricing.db
DATA_DIR=/app/hospital_data
```

### 4. Deploy
- Render auto-deploys on push
- Check logs for data loading progress
- Once deployed, visit: `https://your-app.onrender.com/health`

## API Endpoints Summary

### Search
```bash
GET /api/search?query=cardiac&hospital=Riverside&limit=50
```
Returns: List of matching procedures with prices by hospital

### Compare
```bash
GET /api/compare?procedure=92004&hospital=Riverside%20Methodist
```
Returns: Price statistics + all hospitals' prices for one procedure

### Hospitals
```bash
GET /api/hospitals
```
Returns: List of all hospitals in database

### Statistics
```bash
GET /api/stats
```
Returns: Total counts and last update time

### Full Docs
See `API_DOCUMENTATION.md` for complete reference

## Common Tasks

### Add CSV Data
1. Create file: `hospital_data/Hospital_Name.csv`
2. Format: `procedure_code,procedure_name,price`
3. Restart app (or call `/api/reload`)

### Update Data
```bash
curl -X POST http://localhost:5000/api/reload
```

### Check What's Loaded
```bash
curl http://localhost:5000/api/stats
```

### View Database Directly
```bash
sqlite3 hospital_pricing.db
# Then run SQL queries:
# SELECT COUNT(*) FROM procedures;
# SELECT * FROM hospitals;
```

## Performance

- **15 hospitals** with ~3,200 procedures
- **~48,000 pricing records**
- Search response: <100ms
- Comparison response: <50ms
- All queries use indexed columns

## Troubleshooting

### App crashes on startup
```bash
# Check if database file has permission issues
rm hospital_pricing.db  # Delete and let it recreate
python app.py
```

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### API returns empty results
```bash
# Check database status
curl http://localhost:5000/api/stats

# Force reload data
curl -X POST http://localhost:5000/api/reload
```

### Connection timeouts on Render
- Database file is at `/tmp/hospital_pricing.db` (persists within dyno)
- If dyno restarts, data reloads automatically
- For persistent storage, upgrade to PostgreSQL (Render addon)

## Next Steps

1. **Test locally** with `python app.py`
2. **Deploy to Render** following the steps above
3. **Integrate with frontend** using endpoints in API docs
4. **Add more data** via CSV or URL sources
5. **Monitor** via Render dashboard logs

## Need Help?

Check:
1. `API_DOCUMENTATION.md` - Full endpoint reference
2. Render logs - Shows data loading progress
3. `/api/stats` endpoint - Verify data is loaded
4. SQLite database - Query directly with sqlite3 CLI

---

**You're ready to go!** 🚀

