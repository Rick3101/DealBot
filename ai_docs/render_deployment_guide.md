# Render Deployment Guide

## Overview

This guide explains how to deploy the Telegram Bot with Mini App (webapp) to Render using production-ready configuration.

## What Was Fixed

### Problem
The application was trying to use Flask-SocketIO's development server (`socketio.run()`) in production, which caused this error:
```
RuntimeError: The Werkzeug web server is not designed to run in production.
```

### Solution
We implemented a production-ready setup using:
- **Gunicorn**: Production WSGI server
- **Eventlet**: Async worker for WebSocket support (required by Flask-SocketIO)
- **WSGI Entry Point**: Separate `wsgi.py` file for clean production initialization

## Architecture

```
Render → Gunicorn (eventlet workers) → Flask App + SocketIO → Telegram Bot + WebApp
                                                            ↓
                                                      PostgreSQL Database
```

## Files Changed

### 1. `requirements.txt`
Added production dependencies:
```
gunicorn==21.2.0
eventlet==0.33.3
```

### 2. `render.yaml`
Updated configuration:
```yaml
services:
  - type: web
    name: dealbot-webapp
    runtime: python
    buildCommand: |
      pip install -r requirements.txt
      cd webapp && npm install && npm run build
    startCommand: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120
```

### 3. `wsgi.py` (NEW)
Production entry point that:
- Initializes the BotApplication
- Sets up all services (database, handlers, routes)
- Exposes the Flask app to gunicorn
- Handles proper logging and error reporting

## Deployment Steps

### 1. Prerequisites
- Render account
- PostgreSQL database (can be created on Render)
- Telegram Bot Token
- GitHub repository connected to Render

### 2. Environment Variables
Set these in Render dashboard:

**Required:**
- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `DATABASE_URL`: PostgreSQL connection string (auto-set if using Render PostgreSQL)
- `RAILWAY_URL`: Your app's URL (e.g., `https://your-app.onrender.com`)

**Optional (auto-configured):**
- `ENVIRONMENT`: Set to `production` (auto-set in render.yaml)
- `PORT`: Automatically set by Render
- `PYTHON_VERSION`: Set to `3.10.0` (auto-set in render.yaml)

### 3. Deploy

#### Option A: Automatic (Blueprint)
1. Push code to GitHub
2. In Render dashboard, click "New" → "Blueprint"
3. Connect your repository
4. Render will detect `render.yaml` and configure automatically
5. Set environment variables
6. Deploy!

#### Option B: Manual
1. In Render dashboard, click "New" → "Web Service"
2. Connect your repository
3. Configure:
   - **Name**: dealbot-webapp (or your choice)
   - **Runtime**: Python
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && cd webapp && npm install && npm run build
     ```
   - **Start Command**:
     ```bash
     gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --log-level info
     ```
4. Set environment variables
5. Deploy!

### 4. Post-Deployment

After deployment:

1. **Check Logs**: Monitor the deployment logs for any errors
2. **Verify Health**: Visit `https://your-app.onrender.com/health`
3. **Test Bot**: Send `/start` to your Telegram bot
4. **Test WebApp**: Visit `https://your-app.onrender.com/webapp`

## Access Points

Once deployed, your application will be available at:

- **Main App Health**: `https://your-app.onrender.com/`
- **Detailed Health**: `https://your-app.onrender.com/health`
- **WebApp (Mini App)**: `https://your-app.onrender.com/webapp`
- **API Endpoints**: `https://your-app.onrender.com/api/*`
- **Telegram Webhook**: `https://your-app.onrender.com/webhook`
- **WebSocket**: `wss://your-app.onrender.com/socket.io/`

## Production Configuration

### Gunicorn Settings Explained

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app --timeout 120 --log-level info
```

- `--worker-class eventlet`: Required for SocketIO WebSocket support
- `-w 1`: Single worker (important for SocketIO to maintain connections)
- `--bind 0.0.0.0:$PORT`: Bind to all interfaces on Render's PORT
- `--timeout 120`: 2-minute timeout for long-running requests
- `--log-level info`: Production logging level
- `wsgi:app`: Use the `app` object from `wsgi.py`

### Why Single Worker?

Flask-SocketIO requires a single worker or special configuration for multiple workers. For simplicity and to ensure WebSocket connections work correctly, we use 1 worker. For higher traffic, consider:
- Using Redis for session sharing across workers
- Implementing proper message queue (like Redis or RabbitMQ)

## Monitoring

### Health Checks

The app provides multiple health endpoints:

1. **Basic Health** (`/`):
   ```json
   {"status": "healthy", "timestamp": "..."}
   ```

2. **Detailed Health** (`/health`):
   ```json
   {
     "status": "healthy",
     "services": {
       "database": "healthy",
       "bot": "healthy",
       "socketio": "healthy"
     },
     "uptime": "...",
     "version": "..."
   }
   ```

3. **Service Diagnostics** (`/services`):
   Shows detailed service container status

### Logs

Monitor logs in Render dashboard:
- Application startup
- Request handling
- Database queries
- Bot updates
- WebSocket connections
- Error traces

## Troubleshooting

### Common Issues

#### 1. App Crashes on Startup
**Symptom**: Immediate crash after deployment
**Solution**:
- Check environment variables are set correctly
- Verify DATABASE_URL is valid
- Check logs for specific error messages

#### 2. Bot Not Responding
**Symptom**: Telegram bot doesn't respond to messages
**Solution**:
- Verify BOT_TOKEN is correct
- Check RAILWAY_URL matches your Render URL
- Ensure webhook is set correctly (check logs for webhook setup)

#### 3. WebApp Not Loading
**Symptom**: 404 or blank page at `/webapp`
**Solution**:
- Verify build command ran successfully
- Check if `webapp/dist` folder was created during build
- Review build logs for npm errors

#### 4. WebSocket Connection Failed
**Symptom**: Real-time updates not working
**Solution**:
- Verify eventlet is installed
- Check gunicorn is using `--worker-class eventlet`
- Ensure only 1 worker is running

#### 5. Database Connection Errors
**Symptom**: Database query failures
**Solution**:
- Verify DATABASE_URL format
- Check PostgreSQL service is running
- Review connection pool settings in logs

### Debug Commands

From Render shell (if needed):

```bash
# Check Python version
python --version

# Verify dependencies
pip list | grep -E "gunicorn|eventlet|flask"

# Test database connection
python -c "from database import get_connection; print(get_connection())"

# Check webapp build
ls -la webapp/dist/

# Test app import
python -c "from wsgi import app; print(app)"
```

## Rollback

If deployment fails:

1. In Render dashboard, go to your service
2. Click on "Events" tab
3. Find the last successful deployment
4. Click "Redeploy" next to that version

## Scaling Considerations

### Current Setup (Free Tier)
- 1 Gunicorn worker with eventlet
- Suitable for: Low-to-medium traffic (hundreds of users)
- Limitations: Single server, auto-sleeps after inactivity

### To Scale Up
1. **Upgrade Render Plan**: Move to paid tier for:
   - No sleep mode
   - More RAM/CPU
   - Better performance

2. **Multiple Workers** (requires changes):
   - Implement Redis for session sharing
   - Configure Flask-SocketIO with Redis message queue
   - Update gunicorn to use more workers

3. **Database Optimization**:
   - Connection pooling (already configured)
   - Query optimization
   - Indexes (already configured)

4. **Caching Layer**:
   - Add Redis for caching
   - Cache frequent queries
   - Session storage

## Security Checklist

- [x] Environment variables not committed to git
- [x] Production mode enabled (ENVIRONMENT=production)
- [x] Debug mode disabled
- [x] HTTPS enforced by Render
- [x] Database connection encrypted (PostgreSQL SSL)
- [x] Input validation and sanitization
- [x] Permission system for bot commands
- [x] Webhook authentication (Telegram validates)

## Maintenance

### Regular Tasks

1. **Monitor Logs**: Check for errors daily
2. **Database Backups**: Configure automatic backups in Render
3. **Dependency Updates**: Review and update monthly
4. **Health Checks**: Set up external monitoring (UptimeRobot, etc.)

### Updates

To deploy updates:

1. Push changes to GitHub
2. Render auto-deploys (if enabled)
3. Monitor deployment logs
4. Test critical functionality
5. Rollback if issues occur

## Support

For issues:
- Check logs in Render dashboard
- Review this guide's troubleshooting section
- Check Flask-SocketIO documentation
- Review Gunicorn documentation
- Open issue in project repository

## Additional Resources

- [Render Python Documentation](https://render.com/docs/deploy-flask)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [Eventlet Documentation](https://eventlet.net/)

---

**Last Updated**: 2025-10-26
**Version**: 1.0
