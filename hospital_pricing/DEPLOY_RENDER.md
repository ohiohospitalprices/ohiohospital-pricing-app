# Deploy to Render.com (Step-by-Step)

## Prerequisites

- GitHub account
- Render.com account (free)
- This repository pushed to GitHub

## Step 1: Push to GitHub

```bash
cd hospital_pricing
git init
git add .
git commit -m "Initial commit: OhioHealth pricing website"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ohiohealth-pricing.git
git push -u origin main
```

## Step 2: Deploy on Render

1. **Login to Render.com** → https://dashboard.render.com

2. **Click "New +"** → Select **Web Service**

3. **Connect Repository:**
   - Click "Connect a repository"
   - Select GitHub
   - Find and select `ohiohealth-pricing`
   - Click "Connect"

4. **Configure Service:**
   - **Name:** `ohiohealth-pricing`
   - **Environment:** `Node`
   - **Build Command:** `npm install`
   - **Start Command:** `npm start`
   - **Plan:** Free (sufficient for this use)

5. **Click "Create Web Service"**

Render will automatically:
- Build your app
- Install dependencies
- Start the server
- Assign a public URL

## Step 3: Access Your App

After deployment completes (~2-3 minutes), your app will be live at:

```
https://ohiohealth-pricing.onrender.com
```

(Exact URL shown in Render dashboard)

## Testing the Deployed App

1. ✅ Load the homepage
2. ✅ Select different hospitals from dropdown
3. ✅ Click category buttons (Surgical, Imaging, etc.)
4. ✅ Search for procedures by name or CPT code
5. ✅ Click a procedure to see prices at all hospitals

## Updates

To update procedures or code:

1. Make changes locally
2. `git commit` and `git push` to GitHub
3. Render auto-redeploys on push (or manually trigger via dashboard)

## Troubleshooting

**App won't start?**
- Check logs in Render dashboard
- Verify `package.json` and `server.js` are correct
- Ensure `procedures.json` is in the root directory

**Procedures not loading?**
- Confirm `procedures.json` is committed to GitHub
- Check browser console for fetch errors
- Verify JSON syntax is valid

**Port issues?**
- Render assigns PORT via environment variable
- `server.js` already handles this: `process.env.PORT || 3000`

## Cost

- **Free tier:** Sufficient for this app
  - 750 hours/month (always-on)
  - No custom domain needed
  - Auto-pause if no traffic (still free)

---

Your OhioHealth pricing tool is now live! 🎉
