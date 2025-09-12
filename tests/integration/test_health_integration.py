#!/usr/bin/env python3
"""
Simple test script to verify if Flask health endpoints work without the bot.
"""

import os
import logging
from flask import Flask, jsonify

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_simple_app():
    """Create a minimal Flask app with just health endpoints."""
    app = Flask(__name__)
    
    @app.route("/")
    def health():
        """Simple health check."""
        return jsonify({
            "status": "healthy",
            "message": "Simple Flask app online",
            "version": "test"
        })
    
    @app.route("/health")
    def health_detailed():
        """Detailed health check."""
        return jsonify({
            "status": "healthy",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "config": {
                "environment": "test",
                "debug": False
            }
        })
    
    return app

if __name__ == "__main__":
    logger.info("Starting simple Flask health test...")
    app = create_simple_app()
    
    # Start Flask app
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask on port {port}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )