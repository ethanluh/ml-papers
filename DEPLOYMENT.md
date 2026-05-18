# Deployment Guide for Render.com & Railway

Your app is now configured to work on both Render.com and Railway, which support long-running Python services, persistent databases, and background workers.

## Key Changes Made

✅ **Removed Vercel.json** - Vercel serverless isn't suitable for this architecture  
✅ **Added render.yaml** - Render.com configuration with web service + scheduler  
✅ **Added railway.json** - Railway configuration for auto-detection  
✅ **Added Procfile** - Process definition for both platforms  
✅ **Updated db.py** - Uses persistent `/var/data` storage path  
✅ **Improved api/main.py** - Better error handling and logging  
✅ **Enhanced scheduler.py** - More robust with error recovery  

## Deploying to Render.com (Recommended)

### Step 1: Connect Your Repository
1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`

### Step 2: Configure Environment Variables
In the Render dashboard for your service:
- Add `GROQ_API_KEY` with your API key value
- The `render.yaml` will set `DATABASE_PATH` automatically

### Step 3: Deploy
1. Click "Create Blueprint"
2. Render will automatically:
   - Create a web service (FastAPI on dynamic port)
   - Create a background worker (scheduler.py)
   - Create persistent disk storage at `/var/data`
   - Run `pip install -r requirements.txt`

### Verification
- **Web Service**: Check logs at `https://dashboard.render.com` → Logs tab
- **Scheduler**: Should start logging at 06:00 UTC each day
- **Database**: Persisted to `/var/data/papers.db`

---

## Deploying to Railway

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Connect Repository
```bash
railway login
railway init
```

### Step 3: Configure Variables
In your Railway dashboard or via CLI:
```bash
railway variables set GROQ_API_KEY=your_key_here
```

### Step 4: Deploy
```bash
railway up
```

Railway will:
- Detect Python via `requirements.txt`
- Use start command from `railway.json`
- Build and deploy automatically
- Persist data to `/var/data`

---

## Troubleshooting

### "FUNCTION_INVOCATION_FAILED" on Render/Railway?
✅ **Fixed!** The error occurred because:
- Vercel's serverless functions have a 60-second timeout
- Your app needs persistent database connections
- Scheduler running in the background isn't supported on Vercel

Render.com and Railway support all of this natively.

### Database Not Found?
Ensure `DATABASE_PATH` environment variable is set to `/var/data`:
```bash
# Render.yaml handles this automatically
# Railway: set via dashboard
railway variables set DATABASE_PATH=/var/data
```

### Scheduler Not Running?
Check the background worker logs:
- **Render**: Dashboard → "arxiv-scheduler" service → Logs
- **Railway**: `railway logs --service arxiv-scheduler`

Expected output: `Scheduler started. Will run daily at 06:00 UTC.`

---

## Architecture Comparison

| Feature | Vercel | Render.com | Railway |
|---------|--------|-----------|---------|
| **Python Support** | ✅ Serverless only | ✅ Long-running | ✅ Long-running |
| **Background Tasks** | ❌ No | ✅ Yes | ✅ Via Cron |
| **Persistent DB** | ❌ Cold storage | ✅ Disk storage | ✅ (via DB service) |
| **Database Scheduler** | ❌ Won't work | ✅ YEs | ✅ Yes |
| **Request Timeout** | 60s | 30m (default) | 30m |
| **Free Tier** | ✅ Generous | ✅ $7/month | ✅ $5/month |

---

## Local Development

Nothing has changed for local development:
```bash
# Terminal 1: Run the FastAPI server
uvicorn api.main:app --reload --port 8000

# Terminal 2: Run the scheduler
python pipeline/scheduler.py
```

Environment variables are read from `.env` by default.

---

## Final Checklist

Before deploying:
- [ ] Push code to GitHub
- [ ] `.env` file contains valid `GROQ_API_KEY`
- [ ] `requirements.txt` is up-to-date
- [ ] `render.yaml` or `railway.json` is committed
- [ ] `Procfile` is committed

Then:
1. Choose Render.com (easier) or Railway
2. Connect GitHub repository
3. Set `GROQ_API_KEY` environment variable
4. Watch logs during deployment
5. Verify API is responding: `GET /api/stats`
6. Verify scheduler starts: check logs at 06:00 UTC

---

## Questions?

- **Render.com docs**: https://render.com/docs
- **Railway docs**: https://docs.railway.app
- **FastAPI on Render**: https://render.com/docs/deploy-fastapi
