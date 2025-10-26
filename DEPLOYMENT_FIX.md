# Deployment Fix - Quick Guide

## What Was Fixed

The application was trying to run with the development server (`python app.py`) instead of the production server (gunicorn).

## Files Changed

### 1. [Procfile](Procfile) - CRITICAL FIX
**OLD:**
```
web: python app.py
```

**NEW:**
```
web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --log-level info
```

### 2. [requirements.txt](requirements.txt) - Added production dependencies
```
gunicorn==21.2.0
eventlet==0.33.3
```

### 3. [wsgi.py](wsgi.py) - NEW FILE
Production entry point that:
- Initializes BotApplication
- Sets up services
- Creates Flask app with routes
- Initializes Telegram bot
- Exposes app to gunicorn

### 4. [render.yaml](render.yaml) - Updated (optional, Procfile takes precedence)
Updated with correct build and start commands.

## How to Deploy

### Option 1: Push to GitHub (Recommended)

```bash
git add Procfile requirements.txt wsgi.py render.yaml
git commit -m "Fix production deployment with gunicorn"
git push
```

Render will automatically detect the changes and redeploy.

### Option 2: Manual Redeploy in Render Dashboard

1. Go to your Render service
2. Click "Manual Deploy" → "Deploy latest commit"
3. Wait for build to complete

## Verify Deployment

Once deployed, check:

1. **Logs** - Should see:
   ```
   Initializing BotApplication for production...
   Services initialized successfully
   Flask app created successfully
   Bot initialized successfully
   Application ready for production deployment
   ```

2. **Health Check** - Visit:
   ```
   https://your-app.onrender.com/health
   ```

3. **WebApp** - Visit:
   ```
   https://your-app.onrender.com/webapp
   ```

4. **Bot** - Send `/start` to your Telegram bot

## What Changed Technically

### Before (Wrong):
```
Render → python app.py → Flask dev server → CRASH
```

### After (Correct):
```
Render → Procfile → gunicorn → wsgi.py → Flask app → SUCCESS
```

## Gunicorn Command Explained

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --log-level info
```

- `--worker-class eventlet` - Async worker for WebSocket support (Flask-SocketIO requirement)
- `-w 1` - Single worker (required for SocketIO without Redis)
- `--bind 0.0.0.0:$PORT` - Bind to all interfaces on Render's dynamic port
- `wsgi:app` - Load the `app` object from `wsgi.py`
- `--timeout 120` - 2 minute timeout for long requests
- `--log-level info` - Production logging

## Troubleshooting

### If deployment still fails:

1. **Check Render Logs** - Look for the exact error message
2. **Verify Environment Variables** are set:
   - `BOT_TOKEN`
   - `DATABASE_URL`
   - `RAILWAY_URL`
3. **Check Build Logs** - Ensure all dependencies installed
4. **Verify Procfile** - Make sure it matches the NEW content above

### Common Issues:

**"Module not found: wsgi"**
- Make sure `wsgi.py` is committed to git
- Check file is in root directory

**"gunicorn: command not found"**
- Make sure `requirements.txt` has `gunicorn==21.2.0`
- Check build logs to see if installation failed

**"No module named 'eventlet'"**
- Make sure `requirements.txt` has `eventlet==0.33.3`
- Check build logs

**Bot not responding**
- Verify `RAILWAY_URL` matches your Render URL
- Check webhook is set correctly in logs
- Verify `BOT_TOKEN` is correct

## Success Indicators

You'll know it's working when:

1. ✅ No "Werkzeug web server" error in logs
2. ✅ Logs show "Application ready for production deployment"
3. ✅ `/health` endpoint returns healthy status
4. ✅ `/webapp` loads the Mini App
5. ✅ Bot responds to `/start` on Telegram

---

**Last Updated**: 2025-10-26
**Issue**: Production server configuration
**Status**: FIXED - Ready to deploy
