# Render.com Deployment Checklist

## Pre-Deployment Checks

### 1. Environment Variables (CRITICAL!)

Before deploying, you MUST set these environment variables in Render.com dashboard:

#### Required Variables:
- `BOT_TOKEN` - Your Telegram bot token from @BotFather
- `DATABASE_URL` - PostgreSQL connection string (already set: `postgresql://areno:...@dpg-...render.com/microservices_wo39`)
- `RAILWAY_URL` - Your Render.com app URL (format: `https://dealbot.onrender.com`)

#### Optional but Recommended:
- `ENVIRONMENT` - Set to `production`
- `DEBUG` - Set to `false`
- `LOG_LEVEL` - Set to `INFO`
- `SECRET_KEY` - Random secret for Flask sessions (generate one if not set)

### 2. Verify .env Files Are NOT in Git

Run this command to check:
```cmd
git status
```

Make sure these files show as "untracked" or don't appear:
- `.env`
- `.env.*`
- `webapp/.env`
- `webapp/.env.*`

If they appear as "modified" or "new file", they might be committed! Remove them:
```cmd
git rm --cached .env
git rm --cached webapp/.env
git rm --cached webapp/.env.*
```

### 3. Database Schema

Your database schema should already be initialized since you're using the cloud database. Verify:
- Tables exist (run `/health` endpoint after deployment to check)
- No pending migrations

### 4. Build Configuration

Check `render.yaml`:
- Build command: `pip install -r requirements.txt && cd webapp && npm install && npm run build`
- Start command: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --log-level info`

### 5. Webapp Build Test (IMPORTANT!)

Before deploying, test that the webapp builds successfully locally:

```cmd
cd webapp
npm run build
```

This should create a `webapp/dist` folder with your built files. If this fails, fix it before deploying!

### 6. Security Checks

- [x] CORS is configured (app.py line 117)
- [x] .env files in .gitignore
- [x] No hardcoded secrets in code
- [x] Database credentials in environment variables only

### 7. Telegram Webhook Configuration

After deployment, your bot will automatically set the webhook to:
`https://dealbot.onrender.com/YOUR_BOT_TOKEN`

Verify webhook is set by calling Telegram API:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

## Deployment Steps

### Option 1: Deploy via Render Dashboard (Recommended)

1. Go to https://dashboard.render.com
2. Find your service "dealbot-webapp"
3. Click "Manual Deploy" → "Deploy latest commit"
4. Wait for build to complete (5-10 minutes)
5. Check logs for errors

### Option 2: Deploy via Git Push

1. Commit your changes:
```cmd
git add .
git commit -m "Deploy to production"
git push origin main
```

2. Render will automatically detect the push and deploy

## Post-Deployment Verification

### 1. Check Health Endpoints

```cmd
curl https://dealbot.onrender.com/
curl https://dealbot.onrender.com/health
```

Expected responses:
- `/` - `{"status": "healthy", "message": "Bot online"}`
- `/health` - Detailed health status with all services

### 2. Check Webapp

Visit: `https://dealbot.onrender.com/webapp/`

Should load the Telegram Mini App interface.

### 3. Test Telegram Bot

Send a message to your bot on Telegram. It should respond.

### 4. Check Logs

In Render dashboard, click "Logs" tab to see:
- Application startup logs
- Database connections
- Webhook registration
- Any errors

### 5. Test API Endpoints

```cmd
curl https://dealbot.onrender.com/api/expeditions
```

Should return expedition data (or empty array if none exist).

## Common Issues & Solutions

### Issue: Build fails with "npm: command not found"

**Solution:** Render uses Python buildpack by default. The `render.yaml` should handle this. Check that `buildCommand` includes `npm install`.

### Issue: Webapp shows 404

**Solution:**
- Check that `webapp/dist` folder was created during build
- Verify build logs show "npm run build" completed successfully
- Check app.py routes are serving from correct path

### Issue: Database connection fails

**Solution:**
- Verify `DATABASE_URL` environment variable is set in Render dashboard
- Check database is not paused (free tier databases pause after inactivity)
- Check database accepts connections from Render servers

### Issue: Bot doesn't respond to messages

**Solution:**
- Check webhook is set: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Check logs for webhook errors
- Verify `BOT_TOKEN` is correct
- Verify `RAILWAY_URL` is set to your Render app URL

### Issue: CORS errors in browser

**Solution:**
- Already configured in app.py (line 117)
- Check browser console for specific CORS error
- May need to adjust allowed origins in production

## Environment Variable Setup on Render

1. Go to your service on Render dashboard
2. Click "Environment" tab
3. Add these variables:

```
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://areno:iaITMVkeyDjbs2RwkaHMJhaKxSde6ZAp@dpg-d3089fvdiees73eqk9o0-a.oregon-postgres.render.com/microservices_wo39
RAILWAY_URL=https://dealbot.onrender.com
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

4. Click "Save Changes"
5. Service will automatically redeploy

## Rollback Plan

If deployment fails:

1. In Render dashboard, go to "Events" tab
2. Find the last successful deployment
3. Click "Redeploy" on that commit
4. Or revert git commits and push:
```cmd
git revert HEAD
git push origin main
```

## Important Notes

- **Free tier limitation:** Render free services sleep after 15 minutes of inactivity. First request after sleep takes 30-60 seconds.
- **Build time:** Expect 5-10 minutes for full build (Python + Node.js)
- **Database:** Make sure database is on a paid plan if you need 24/7 availability
- **Logs:** Keep an eye on logs for the first few hours after deployment

## Ready to Deploy?

Run through this checklist:
- [ ] Environment variables set on Render
- [ ] .env files NOT in git
- [ ] `npm run build` works locally
- [ ] Database is accessible
- [ ] BOT_TOKEN is correct
- [ ] RAILWAY_URL points to your Render app
- [ ] Committed all code changes
- [ ] Reviewed recent changes for any hardcoded secrets

If all checked, you're ready to deploy!
