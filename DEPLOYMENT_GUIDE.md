# Hospital Pricing API - Deployment Guide

## Overview

This guide covers deploying the Hospital Pricing Database API to production. Multiple deployment options are available:

1. **Render** (recommended) - Zero-config, free tier available
2. **Docker** - For self-hosted or custom deployments
3. **Local** - For development and testing

---

## Deployment Option 1: Render (Recommended)

### Why Render?

✅ Auto-deploys on git push  
✅ Free tier available  
✅ Built-in SSL/HTTPS  
✅ Environment variables in dashboard  
✅ Logs and monitoring included  
✅ Auto-scales (on paid plan)  

### Step-by-Step

#### 1. Prepare Your Repository

```bash
# Ensure all files are committed
git add app.py requirements.txt render.yaml .env.example
git commit -m "Add hospital pricing API"
git push origin main
```

#### 2. Create Render Service

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. **Connect Repository**:
   - Select your GitHub repository
   - Select branch (usually `main`)
4. **Configure**:
   - Name: `hospital-pricing-api`
   - Region: Choose closest to your users
   - Branch: `main`
   - Build Command: (leave empty - uses render.yaml)
   - Start Command: (leave empty - uses render.yaml)
   - Plan: Starter ($7/month) or Free
5. **Create Web Service**

#### 3. Set Environment Variables

In Render Dashboard → Your Service → Environment:

```
FLASK_ENV=production
DATABASE_PATH=/tmp/hospital_pricing.db
DATA_DIR=/app/hospital_data
```

#### 4. Deploy

- Click **Manual Deploy** or push to trigger auto-deploy
- Check **Logs** tab to watch deployment
- Once built, service URL appears at top (e.g., `https://hospital-pricing-api.onrender.com`)

#### 5. Test Deployment

```bash
# Replace with your Render URL
curl https://hospital-pricing-api.onrender.com/health
curl "https://hospital-pricing-api.onrender.com/api/stats"
```

### Render Pricing

- **Free tier**: 1 shared CPU, 512MB RAM, auto-sleeps after 15min inactivity
- **Starter ($7/month)**: Dedicated resources, no sleep
- **Standard ($12/month)**: More resources, better performance

**Tip**: Free tier is great for testing/demo. Upgrade to Starter for consistent availability.

### Known Render Issues & Solutions

**Issue**: Database resets after dyno restart
- **Solution**: Use persistent volume or upgrade to PostgreSQL add-on
- **Current**: Data reloads automatically on startup (OK for read-heavy workloads)

**Issue**: Slow first request (cold start)
- **Solution**: Upgrade to Starter plan (keeps dyno warm)
- **Current**: Free tier sleeps after 15min inactivity

**Issue**: "No space left on device"
- **Solution**: Database is at `/tmp` (ephemeral, ~10GB)
- **Current**: Clean up or upgrade to persistent storage

---

## Deployment Option 2: Docker

### Build Locally

```bash
# Build image
docker build -t hospital-api:latest .

# Run container
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e DATABASE_PATH=/app/data/hospital_pricing.db \
  -e DATA_DIR=/app/hospital_data \
  -v hospital_data:/app/data \
  hospital-api:latest
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f hospital-api

# Stop services
docker-compose down
```

### Push to Docker Hub

```bash
# Tag image
docker tag hospital-api:latest yourname/hospital-api:latest

# Login to Docker Hub
docker login

# Push
docker push yourname/hospital-api:latest
```

### Deploy to Other Platforms

Once image is on Docker Hub, deploy to:
- **AWS ECS**: Pull image from Hub, create task definition
- **Heroku**: Use Docker buildpack
- **DigitalOcean App Platform**: Connect Docker Hub
- **Fly.io**: `flyctl launch` → select Docker container
- **Railway**: Connect GitHub repo with Dockerfile

---

## Deployment Option 3: Traditional VPS

### Prerequisites

- VPS with Ubuntu 20.04+ (AWS, DigitalOcean, Linode, etc.)
- SSH access
- 2GB+ RAM, 20GB+ disk

### Setup

```bash
# 1. SSH into your server
ssh ubuntu@your-server-ip

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install Python and dependencies
sudo apt install -y python3.11 python3-pip git sqlite3

# 4. Clone repository
git clone https://github.com/yourname/hospital-api.git
cd hospital-api

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install Python packages
pip install -r requirements.txt

# 7. Run app
python app.py &
```

### Production Setup with Systemd

Create `/etc/systemd/system/hospital-api.service`:

```ini
[Unit]
Description=Hospital Pricing API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/hospital-api
Environment="PATH=/home/ubuntu/hospital-api/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/home/ubuntu/hospital-api/venv/bin/gunicorn app:app --bind 0.0.0.0:5000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable hospital-api
sudo systemctl start hospital-api
sudo systemctl status hospital-api
```

### Nginx Reverse Proxy

```bash
sudo apt install -y nginx

# Create config file
sudo nano /etc/nginx/sites-available/hospital-api
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/hospital-api /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Enable HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Post-Deployment Checklist

### Immediate

- [ ] Health check returns 200: `/health`
- [ ] Search endpoint works: `/api/search?query=cardiac`
- [ ] Comparison works: `/api/compare?procedure=92004`
- [ ] Stats show data loaded: `/api/stats`
- [ ] Hospitals list populated: `/api/hospitals`

### Security

- [ ] HTTPS enabled (Render provides free SSL)
- [ ] No sensitive data in logs
- [ ] Environment variables not hardcoded
- [ ] Restrict `/api/reload` endpoint (add API key if public)

### Monitoring

- [ ] Set up error alerts (Render/Sentry)
- [ ] Monitor response times
- [ ] Track database size growth
- [ ] Set up uptime monitoring (Healthchecks.io, etc.)

### Performance

- [ ] Database indexed (`sqlite3 hospital_pricing.db ".indices"`)
- [ ] Response times <200ms for search
- [ ] Comparison queries complete in <100ms
- [ ] Load test with multiple concurrent requests

### Backups

- [ ] Daily database backups (if using persistent storage)
- [ ] Monitor disk space usage
- [ ] Document data reload procedure

---

## Monitoring & Maintenance

### Check Deployment Status

**Render Dashboard:**
```
https://dashboard.render.com → Your Service → Events
```

**Logs:**
```bash
# View recent logs
curl https://your-service.onrender.com/api/stats
```

### Common Issues

#### High Memory Usage
```bash
# Restart service
# Render: Dashboard → More → Restart Instance

# Cause: Possible memory leak in data loading
# Solution: Limit concurrent connections or batch load
```

#### Slow Queries
```bash
# Check indexes exist
sqlite3 hospital_pricing.db ".indices"

# Rebuild index if missing
sqlite3 hospital_pricing.db "REINDEX;"
```

#### Database Locked
```bash
# Kill existing connections
sqlite3 hospital_pricing.db ".exit"

# Clear locks
rm -f hospital_pricing.db-journal
```

---

## Scaling

### Single Server (Current)

- ✅ Up to ~10 concurrent requests
- ✅ ~50K procedures
- ✅ <200ms response time
- ✅ Cost: $7-12/month

### Scale Up (Render)

Upgrade plan:
- Starter: $7/month → Standard: $12/month
- More CPU/RAM = more concurrent requests
- No code changes required

### Scale Out (Future)

- Add Redis cache for hot procedures
- Split into read/write database
- Use PostgreSQL for persistence
- Add CDN caching layer

---

## Disaster Recovery

### Backup Strategy

```bash
# Download database from Render
# (if using persistent volume)

# Or rebuild from sources
curl -X POST https://your-api.onrender.com/api/reload
```

### Restore Procedure

1. If database corrupted, delete `hospital_pricing.db`
2. Restart service (auto-recreates and reloads data)
3. Verify with `/api/stats`

---

## Conclusion

**Recommended path**: Deploy to Render using `render.yaml` (2 minutes, free to try).

For questions or issues:
1. Check service logs in Render dashboard
2. Test `/health` endpoint
3. Verify `/api/stats` shows data loaded
4. Run `test_api.py` locally to compare behavior

---

## Support Resources

- **Render Docs**: https://render.com/docs
- **Flask Docs**: https://flask.palletsprojects.com
- **SQLite Docs**: https://www.sqlite.org/docs.html
- **Gunicorn Docs**: https://gunicorn.org

**Status**: ✅ Production-ready. Deploy with confidence!

