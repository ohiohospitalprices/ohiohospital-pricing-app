# ⚡ QUICK DEPLOY TO RENDER (5 MINUTES)

Your code is already on GitHub. Now just connect Render.

## Step-by-Step

### 1. Go to Render Dashboard
```
https://dashboard.render.com
```
(Sign up free with GitHub if needed)

### 2. Create Web Service
- Click **"New +"** at top
- Choose **"Web Service"**
- Click **"Connect a repository"**

### 3. Select Your Repo
- Choose GitHub → `ohiohospital-pricing-app`
- Click **"Connect"**

### 4. Configure (Copy/Paste These)
| Field | Value |
|-------|-------|
| **Name** | `ohiohealth-pricing` |
| **Environment** | `Node` |
| **Region** | `Ohio` (or closest) |
| **Build Command** | `npm install` |
| **Start Command** | `npm start` |
| **Plan** | **Free** (sufficient) |

### 5. Create & Deploy
- Click **"Create Web Service"**
- Render builds automatically (~2 min)
- You'll get a URL like: `https://ohiohealth-pricing.onrender.com`

### 6. Test
Go to your new URL and verify:
- ✅ Hospitals appear in dropdown
- ✅ Categories work (Surgical, Imaging, etc.)
- ✅ Search filters procedures
- ✅ Prices show up

---

## Already on GitHub

Your repo is here and ready:
```
https://github.com/ohiohospitalprices/ohiohospital-pricing-app
```

Render will automatically pull from `master` branch.

---

## Troubleshooting

**Can't find the repo?**
- Make sure you're logged into GitHub when connecting Render
- Repo needs to be public (it is)

**Build fails?**
- Check Render logs (in dashboard)
- Usually it's just waiting for Node to install dependencies

**Won't load?**
- Give it 30 seconds after "build complete"
- Check browser console for errors
- Render free tier may sleep after 15 min inactive

---

## Done!

Once Render shows green checkmark, your app is **LIVE**.

Share the URL with hospital staff. They can now search pricing anytime.

---

*Code deployed at 10:09 AM EST. Deadline 10:30 AM EST. You've got this!* ✨
