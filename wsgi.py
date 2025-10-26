"""
WSGI entry point for production deployment.
This file is used by gunicorn to run the Flask application.
"""

import os
import sys
import logging

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

try:
    # Import the main application
    from app import BotApplication

    logger.info("Initializing BotApplication for production...")

    # Create the application instance
    bot_application = BotApplication()

    # Initialize services (database, service container, etc.)
    bot_application.initialize_services()
    logger.info("Services initialized successfully")

    # Create Flask app (this also configures routes and SocketIO)
    app = bot_application.create_flask_app()
    logger.info("Flask app created successfully")

    # Initialize bot (handlers, webhook, etc.)
    bot_application.initialize_bot()
    logger.info("Bot initialized successfully")

    # Get the SocketIO instance
    socketio = bot_application.socketio

    logger.info("Application ready for production deployment")
    logger.info(f"Webhook URL configured: {bot_application.config.telegram.webhook_url}")

    # Note: We expose both 'app' and 'socketio' but gunicorn will use 'app'
    # The socketio functionality is integrated into the Flask app

except Exception as e:
    logger.error(f"Failed to initialize application: {e}", exc_info=True)
    raise

if __name__ == "__main__":
    # This is only for testing - production uses gunicorn
    logger.info("Running in development mode (use gunicorn for production)")
    port = int(os.environ.get("PORT", 5000))

    if socketio:
        socketio.run(app, host="0.0.0.0", port=port, debug=False)
    else:
        app.run(host="0.0.0.0", port=port, debug=False)
