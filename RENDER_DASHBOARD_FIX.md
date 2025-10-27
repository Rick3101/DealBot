# URGENT: Fix Render Dashboard Configuration

## The Problem

Your Procfile is correct in GitHub, but Render's dashboard has a **manual override** for the Start Command that's running `python app.py` instead of using the Procfile.

## How to Fix (5 minutes)

### Step 1: Go to Render Dashboard

1. Open https://dashboard.render.com
2. Click on your service (dealbot-webapp or similar name)

### Step 2: Go to Settings

1. Click the **Settings** tab in the left sidebar
2. Scroll down to the **Build & Deploy** section

### Step 3: Check Start Command

Look for a field called **Start Command**.

**If it shows:**
```
python app.py
```

**Change it to BLANK (empty) or:**
```
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --log-level info
```

### Step 4: Save Changes

1. Click **Save Changes** at the bottom
2. Render will ask if you want to redeploy - click **Yes, Deploy**

## Why This Happens

Render has two ways to set the start command:

1. **Procfile** (in your code) ← Should use this
2. **Dashboard override** (manual setting) ← Currently using this (wrong)

The dashboard override takes precedence over Procfile.

## Alternative: Delete and Recreate Service

If the above doesn't work:

### Option A: Use render.yaml Blueprint

1. In Render dashboard, click **New +**
2. Select **Blueprint**
3. Connect your GitHub repository
4. Render will detect `render.yaml` and configure automatically
5. Set environment variables:
   - `BOT_TOKEN`
   - `DATABASE_URL`
   - `RAILWAY_URL`

### Option B: Manual Web Service

1. Delete current service (or create new one)
2. Click **New +** → **Web Service**
3. Connect GitHub repository
4. **IMPORTANT:** Leave **Start Command** BLANK
5. Configure:
   - **Name**: dealbot-webapp
   - **Runtime**: Python
   - **Build Command**:
     ```
     pip install -r requirements.txt && cd webapp && npm install && npm run build
     ```
   - **Start Command**: **LEAVE BLANK** (will use Procfile)
6. Set environment variables
7. Deploy

## Verify the Fix

After redeploying, check the logs. You should see:

### ✅ CORRECT Logs:
```
==> Starting service with 'gunicorn --worker-class eventlet...'
[2025-10-26 23:00:00] [1] [INFO] Starting gunicorn 21.2.0
[2025-10-26 23:00:00] [1] [INFO] Listening at: http://0.0.0.0:10000
[2025-10-26 23:00:00] [1] [INFO] Using worker: eventlet
Initializing BotApplication for production...
Services initialized successfully
Flask app created successfully
Bot initialized successfully
Application ready for production deployment
```

### ❌ WRONG Logs (what you're seeing now):
```
Traceback (most recent call last):
  File "/app/app.py", line 2831, in run
    self.socketio.run(
RuntimeError: The Werkzeug web server is not designed to run in production
```

## Quick Checklist

- [ ] Go to Render dashboard
- [ ] Open your service settings
- [ ] Find "Start Command" field
- [ ] Clear it (leave blank) OR set to gunicorn command
- [ ] Save changes
- [ ] Redeploy
- [ ] Check logs for "Starting gunicorn"
- [ ] Verify app works at /webapp and /health

## Screenshot Guide

### Where to Find Settings:

```
Render Dashboard
└── Your Service (dealbot-webapp)
    └── Settings (left sidebar)
        └── Build & Deploy section
            └── Start Command ← FIX THIS FIELD
```

### What It Should Look Like:

**Before (WRONG):**
```
Start Command: python app.py
```

**After (CORRECT):**
```
Start Command: [blank/empty]
```
or
```
Start Command: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --log-level info
```

## If You Need Help

The issue is NOT in your code. Your code is correct:
- ✅ Procfile has correct command
- ✅ wsgi.py exists and is correct
- ✅ requirements.txt has gunicorn
- ✅ All files are committed and pushed

The issue is ONLY in Render's dashboard configuration.

## Still Having Issues?

If after clearing the Start Command you still see the error:

1. **Check Build Command** in dashboard - should be:
   ```
   pip install -r requirements.txt && cd webapp && npm install && npm run build
   ```

2. **Check Environment** - Make sure these are set:
   - `BOT_TOKEN`
   - `DATABASE_URL`
   - `RAILWAY_URL` (should be your Render URL)

3. **Force Rebuild**:
   - In Render dashboard, go to **Manual Deploy**
   - Click **Clear build cache & deploy**

4. **Check Render is using correct branch**:
   - Settings → Branch: should be `main`

## Contact Info

If this still doesn't work, the issue might be:
- Render caching old configuration
- Service needs to be recreated
- Region-specific Render issue

---

**Last Updated**: 2025-10-26
**Status**: URGENT FIX NEEDED
**Action Required**: Update Render Dashboard Settings
