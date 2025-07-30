import os
import logging
import nest_asyncio
from flask import Flask, request
from telegram import Update

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Initialize database connection manager
from database import initialize_database, get_db_manager
from core.bot_manager import BotManager
from core.handler_registry import configure_handlers

# === CONFIGURAÇÃO ===
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
RAILWAY_URL = os.getenv("RAILWAY_URL")
if not RAILWAY_URL:
    raise ValueError("RAILWAY_URL environment variable is required")
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RAILWAY_URL}{WEBHOOK_PATH}"

# === FLASK INIT ===
app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
nest_asyncio.apply()

# === DATABASE INIT ===
try:
    initialize_database()
    logger.info("✅ Database connection pool initialized")
    
    # Initialize database tables
    from services import produto_service_pg
    produto_service_pg.init_db()
    logger.info("✅ Database tables initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize database: {e}")
    raise

# === BOT MANAGER INIT ===
bot_manager = BotManager(TOKEN, WEBHOOK_URL)
bot_manager.set_handler_configurator(configure_handlers)

# === FLASK LIFECYCLE ===
@app.before_first_request
def activate_bot():
    """Initialize bot on first Flask request."""
    if not hasattr(app, "bot_started"):
        app.bot_started = True
        bot_manager.start_worker()
        logger.info("✅ Bot activation completed")

# === FLASK ROUTES ===
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    """Handle incoming telegram webhooks."""
    try:
        if not bot_manager.is_ready:
            logger.warning("⚠️ Bot not ready, rejecting webhook")
            return "BOT NOT READY", 503

        # Parse telegram update
        update_data = request.get_json(force=True)
        if not update_data:
            return "NO DATA", 400
            
        update = Update.de_json(update_data, bot_manager.app_bot.bot)
        
        # Queue update for processing
        if bot_manager.queue_update(update):
            return "OK", 200
        else:
            return "QUEUE FULL", 503
            
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return "ERROR", 500

@app.route("/")
def health():
    """Simple health check."""
    return "✅ Bot online (health check)", 200

@app.route("/health")
def health_detailed():
    """Detailed health check with full system status."""
    try:
        # Database health
        db_manager = get_db_manager()
        db_healthy = db_manager.health_check()
        pool_status = db_manager.get_pool_status()
        
        # Bot health
        bot_status = bot_manager.get_health_status()
        
        # Overall status
        overall_healthy = db_healthy and bot_status["bot_ready"]
        
        status = {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": "2025-01-30T00:00:00Z",  # You could use datetime.utcnow().isoformat()
            "database": {
                "healthy": db_healthy,
                "pool": pool_status
            },
            "bot": bot_status,
            "version": os.getenv("RENDER_GIT_COMMIT", "unknown")[:8] if os.getenv("RENDER_GIT_COMMIT") else "local"
        }
        
        return status, 200 if overall_healthy else 503
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": "2025-01-30T00:00:00Z"
        }, 503

def cleanup_on_exit():
    """Clean shutdown for both bot and database."""
    logger.info("🔄 Performing cleanup on exit...")
    
    try:
        # Shutdown bot manager
        import asyncio
        if bot_manager.app_bot:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_manager.shutdown())
    except Exception as e:
        logger.error(f"❌ Bot shutdown error: {e}")
    
    try:
        # Close database connections
        from database import close_database
        close_database()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Database shutdown error: {e}")


if __name__ == "__main__":
    import atexit
    import signal
    
    # Register cleanup functions
    atexit.register(cleanup_on_exit)
    
    # Handle termination signals (important for Render)
    def signal_handler(signum, frame):
        logger.info(f"🔄 Received signal {signum}, shutting down gracefully...")
        cleanup_on_exit()
        exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"🚀 Starting Flask app on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
        
    except KeyboardInterrupt:
        logger.info("🔄 Keyboard interrupt received")
        cleanup_on_exit()
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
        cleanup_on_exit()
        raise