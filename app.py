"""
Modern Flask application using the new service container architecture.
This replaces app.py with proper dependency injection and configuration management.
"""

import os
import logging
import nest_asyncio
from flask import Flask, request, jsonify, render_template
from telegram import Update

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Import new configuration and service system
from core.config import get_config, configure_logging, print_config_summary
from core.modern_service_container import initialize_services, health_check_services, get_service_diagnostics
from database import initialize_database
from database.schema import initialize_schema
from core.bot_manager import BotManager
from core.handler_registry import configure_handlers


class BotApplication:
    """
    Main application class that manages the bot lifecycle and services.
    Encapsulates Flask app, services, and bot management.
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.flask_app = None
        self.bot_manager = None
        self.services_initialized = False
        
        # Configure logging first
        configure_logging()
        self.logger.info("BotApplication initializing...")
        
        # Print configuration summary
        print_config_summary()
        
        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            self.logger.error(f"Configuration errors: {config_errors}")
            raise ValueError(f"Invalid configuration: {', '.join(config_errors)}")
    
    def initialize_services(self):
        """Initialize all application services."""
        if self.services_initialized:
            return
        
        self.logger.info("Initializing services...")
        
        try:
            # Initialize database connection pool
            initialize_database(database_url=self.config.database.url)
            self.logger.info("Database connection pool initialized")
            
            # Initialize database schema (tables, indexes, default data)
            initialize_schema()
            self.logger.info("Database schema initialized")
            
            # Initialize modern service container
            service_config = {
                'environment': self.config.environment.value,
                'debug': self.config.debug,
                'database': self.config.database.to_dict() if hasattr(self.config.database, 'to_dict') else {}
            }
            
            initialize_services(service_config)
            self.logger.info("Service container initialized")
            
            # Verify services health
            health = health_check_services()
            if not health.get('container', {}).get('healthy', False):
                self.logger.warning("Some services are not healthy:")
                for service, status in health.get('services', {}).items():
                    if not status.get('healthy', False):
                        self.logger.warning(f"  - {service}: {status.get('message', 'Unknown error')}")
            
            self.services_initialized = True
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise
    
    def create_flask_app(self) -> Flask:
        """Create and configure Flask application."""
        if self.flask_app is not None:
            return self.flask_app
        
        self.logger.info("Creating Flask application...")
        
        # Create Flask app
        app = Flask(__name__)
        
        # Apply nest_asyncio for async compatibility
        nest_asyncio.apply()
        
        # Configure routes
        self._configure_routes(app)
        
        self.flask_app = app
        self.logger.info("Flask application created")
        
        return app
    
    def initialize_bot(self):
        """Initialize the Telegram bot manager."""
        if self.bot_manager is not None:
            return
        
        self.logger.info("Initializing bot manager...")
        
        try:
            webhook_url = f"{self.config.telegram.webhook_url}/{self.config.telegram.bot_token}"
            
            self.bot_manager = BotManager(
                self.config.telegram.bot_token, 
                webhook_url
            )
            
            # Configure handlers using the service container
            self.bot_manager.set_handler_configurator(configure_handlers)
            
            self.logger.info(f"Bot manager initialized with webhook URL: {webhook_url}")
            self.logger.info("Webhook has been set up and is ready to receive updates")
            self.logger.info(f"Bot manager instance ID: {id(self.bot_manager)}")
            
            # Start worker thread immediately - async initialization will happen in worker
            self.bot_manager.start_worker()
            self.logger.info("Bot manager worker started - initialization will complete async")
            
            # Wait for bot initialization to complete properly
            import time
            max_wait = 35  # Maximum 35 seconds (longer than bot manager timeout of 25s)
            wait_time = 0
            
            while not self.bot_manager.is_ready and wait_time < max_wait:
                time.sleep(0.5)
                wait_time += 0.5
                self.logger.debug(f"Waiting for bot initialization... {wait_time}s")
            
            if self.bot_manager.is_ready:
                self.logger.info(f"Bot ready after {wait_time}s - Bot manager ID: {id(self.bot_manager)}")
            else:
                self.logger.error(f"Bot failed to initialize within {max_wait}s")
                raise RuntimeError("Bot initialization timeout")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}", exc_info=True)
            raise
    
    def _configure_routes(self, app: Flask):
        """Configure Flask routes."""
        
        
        @app.route(f"/{self.config.telegram.bot_token}", methods=["POST"])
        def webhook():
            """Handle incoming telegram webhooks."""
            self.logger.info("=== WEBHOOK REQUEST RECEIVED ===")
            try:
                if not self.bot_manager:
                    self.logger.warning("Bot manager not initialized, rejecting webhook")
                    return jsonify({"error": "Bot manager not initialized"}), 503
                
                # Force debug the bot manager state
                self.logger.info(f"Webhook - Bot manager instance ID: {id(self.bot_manager)}")
                self.logger.info(f"Webhook - Bot manager exists: {self.bot_manager is not None}")
                if self.bot_manager:
                    self.logger.info(f"Webhook - Bot manager ready: {self.bot_manager.is_ready}")
                    self.logger.info(f"Webhook - App bot exists: {self.bot_manager.app_bot is not None}")
                    if self.bot_manager.app_bot:
                        self.logger.info(f"Webhook - Bot exists: {self.bot_manager.app_bot.bot is not None}")
                    self.logger.info(f"Webhook - Initialized: {self.bot_manager._is_initialized}")
                    self.logger.info(f"Webhook - Worker alive: {self.bot_manager.worker_thread and self.bot_manager.worker_thread.is_alive()}")
                
                if not self.bot_manager.is_ready:
                    # Log detailed status for debugging
                    self.logger.warning(f"Bot manager object id: {id(self.bot_manager)}")
                    self.logger.warning(f"Bot manager app_bot: {self.bot_manager.app_bot is not None}")
                    self.logger.warning(f"Bot manager initialized: {self.bot_manager._is_initialized}")
                    status = self.bot_manager.get_health_status()
                    self.logger.warning(f"Bot not ready, rejecting webhook. Status: {status}")
                    return jsonify({"error": "Bot not ready", "status": status}), 503

                # Parse telegram update
                update_data = request.get_json(force=True)
                if not update_data:
                    return jsonify({"error": "No data"}), 400
                    
                update = Update.de_json(update_data, self.bot_manager.app_bot.bot)
                
                # Queue update for processing
                self.logger.info(f"Queuing update: {update.update_id}")
                if self.bot_manager.queue_update(update):
                    self.logger.info(f"Update {update.update_id} queued successfully")
                    return jsonify({"status": "ok"}), 200
                else:
                    self.logger.warning(f"Failed to queue update {update.update_id} - queue full")
                    return jsonify({"error": "Queue full"}), 503
                    
            except Exception as e:
                self.logger.error(f"Webhook error: {e}", exc_info=True)
                return jsonify({"error": "Internal server error"}), 500
        
        @app.route("/")
        def health():
            """Simple health check."""
            return jsonify({
                "status": "healthy",
                "message": "Bot online",
                "version": os.getenv("RENDER_GIT_COMMIT", "local")[:8] if os.getenv("RENDER_GIT_COMMIT") else "local"
            })
        
        @app.route("/test", methods=["GET", "POST"])
        def test_endpoint():
            """Test endpoint to verify Flask is working."""
            self.logger.info(f"Test endpoint hit: {request.method}")
            return jsonify({"message": "Flask is working", "method": request.method})
        
        @app.route("/health")
        def health_detailed():
            """Detailed health check with full system status."""
            try:
                # Get service diagnostics
                diagnostics = get_service_diagnostics()
                
                # Bot health
                bot_status = {}
                if self.bot_manager:
                    bot_status = self.bot_manager.get_health_status()
                else:
                    bot_status = {"bot_ready": False, "error": "Bot manager not initialized"}
                
                # Overall status
                services_healthy = diagnostics.get('health', {}).get('container', {}).get('healthy', False)
                bot_healthy = bot_status.get("bot_ready", False)
                overall_healthy = services_healthy and bot_healthy
                
                response = {
                    "status": "healthy" if overall_healthy else "degraded",
                    "timestamp": __import__('datetime').datetime.now().isoformat(),
                    "services": diagnostics,
                    "bot": bot_status,
                    "config": {
                        "environment": self.config.environment.value,
                        "debug": self.config.debug,
                        "webhook_enabled": self.config.telegram.use_webhook
                    },
                    "version": os.getenv("RENDER_GIT_COMMIT", "local")[:8] if os.getenv("RENDER_GIT_COMMIT") else "local"
                }
                
                return jsonify(response), 200 if overall_healthy else 503
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                }), 503
        
        @app.route("/services")
        def services_info():
            """Get detailed service information."""
            try:
                diagnostics = get_service_diagnostics()
                return jsonify(diagnostics)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @app.route("/config")
        def config_info():
            """Get configuration information (sensitive data hidden)."""
            try:
                return jsonify(self.config.to_dict())
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        
        @app.route("/api/dashboard")
        def api_dashboard():
            """API endpoint for dashboard data."""
            try:
                from core.modern_service_container import get_product_service, get_user_service, get_sales_service
                from database import get_database_manager
                
                # Get services
                product_service = get_product_service()
                user_service = get_user_service(None)
                sales_service = get_sales_service()
                db_manager = get_database_manager()
                
                # Get stats from database
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Count products
                        cur.execute("SELECT COUNT(*) FROM Produtos")
                        total_products = cur.fetchone()[0]
                        
                        # Count sales
                        cur.execute("SELECT COUNT(*) FROM Vendas")
                        total_sales = cur.fetchone()[0]
                        
                        # Count users
                        cur.execute("SELECT COUNT(*) FROM Usuarios")
                        total_users = cur.fetchone()[0]
                        
                        # Calculate total revenue
                        cur.execute("SELECT COALESCE(SUM(preco_total), 0) FROM Vendas")
                        total_revenue = float(cur.fetchone()[0] or 0)
                
                return jsonify({
                    "products": total_products,
                    "sales": total_sales,
                    "users": total_users,
                    "revenue": f"R$ {total_revenue:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                })
            except Exception as e:
                self.logger.error(f"Dashboard API error: {e}")
                return jsonify({"error": "Erro ao carregar dados"}), 500
        
        @app.route("/api/products")
        def api_products():
            """API endpoint for products data."""
            try:
                from database import get_database_manager
                
                db_manager = get_database_manager()
                
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT p.id, p.nome, p.emoji, p.preco, 
                                   COALESCE(SUM(e.quantidade), 0) as estoque,
                                   CASE WHEN COALESCE(SUM(e.quantidade), 0) > 0 THEN 'Ativo' ELSE 'Inativo' END as status
                            FROM Produtos p
                            LEFT JOIN Estoque e ON p.id = e.produto_id
                            GROUP BY p.id, p.nome, p.emoji, p.preco
                            ORDER BY p.nome
                        """)
                        
                        products = []
                        for row in cur.fetchall():
                            products.append({
                                "id": row[0],
                                "name": f"{row[2] or ''} {row[1]}".strip(),
                                "price": f"R$ {row[3]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                "stock": int(row[4]),
                                "status": row[5]
                            })
                
                return jsonify({"products": products})
            except Exception as e:
                self.logger.error(f"Products API error: {e}")
                return jsonify({"error": "Erro ao carregar produtos"}), 500
        
        @app.route("/api/sales")
        def api_sales():
            """API endpoint for sales data."""
            try:
                from database import get_database_manager
                
                db_manager = get_database_manager()
                
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT v.id, v.data_venda, v.comprador_nome, v.preco_total,
                                   CASE WHEN p.valor_pago >= v.preco_total THEN 'Pago' ELSE 'Pendente' END as status,
                                   STRING_AGG(pr.emoji || ' ' || pr.nome, ', ') as produtos
                            FROM Vendas v
                            LEFT JOIN Pagamentos p ON v.comprador_nome = p.usuario_nome
                            LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                            LEFT JOIN Produtos pr ON iv.produto_id = pr.id
                            GROUP BY v.id, v.data_venda, v.comprador_nome, v.preco_total, p.valor_pago
                            ORDER BY v.data_venda DESC
                            LIMIT 50
                        """)
                        
                        sales = []
                        for row in cur.fetchall():
                            sales.append({
                                "id": row[0],
                                "date": row[1].strftime("%d/%m %H:%M") if row[1] else "",
                                "customer": row[2],
                                "total": f"R$ {row[3]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                "status": row[4],
                                "products": row[5] or "N/A"
                            })
                
                return jsonify({"sales": sales})
            except Exception as e:
                self.logger.error(f"Sales API error: {e}")
                return jsonify({"error": "Erro ao carregar vendas"}), 500
        
        @app.route("/api/users")
        def api_users():
            """API endpoint for users data."""
            try:
                from database import get_database_manager
                
                db_manager = get_database_manager()
                
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT u.username, u.nivel,
                                   COALESCE(SUM(v.preco_total), 0) as total_compras,
                                   MAX(v.data_venda) as ultimo_acesso
                            FROM Usuarios u
                            LEFT JOIN Vendas v ON u.username = v.comprador_nome
                            GROUP BY u.username, u.nivel
                            ORDER BY total_compras DESC
                        """)
                        
                        users = []
                        for row in cur.fetchall():
                            users.append({
                                "username": row[0],
                                "level": row[1].capitalize() if row[1] else "User",
                                "total_purchases": f"R$ {row[2]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                "last_access": row[3].strftime("%d/%m %H:%M") if row[3] else "Nunca",
                                "status": "Ativo"
                            })
                
                return jsonify({"users": users})
            except Exception as e:
                self.logger.error(f"Users API error: {e}")
                return jsonify({"error": "Erro ao carregar usuários"}), 500
    
    def run(self):
        """Run the complete application."""
        try:
            # Initialize services
            self.logger.info(">> STEP 1: Initializing services")
            self.initialize_services()
            
            # Create Flask app
            self.logger.info(">> STEP 2: Creating Flask app")
            app = self.create_flask_app()
            
            # Initialize bot
            self.logger.info(">> STEP 3: Initializing bot")
            self.initialize_bot()
            
            # Register cleanup
            import atexit
            self.logger.info(">> STEP 4: Starting Flask")
            atexit.register(self.cleanup)
            
            # Handle signals
            import signal
            def signal_handler(signum, frame):
                self.logger.info(f"Received signal {signum}, shutting down gracefully...")
                self.cleanup()
                exit(0)
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            # Start Flask app
            self.logger.info(f"Starting Flask app on {self.config.host}:{self.config.port}")
            app.run(
                host=self.config.host,
                port=self.config.port,
                debug=False,  # FORCE OFF
                use_reloader=False  # 🔥 CRITICAL: disables restart
            )
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.cleanup()
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            self.cleanup()
            raise
    
    def cleanup(self):
        """Clean shutdown for all services."""
        self.logger.info("Performing cleanup...")
        
        try:
            # Shutdown bot manager
            if self.bot_manager:
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.bot_manager.shutdown())
                    self.logger.info("Bot manager shutdown complete")
                except Exception as e:
                    self.logger.error(f"Bot shutdown error: {e}")
        except Exception as e:
            self.logger.error(f"Error during bot cleanup: {e}")
        
        try:
            # Dispose services
            from core.modern_service_container import get_service_registry
            registry = get_service_registry()
            registry.dispose()
            self.logger.info("Services disposed")
        except Exception as e:
            self.logger.error(f"Error disposing services: {e}")
        
        try:
            # Close database connections
            from database import close_database
            close_database()
            self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Database shutdown error: {e}")
        
        self.logger.info("Cleanup completed")


def create_app() -> Flask:
    """
    Factory function to create Flask app.
    Useful for testing and external integrations.
    """
    bot_app = BotApplication()
    bot_app.initialize_services()
    bot_app.initialize_bot()
    return bot_app.create_flask_app()


if __name__ == "__main__":
    # Create and run the application
    bot_application = BotApplication()
    bot_application.run()