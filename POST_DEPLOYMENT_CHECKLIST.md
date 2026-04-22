# Post-Deployment Verification Checklist

**After Render deployment completes (5-10 minutes), follow this checklist:**

---

## Step 1: Access the Website
- [ ] Open https://ohiohospital-pricing-app-1.onrender.com
- [ ] Page loads completely (no blank/spinning screen)
- [ ] Page loads in <2 seconds
- [ ] No 404 or 500 errors shown

---

## Step 2: Check Health Endpoint
```bash
curl https://ohiohospital-pricing-app-1.onrender.com/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "procedures_count": 65966
}
```

**Verification:**
- [ ] Returns HTTP 200
- [ ] Shows "healthy" status
- [ ] Shows "connected" database
- [ ] procedures_count shows 65,966 (or higher)

---

## Step 3: Check UI Elements

### Homepage
- [ ] Ohio map outline displays
- [ ] All buttons are visible and clickable
- [ ] Text content is readable

### Disclaimer Section
- [ ] Disclaimer is visible at top or bottom
- [ ] Close/accept button works
- [ ] Returns to normal view after dismissal

### Navigation Tabs
- [ ] All tabs are clickable
- [ ] Tab switching works smoothly
- [ ] Content updates when switching tabs

### Search/Filter
- [ ] Search box accepts input
- [ ] Hospital dropdown has options
- [ ] Category dropdown has options
- [ ] Search/filter buttons work

---

## Step 4: Test API Endpoints

### Get Hospitals List
```bash
curl https://ohiohospital-pricing-app-1.onrender.com/api/hospitals
```
- [ ] Returns HTTP 200
- [ ] Response includes hospital names
- [ ] Should show 23+ hospitals

### Get Procedures List
```bash
curl https://ohiohospital-pricing-app-1.onrender.com/api/procedures
```
- [ ] Returns HTTP 200
- [ ] Response includes procedure names with CPT codes
- [ ] Should show 65,966+ procedures

### Search Endpoint
```bash
curl "https://ohiohospital-pricing-app-1.onrender.com/api/search?q=surgery"
```
- [ ] Returns HTTP 200
- [ ] Response includes search results
- [ ] Results have hospital, procedure, and price data

### Search with Hospital Filter
```bash
curl "https://ohiohospital-pricing-app-1.onrender.com/api/search?hospital=hospital_name"
```
- [ ] Returns HTTP 200
- [ ] Results filtered by hospital
- [ ] Count matches filtered results

---

## Step 5: Verify Data

### Sample Search Results
1. Search for a common procedure (e.g., "room", "surgery", "lab")
2. Verify results show:
   - [ ] Hospital name
   - [ ] Procedure name
   - [ ] CPT code
   - [ ] Price in dollars

### Filter by Hospital
1. Select a hospital from dropdown
2. Verify:
   - [ ] Only that hospital's procedures appear
   - [ ] Prices are reasonable ($500-$100K range)
   - [ ] Multiple procedures available

### Filter by Category
1. Select a category (Room, Lab, Surgery, etc.)
2. Verify:
   - [ ] Only that category's procedures appear
   - [ ] Results are relevant to category
   - [ ] Count updates correctly

---

## Step 6: Performance Check

### Load Time Test
```bash
time curl -o /dev/null -s https://ohiohospital-pricing-app-1.onrender.com
```
- [ ] Total time <2 seconds
- [ ] No network timeouts
- [ ] Consistent performance on repeat

### API Response Time
```bash
time curl -o /dev/null -s https://ohiohospital-pricing-app-1.onrender.com/api/health
```
- [ ] <100ms response time
- [ ] No delays or hangs

---

## Step 7: Database Verification

### Check Database is Populated
```bash
curl "https://ohiohospital-pricing-app-1.onrender.com/api/search?q=hospital" | jq '.count'
```
- [ ] Returns number >0
- [ ] Indicates database has data

### Verify Record Count
Expected counts:
- [ ] Hospitals: 23
- [ ] Procedures: 65,966
- [ ] Pricing records: 185,287

---

## Step 8: Browser Console Check

Open browser Developer Tools (F12) → Console:
- [ ] No red error messages
- [ ] No CORS errors
- [ ] No 404 warnings for static files
- [ ] All network requests successful (green status)

---

## Step 9: Responsive Design

Test on different screen sizes:
- [ ] Desktop (1920x1080): All content visible and properly laid out
- [ ] Tablet (768x1024): Content adapts to tablet size
- [ ] Mobile (375x667): Content adapts to mobile size
- [ ] No horizontal scrolling needed

---

## Automated Verification Script

Run the verification script:
```bash
bash VERIFY_DEPLOYMENT.sh
```

Expected output:
```
[OK] Homepage loads
[OK] Health check passed
[OK] Search API works
[OK] Hospitals endpoint works
[OK] Procedures endpoint works

All tests passed!
Deployment is successful.
```

---

## Troubleshooting

### If Website Won't Load
1. Check Render dashboard for build/deploy errors
2. Wait 10 minutes - deployment may still be in progress
3. Clear browser cache: Ctrl+Shift+Delete
4. Try different browser

### If Health Endpoint Returns Error
1. Database may not be initialized yet
2. Wait 2 more minutes for build to complete
3. Check Render logs for Python errors
4. Verify procedures.json file exists in repository

### If API Returns 404
1. Endpoint may have moved
2. Check /api/health first to verify API is running
3. Test endpoints one at a time
4. Check app.py for endpoint definitions

### If Performance is Slow
1. Render instance may be under load
2. Database indices may not have been created
3. Try again in 5 minutes
4. Check Render metrics dashboard

### If Data Looks Incomplete
1. Database initialization may still be running
2. Check Render build logs for completion status
3. Wait until build shows "Success"
4. Refresh page and try again

---

## Success Indicators

✅ **All of the following should be true:**

1. Website loads in <2 seconds
2. Health endpoint returns "healthy" status
3. Database connected with 65,966+ procedures
4. All API endpoints respond with data
5. Search and filtering work correctly
6. Ohio map displays properly
7. Disclaimer visible and functional
8. No errors in browser console
9. Mobile/tablet responsive
10. Automated verification script passes

---

## Next Steps

If all checks pass:
1. ✅ Deployment successful
2. ✅ Website is ready for production
3. ✅ Users can search hospital pricing

If issues found:
1. Check Render logs: Dashboard → Logs
2. Review troubleshooting section above
3. Check GitHub commits for recent changes
4. Consider rolling back if needed

---

## Contact Information

For deployment issues:
- Check Render dashboard logs
- Review error messages in browser console
- Check GitHub commit history
- Reference: SUBAGENT_DEPLOYMENT_COMPLETE.md

---

**Estimated Completion:** 5-10 minutes after deployment starts  
**Expected:** All checks should pass ✅

